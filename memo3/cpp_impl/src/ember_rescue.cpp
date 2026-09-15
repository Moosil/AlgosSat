#include "ember_rescue.h"

#include <queue>
#include <ranges>
#include <stack>

#include "barkeep.h"
#include "complexity.h"

std::unordered_map<Graph::VertexT, Graph::VertexT> dfs(const Graph& g, const Graph::VertexT source) {
	std::unordered_map<Graph::VertexT, Graph::VertexT> prev;
	std::stack<Graph::VertexT> stack{};
	stack.push(source);

	Complexity::operation_counter += 2 + Complexity::braced_init;
	Complexity::operation_counter += Complexity::while_outer;

	while (!stack.empty()) {
		Complexity::operation_counter += Complexity::while_inner + 2;
		const Graph::VertexT u = stack.top();
		stack.pop();
		Complexity::operation_counter += 1;

		Complexity::operation_counter += Complexity::for_outer + Complexity::get_neighbours(g.size());
		for (const auto v : g.get_neighbors(u) | std::views::keys) {
			Complexity::operation_counter += Complexity::for_inner + 2 + Complexity::if_;
			if (!prev.contains(v) && v != source) {
				Complexity::operation_counter += 2;
				prev[v] = u;
				stack.push(v);
			}
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return prev;
}

std::vector<Graph::VertexT> get_path_from_dfs(
	const Graph::VertexT source,
	const Graph::VertexT sink,
	std::unordered_map<Graph::VertexT, Graph::VertexT> prev
) {
	std::vector left_path{source};
	std::vector right_path{sink};
	Graph::VertexT left = source;
	Graph::VertexT right = sink;
	Complexity::operation_counter += 4 + 2 * Complexity::braced_init;

	Complexity::operation_counter += Complexity::while_outer;
	while (prev.contains(left) || prev.contains(right)) {
		Complexity::operation_counter += Complexity::while_inner + 3;
		if (prev.contains(left)) {
			Complexity::operation_counter += 3;
			left = prev[left];
			left_path.push_back(left);
		}
		Complexity::operation_counter += 1 + Complexity::if_;

		if (prev.contains(right)) {
			Complexity::operation_counter += 3;
			right = prev[right];
			right_path.push_back(right);
		}
		Complexity::operation_counter += 1 + Complexity::if_;


		Complexity::operation_counter += Complexity::for_outer + 1 + left_path.size() * (
			Complexity::for_inner + 2 + Complexity::if_);
		if (const auto it = std::ranges::find(left_path, right);
			it != left_path.end()) {
			Complexity::operation_counter += 1 + Complexity::for_outer + std::distance(left_path.begin(), it) * (
						Complexity::for_inner + 2) + 1 + Complexity::for_outer + right_path.size() * (
						Complexity::for_inner + 4)
					+ Complexity::return_;
			std::vector<Graph::VertexT> res{left_path.begin(), it};
			res.append_range(std::views::reverse(right_path));
			return res;
		}

		Complexity::operation_counter += Complexity::for_outer + 1 + right_path.size() * (
			Complexity::for_inner + 2 + Complexity::if_);
		if (const auto it = std::ranges::find(right_path, left);
			it != right_path.end()) {
			Complexity::operation_counter += 1 + Complexity::for_outer + left_path.size() * (Complexity::for_inner + 2)
					+ 1 + Complexity::for_outer + std::distance(right_path.begin(), it) * (Complexity::for_inner + 3) +
					Complexity::return_;
			left_path.append_range(
				std::ranges::subrange(
					std::make_reverse_iterator(it),
					std::make_reverse_iterator(right_path.begin())
				)
			);
			return left_path;
		}
	}
	throw std::runtime_error{"Opps"};
}

std::vector<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>& supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID>& found_supply_ids,
	const std::vector<SupplyID>& supply_storage
) {
	Complexity::operation_counter += 1 + Complexity::for_outer;
	for (auto supply : supply_storage) {
		Complexity::operation_counter += Complexity::for_inner + Complexity::braced_init + 2;
		found_supply_ids.insert(supply);
	}

	Complexity::operation_counter += 1 + Complexity::for_outer;
	std::vector<Graph::VertexT> res{};
	for (const auto& supply : supplies) {
		Complexity::operation_counter += Complexity::for_inner + Complexity::if_ + 3;
		if (!found_supply_ids.contains(vertex_to_supply_id.at(supply))) {
			Complexity::operation_counter += 2 + Complexity::braced_init;
			res.push_back(supply);
		}
	}
	return res;
}

Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path) {
	Complexity::operation_counter += Complexity::if_ + 2;
	if (path.empty()) {
		Complexity::operation_counter += Complexity::return_;
		return 0;
	}
	Complexity::operation_counter += 3 + Complexity::for_outer;
	Graph::WeightT res = 0;
	for (std::size_t i = 0; i < path.size() - 1; ++i) {
		Complexity::operation_counter += Complexity::for_inner + 5 + Complexity::get_edge_weight;
		res += wing.get_edge_weight(path[i], path[i + 1]);
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

Graph get_F(
	const Facility_ADT& G,
	const Graph::VertexT entry,
	const std::vector<Graph::VertexT>& supplies,
	const std::unordered_set<Graph::VertexT>& exits,
	const std::unordered_map<std::size_t, std::unordered_map<Graph::VertexT, Graph::VertexT> >& prevs
) {
	Complexity::operation_counter += 1 + 2 + Complexity::braced_init + Complexity::for_outer;
	Graph res;

	for (const auto& v : supplies) {
		Complexity::operation_counter += Complexity::for_inner + 1;
		res.add_vertex(v);
	}
	for (const auto& v : exits) {
		Complexity::operation_counter += Complexity::for_inner + 1;
		res.add_vertex(v);
	}
	Complexity::operation_counter += Complexity::for_inner + 1;
	res.add_vertex(entry);


	Complexity::operation_counter += 1 + 1 + Complexity::for_outer;
	std::vector<Graph::VertexT> junction_vertices;
	for (const auto& [u, v] : G.second) {
		Complexity::operation_counter += Complexity::for_inner + 13 + 2 * Complexity::braced_init;
		res.add_vertex(u);
		res.add_vertex(v);
		res.add_edge(u, v, 1);

		junction_vertices.push_back(u);
		junction_vertices.push_back(v);
	}

	Complexity::operation_counter += Complexity::for_outer + 1;
	for (std::size_t w_it = 0; w_it < G.first.size(); ++w_it) {
		Complexity::operation_counter += Complexity::for_inner + 1 + 5 + Complexity::braced_init +
				Complexity::for_outer;
		const auto& wing = G.first[w_it];
		std::vector<Graph::VertexT> salient_vertices;
		for (const auto& v : supplies) {
			if (wing.contains(v)) {
				Complexity::operation_counter += Complexity::for_inner + 1;
				salient_vertices.push_back(v);
			}
		}

		for (const auto& v : exits) {
			if (wing.contains(v)) {
				Complexity::operation_counter += Complexity::for_inner + 1;
				salient_vertices.push_back(v);
			}
		}

		for (const auto& v : junction_vertices) {
			if (wing.contains(v)) {
				Complexity::operation_counter += Complexity::for_inner + 1;
				salient_vertices.push_back(v);
			}
		}

		if (wing.contains(entry)) {
			Complexity::operation_counter += Complexity::for_inner + 1;
			salient_vertices.push_back(entry);
		}

		Complexity::operation_counter += Complexity::for_outer + 1;
		for (std::size_t i = 0; i < salient_vertices.size(); ++i) {
			Complexity::operation_counter += Complexity::for_inner + Complexity::for_outer + 1;
			for (std::size_t j = i + 1; j < salient_vertices.size(); ++j) {
				Complexity::operation_counter += Complexity::for_inner + 4;
				const Graph::VertexT u = salient_vertices[i];
				const Graph::VertexT v = salient_vertices[j];

				Complexity::operation_counter += 4;
				std::vector<Graph::VertexT> path = get_path_from_dfs(u, v, prevs.at(w_it));
				const Graph::WeightT weight = get_path_length(wing, path);

				res.add_edge(u, v, weight);
			}
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::vector<Graph::VertexT> reconstruct_path(
	const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
	Graph::VertexT sink
) {
	Complexity::operation_counter += 1 + Complexity::braced_init;
	std::vector res = {sink};
	Complexity::operation_counter += Complexity::while_outer;
	while (prev.contains(sink)) {
		Complexity::operation_counter += Complexity::while_inner + 1 + 3;
		sink = prev.at(sink);
		res.push_back(sink);
	}
	Complexity::operation_counter += Complexity::reverse(res.size()) + Complexity::return_;
	std::ranges::reverse(res);
	return res;
}

std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > dijkstra(
	const Graph& g,
	Graph::VertexT source,
	const std::unordered_set<Graph::VertexT>& sinks
) {
	Complexity::operation_counter += 3;
	std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > res;
	std::unordered_map<Graph::VertexT, Graph::WeightT> dist;
	Complexity::operation_counter += Complexity::for_outer + 1;
	for (const auto& v : g.get_vertices()) {
		Complexity::operation_counter += Complexity::for_inner + 1;
		dist[v] = std::numeric_limits<Graph::WeightT>::max();
	}
	Complexity::operation_counter += 1;
	dist[source] = 0;
	Complexity::operation_counter += 1;
	std::unordered_map<Graph::VertexT, Graph::VertexT> prev;
	Complexity::operation_counter += 1 + Complexity::for_outer;
	Complexity::operation_counter += g.size() * (Complexity::for_inner + 2);
	std::priority_queue<std::pair<Graph::WeightT, Graph::VertexT> > pq;
	pq.emplace(0, source);

	Complexity::operation_counter += Complexity::while_outer;
	while (!pq.empty()) {
		const auto [d, u] = pq.top();
		pq.pop();
		if (dist[u] < -d) {
			continue;
		}
		Complexity::operation_counter += Complexity::while_inner + 2 + 1;

		Complexity::operation_counter += Complexity::if_ + 1;
		if (sinks.contains(u)) {
			Complexity::operation_counter += 1 + 3 + Complexity::if_;
			res[u] = reconstruct_path(prev, u);
			if (res.size() == sinks.size()) {
				Complexity::operation_counter += Complexity::return_;
				return res;
			}
		}

		Complexity::operation_counter += Complexity::for_outer + Complexity::get_neighbours(g.size());
		for (const auto& [v, w] : g.get_neighbors(u)) {
			Complexity::operation_counter += Complexity::for_inner + Complexity::get_edge_weight + 1;
			Complexity::operation_counter += Complexity::if_ + 4;
			if (dist[u] + w < dist[v]) {
				Complexity::operation_counter += 6;
				prev[v] = u;
				dist[v] = dist[u] + w;
				pq.emplace(-dist[v], v);
			}
		}
	}
	throw std::runtime_error("Dijkstra did not find all sinks.");
}

std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > > get_path_matrix(
	const Graph& F,
	Graph::VertexT entry,
	std::unordered_set<Graph::VertexT> exits,
	std::vector<Graph::VertexT> supplies
) {
	Complexity::operation_counter += 1 + Complexity::for_outer + 1 + Complexity::braced_init;
	std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > > res;
	exits.insert_range(supplies);
	supplies.push_back(entry);
	for (const auto& source : supplies) {
		Complexity::operation_counter += 2;
		res[source] = dijkstra(F, source, exits);
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> > get_path_cost_matrix(
	const Graph& F,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > >&
	path_matrix
) {
	Complexity::operation_counter += 1 + Complexity::for_outer + 1;
	std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> > res{};
	for (const auto& source : path_matrix | std::views::keys) {
		Complexity::operation_counter += Complexity::for_inner + 4;
		res[source] = {};
		for (const auto& sink_paths = path_matrix.at(source);
		     const auto& sink : sink_paths | std::views::keys) {
			Complexity::operation_counter += 3;
			res[source][sink] = get_path_length(F, sink_paths.at(sink));
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::pair<std::vector<Graph::VertexT>, Graph::WeightT> dp_recursive(
	Graph::VertexT source,
	const std::vector<Graph::VertexT>& supplies,
	const std::unordered_set<Graph::VertexT>& exits,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> >& path_cost_matrix,
	size_t fuel,
	uint32_t mask,
	std::unordered_map<uint64_t, std::pair<std::vector<Graph::VertexT>, Graph::WeightT> >& memo
) {
	Complexity::operation_counter += Complexity::braced_init + 1 + 1 + Complexity::if_;
	auto key = static_cast<uint64_t>(mask);
	key |= static_cast<uint64_t>(source) << 32;
	if (memo.contains(key)) {
		Complexity::operation_counter += 1 + Complexity::return_;
		return memo.at(key);
	}

	Complexity::operation_counter += 2;
	Graph::WeightT min_cost = std::numeric_limits<Graph::WeightT>::max();
	std::vector<Graph::VertexT> min_cost_path{};
	min_cost_path.reserve(fuel);

	Complexity::operation_counter += 1 + Complexity::if_;
	if (fuel == 0) {
		Complexity::operation_counter += Complexity::for_outer;
		for (const auto exit : exits) {
			Complexity::operation_counter += Complexity::for_inner + 3 + Complexity::if_ + 1;
			auto cost = path_cost_matrix.at(source).at(exit);
			if (cost < min_cost) {
				Complexity::operation_counter += 2 + Complexity::braced_init;
				min_cost = cost;
				min_cost_path = {exit};
			}
		}
	} else {
		Complexity::operation_counter += Complexity::for_outer;
		for (uint32_t i = 0; i < supplies.size(); ++i) {
			if (mask & (1 << i)) {
				continue;
			}
			Complexity::operation_counter += 3 + Complexity::braced_init;
			const auto& supply = supplies[i];
			auto [min_path_through, cost] = dp_recursive(supply, supplies, exits, path_cost_matrix, fuel - 1,
			                                             mask | (1 << i), memo);
			Complexity::operation_counter += 6;
			cost += path_cost_matrix.at(source).at(supply);
			Complexity::operation_counter += Complexity::if_ + 1;
			if (cost < min_cost) {
				Complexity::operation_counter += 2 + Complexity::braced_init + Complexity::for_outer;
				Complexity::operation_counter += min_path_through.size() * (Complexity::for_inner + 1);
				min_cost = cost;
				min_cost_path = {supply};
				min_cost_path.append_range(min_path_through);
			}
		}
	}
	Complexity::operation_counter += 1 + Complexity::braced_init;
	memo[key] = {min_cost_path, min_cost};
	Complexity::operation_counter += Complexity::return_ + Complexity::braced_init;
	return memo[key];
}

std::vector<Graph::VertexT> dp(
	Graph::VertexT entry,
	const std::vector<Graph::VertexT>& supplies,
	const std::unordered_set<Graph::VertexT>& exits,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> >& path_cost_matrix,
	size_t fuel
) {
	Complexity::operation_counter += 3;
	std::unordered_map<uint64_t, std::pair<std::vector<Graph::VertexT>, Graph::WeightT> > memo{};
	std::vector<Graph::VertexT> res = dp_recursive(entry, supplies, exits, path_cost_matrix, fuel, 0, memo).first;

	Complexity::operation_counter += 1 + Complexity::braced_init + Complexity::for_outer;
	Complexity::operation_counter += res.size() * (Complexity::for_inner + 1);
	res.insert(res.begin(), entry);
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::vector<Graph::VertexT> get_F_path_from_H_path(
	const std::vector<Graph::VertexT>& H_path,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > >&
	path_matrix
) {
	Complexity::operation_counter += 1 + Complexity::for_outer + 2;
	std::vector<Graph::VertexT> res;
	for (std::size_t i = 0; i < H_path.size() - 1; ++i) {
		Complexity::operation_counter += Complexity::for_inner + 6;
		auto path = path_matrix.at(H_path[i]).at(H_path[i + 1]);
		res.append_range(path);
		Complexity::operation_counter += Complexity::for_outer + 2;
		Complexity::operation_counter += (path.size() - 1) * (Complexity::for_inner + 2);
		if (i != H_path.size() - 2) {
			res.pop_back();
		}
	}
	Complexity::operation_counter += 3 + Complexity::return_;
	return res;
}

std::size_t get_which_wing(
	const Facility_ADT& G,
	Graph::VertexT v
) {
	Complexity::operation_counter += Complexity::for_outer + 1;
	for (std::size_t i = 0; i < G.first.size(); ++i) {
		Complexity::operation_counter += Complexity::for_inner + Complexity::if_ + 2;
		if (G.first[i].contains(v)) {
			Complexity::operation_counter += Complexity::return_;
			return i;
		}
	}
	throw std::runtime_error("Imaginary vertex in get_which_wing");
}

std::vector<Graph::VertexT> get_G_path_from_F_path(
	const Facility_ADT& G,
	const std::vector<Graph::VertexT>& F_path,
	const std::unordered_map<std::size_t, std::unordered_map<Graph::VertexT, Graph::VertexT> >& prevs
) {
	Complexity::operation_counter += 1 + Complexity::for_outer + 2;
	std::vector<Graph::VertexT> res;
	for (std::size_t i = 0; i < F_path.size() - 1; ++i) {
		Complexity::operation_counter += Complexity::for_inner + 8 + Complexity::if_;
		const auto u = F_path[i];
		const auto v = F_path[i + 1];
		const auto u_wing = get_which_wing(G, u);
		const auto v_wing = get_which_wing(G, v);
		if (u_wing == v_wing) {
			Complexity::operation_counter += 4 + Complexity::for_outer;
			auto path = get_path_from_dfs(u, v, prevs.at(u_wing));
			Complexity::operation_counter += (path.size() - 1) * (Complexity::for_inner + 2);
			res.append_range(path);
			if (i != F_path.size() - 2) {
				res.pop_back();
			}
		} else {
			Complexity::operation_counter += 1;
			res.push_back(u);
		}
	}
	Complexity::operation_counter += 3 + Complexity::return_;
	return res;
}

void get_new_supply_storage(
	const std::vector<Graph::VertexT>& supplies,
	std::vector<SupplyID>& supply_storage,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	size_t num_of_supplies_to_collect,
	const std::vector<Graph::VertexT>& H_path
) {
	Complexity::operation_counter += 1 + Complexity::for_outer;
	std::vector<Graph::VertexT> collected_supplies;
	const std::unordered_set<Graph::VertexT> supply_set{supplies.begin(), supplies.end()};
	for (const auto& v : H_path) {
		Complexity::operation_counter += Complexity::for_inner + 1 + Complexity::if_;
		if (supply_set.contains(v)) {
			Complexity::operation_counter += 1;
			collected_supplies.push_back(v);
		}
	}

	Complexity::operation_counter += 1 + Complexity::for_outer;
	std::size_t supply_storage_idx = 0;
	for (std::size_t i = 0; i < num_of_supplies_to_collect; ++i) {
		Complexity::operation_counter += Complexity::for_inner + 2 + Complexity::if_;
		if (supply_storage_idx == supply_storage.size()) {
			Complexity::operation_counter += Complexity::return_;
			return;
		}
		Complexity::operation_counter += 2 + Complexity::if_;
		if (supply_storage[supply_storage_idx] == 0) {
			Complexity::operation_counter += 5;
			supply_storage[supply_storage_idx] = vertex_to_supply_id.at(collected_supplies[i]);
			++supply_storage_idx;
		}
	}
	Complexity::operation_counter += Complexity::return_;
}

std::vector<Graph::VertexT> ember_rescue(
	const Facility_ADT& G,
	Graph::VertexT entry,
	const std::unordered_set<Graph::VertexT>& supplies,
	const std::unordered_set<Graph::VertexT>& exits,
	std::vector<SupplyID>& supply_storage,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID> found_supply_ids
) {
	Complexity::operation_counter = 0;

	Complexity::operation_counter += 1;
	const auto uncollected_supplies = get_supplies_to_collect(
		supplies,
		vertex_to_supply_id,
		found_supply_ids,
		supply_storage
	);

	Complexity::operation_counter += 1 + Complexity::for_outer;
	std::size_t num_of_supplies_to_collect = 0;
	for (const auto& id : supply_storage) {
		Complexity::operation_counter += Complexity::for_inner + 2 + Complexity::if_;
		if (id != 0) {
			Complexity::operation_counter += 2;
			++num_of_supplies_to_collect;
		}
	}
	Complexity::operation_counter += 2 + Complexity::max;
	num_of_supplies_to_collect = std::max(num_of_supplies_to_collect, supplies.size());

	Complexity::operation_counter += 1 + Complexity::for_outer;
	std::unordered_map<std::size_t, std::unordered_map<Graph::VertexT, Graph::VertexT> > prevs;
	for (std::size_t i = 0; i < G.first.size(); ++i) {
		Complexity::operation_counter += Complexity::for_inner + 3 + Complexity::if_;
		if (G.first[i].size() > 0) {
			Complexity::operation_counter += 3;
			prevs[i] = dfs(G.first[i], G.first[i].get_a_vertex());
		}
	}

	Complexity::operation_counter += 1;
	Graph F = get_F(G, entry, uncollected_supplies, exits, prevs);

	Complexity::operation_counter += 1;
	auto path_matrix = get_path_matrix(F, entry, exits, uncollected_supplies);

	Complexity::operation_counter += 1;
	auto path_cost_matrix = get_path_cost_matrix(F, path_matrix);

	Complexity::operation_counter += 1;
	auto H_path = dp(entry, uncollected_supplies, exits, path_cost_matrix, num_of_supplies_to_collect);

	Complexity::operation_counter += 1;
	auto F_path = get_F_path_from_H_path(H_path, path_matrix);

	Complexity::operation_counter += 1;
	auto G_path = get_G_path_from_F_path(G, F_path, prevs);

	Complexity::operation_counter += 1;
	get_new_supply_storage(
		uncollected_supplies,
		supply_storage,
		vertex_to_supply_id,
		num_of_supplies_to_collect,
		H_path
	);
	Complexity::operation_counter += Complexity::braced_init + Complexity::return_;
	return G_path;
}
