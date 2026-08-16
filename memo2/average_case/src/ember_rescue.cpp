#include "ember_rescue.h"

#include <queue>
#include <ranges>
#include <stack>

std::unordered_map<VertexT, VertexT> dfs(const Graph& g, const VertexT source) {
	std::unordered_map<VertexT, VertexT> prev;
	std::stack<VertexT>                  stack{};
	stack.push(source);

	while (!stack.empty()) {
		const VertexT u = stack.top();
		stack.pop();

		for (const auto v : g.get_neighbors(u) | std::views::keys) {
			if (!prev.contains(v)) {
				prev[v] = u;
				stack.push(v);
			}
		}
	}
	return prev;
}

std::vector<VertexT> get_path_from_dfs(
	const VertexT source,
	const VertexT sink,
	std::unordered_map<VertexT, VertexT> prev) {
	std::vector left_path{source};
	std::vector right_path{sink};
	VertexT     left  = source;
	VertexT     right = sink;

	while (prev.contains(left) || prev.contains(right)) {
		if (prev.contains(left)) {
			left = prev[left];
			left_path.push_back(left);
		}

		if (prev.contains(right)) {
			right = prev[right];
			right_path.push_back(right);
		}

		if (const auto it = std::ranges::find(left_path, right);
			it != left_path.end()) {
			std::vector<VertexT> res{left_path.begin(), it};
			res.append_range(std::views::reverse(right_path));
			return res;
		}

		if (const auto it = std::ranges::find(right_path, left);
			it != right_path.end()) {
			left_path.append_range(
				std::ranges::subrange(
					std::make_reverse_iterator(right_path.end()),
					std::make_reverse_iterator(it)
				)
			);
			return left_path;
		}
	}
	throw std::runtime_error{"Opps"};
}

std::vector<VertexT> get_supplies_to_collect(
	const std::unordered_set<VertexT>& supplies,
	const std::unordered_map<VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID>& found_supply_ids,
	const std::vector<SupplyID>& supply_storage) {
	for (auto supply : supply_storage) {
		found_supply_ids.insert(supply);
	}

	std::vector<VertexT> res{};
	for (const auto& supply : supplies) {
		if (!found_supply_ids.contains(vertex_to_supply_id.at(supply))) {
			res.push_back(supply);
		}
	}
	return res;
}

WeightT get_path_length(const Graph& wing, const std::vector<VertexT>& path) {
	if (path.empty()) {
		return 0;
	}
	WeightT res = 0;
	for (std::size_t i = 0; i < path.size() - 1; ++i) {
		res += wing.get_edge_weight(path[i], path[i + 1]);
	}
	return res;
}

Graph get_F(
	const std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT> > >& G,
	const VertexT                                                                                 entry,
	const std::vector<VertexT>&                                                             supplies,
	const std::unordered_set<VertexT>&                                                      exits,
	const std::unordered_map<std::size_t, std::unordered_map<VertexT, VertexT> >&           prevs) {
	Graph res;

	for (const auto& v : supplies) {
		res.add_vertex(v);
	}
	for (const auto& v : exits) {
		res.add_vertex(v);
	}
	res.add_vertex(entry);

	std::vector<VertexT> junction_vertices;
	for (const auto& [u, v] : G.second) {
		res.add_vertex(u);
		res.add_vertex(v);
		res.add_edge(u, v, 1);

		junction_vertices.push_back(u);
		junction_vertices.push_back(v);
	}

	for (std::size_t w_it = 0; w_it < G.first.size(); ++w_it) {
		const auto&          wing = G.first[w_it];
		std::vector<VertexT> salient_vertices;
		for (const auto& v : supplies) {
			if (wing.contains(v)) {
				salient_vertices.push_back(v);
			}
		}

		for (const auto& v : exits) {
			if (wing.contains(v)) {
				salient_vertices.push_back(v);
			}
		}

		for (const auto& v : junction_vertices) {
			if (wing.contains(v)) {
				salient_vertices.push_back(v);
			}
		}

		if (wing.contains(entry)) {
			salient_vertices.push_back(entry);
		}

		for (std::size_t i = 0; i < supplies.size(); ++i) {
			for (std::size_t j = i + 1; j < supplies.size(); ++j) {
				const VertexT u = salient_vertices[i];
				const VertexT v = salient_vertices[j];

				std::vector<VertexT> path   = get_path_from_dfs(u, v, prevs.at(w_it));
				const WeightT        weight = get_path_length(wing, path);

				res.add_edge(u, v, weight);
			}
		}
	}
	return res;
}

std::vector<VertexT> reconstruct_path(const std::unordered_map<VertexT, VertexT>& prev, VertexT sink) {
	std::vector res = {sink};
	while (prev.contains(sink)) {
		sink = prev.at(sink);
		res.push_back(sink);
	}
	std::ranges::reverse(res);
	return res;
}

std::unordered_map<VertexT, std::vector<VertexT>> dijkstra(
	const Graph& g,
	VertexT source,
	const std::unordered_set<VertexT>& sinks) {
	std::unordered_map<VertexT, std::vector<VertexT>> res;
	std::unordered_map<VertexT, WeightT>              dist;
	for (const auto& v : g.get_vertices()) {
		dist[v] = std::numeric_limits<WeightT>::max();
	}
	dist[source] = 0;
	std::unordered_map<VertexT, VertexT>              prev;
	std::priority_queue<std::pair<WeightT, VertexT> > pq;
	pq.emplace(0, source);

	while (!pq.empty()) {
		const auto [d, u] = pq.top();
		pq.pop();
		if (dist[u] < -d) {
			continue;
		}

		if (sinks.contains(u)) {
			res[u] = reconstruct_path(prev, u);
			if (res.size() == sinks.size()) {
				return res;
			}
		}

		for (const auto& [v, w] : g.get_neighbors(u)) {
			if (dist[u] + w < dist[v]) {
				prev[v] = u;
				dist[v] = dist[u] + w;
				pq.emplace(-dist[v], v);
			}
		}
	}
	throw std::runtime_error("Dijkstra did not find all sinks.");
}

std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT>>> get_path_matrix(
	const Graph& F,
	VertexT entry,
	std::unordered_set<VertexT> exits,
	std::vector<VertexT> supplies) {
	std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT>> > res;
	exits.insert_range(supplies);
	supplies.push_back(entry);
	for (const auto& source : supplies) {
		res[source] = dijkstra(F, source, exits);
	}
	return res;
}

std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT>> get_path_cost_matrix(
	const Graph& F,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT>>>& path_matrix) {
	std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT>> res{};
	for (const auto& source : path_matrix | std::views::keys) {
		res[source] = {};
		for (const auto& sink_paths = path_matrix.at(source);
		     const auto& sink : sink_paths | std::views::keys) {
			res[source][sink] = get_path_length(F, sink_paths.at(sink));
		}
	}
	return res;
}

std::pair<std::vector<VertexT>, WeightT> dp_recursive(
	VertexT source,
	const std::vector<VertexT>& supplies,
	const std::unordered_set<VertexT>& exits,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT>>& path_cost_matrix,
	size_t fuel,
	uint32_t mask,
	std::unordered_map<uint64_t, std::pair<std::vector<VertexT>, WeightT>>& memo) {
	auto key = static_cast<uint64_t>(mask);
	key      |= static_cast<uint64_t>(source) << 32;
	if (memo.contains(key)) {
		return memo.at(key);
	}

	WeightT              min_cost = std::numeric_limits<WeightT>::max();
	std::vector<VertexT> min_cost_path{};
	min_cost_path.reserve(fuel);

	if (fuel == 0) {
		for (const auto exit : exits) {
			auto cost = path_cost_matrix.at(source).at(exit);
			if (cost < min_cost) {
				min_cost      = cost;
				min_cost_path = {exit};
			}
		}
	} else {
		for (uint32_t i = 0; i < fuel; ++i) {
			if (mask & (1 << i)) {
				continue;
			}
			const auto& supply = supplies[i];
			auto [min_path_through, cost] = dp_recursive(supply, supplies, exits, path_cost_matrix, fuel - 1, mask | (1 << i), memo);
			cost += path_cost_matrix.at(source).at(supply);
			if (cost < min_cost) {
				min_cost      = cost;
				min_cost_path = {supply};
				min_cost_path.append_range(min_path_through);
			}
		}
	}
	memo[key] = {min_cost_path, min_cost};
	return memo[key];
}

std::vector<VertexT> dp(
	VertexT entry,
	const std::vector<VertexT>& supplies,
	const std::unordered_set<VertexT>& exits,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT>>& path_cost_matrix,
	size_t fuel) {
	std::unordered_map<uint64_t, std::pair<std::vector<VertexT>, WeightT> > memo{};
	std::vector<VertexT> res = dp_recursive(entry, supplies, exits, path_cost_matrix, fuel, 0, memo).first;

	res.insert(res.begin(), entry);
	return res;
}

std::vector<VertexT> get_F_path_from_H_path(
	const std::vector<VertexT>& H_path,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT>>>& path_matrix) {
	std::vector<VertexT> res;
	for (std::size_t i = 0; i < H_path.size() - 1; ++i) {
		res.append_range(path_matrix.at(H_path[i]).at(H_path[i + 1]));
		if (i != H_path.size() - 2) {
			res.pop_back();
		}
	}
	return res;
}

std::size_t get_which_wing(
	const std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT>>>& G,
	VertexT v) {
	for (std::size_t i = 0; i < G.first.size(); ++i) {
		if (G.first[i].contains(v)) {
			return i;
		}
	}
	throw std::runtime_error("Imaginary vertex in get_which_wing");
}

std::vector<VertexT> get_G_path_from_F_path(
	const std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT>>>& G,
	const std::vector<VertexT>& F_path,
	const std::unordered_map<std::size_t, std::unordered_map<VertexT, VertexT>>& prevs) {
	std::vector<VertexT> res;
	for (std::size_t i = 0; i < F_path.size() - 1; ++i) {
		const auto u      = F_path[i];
		const auto v      = F_path[i + 1];
		const auto u_wing = get_which_wing(G, u);
		const auto v_wing = get_which_wing(G, v);
		if (u_wing == v_wing) {
			res.append_range(get_path_from_dfs(u, v, prevs.at(u_wing)));
			if (i != F_path.size() - 2) {
				res.pop_back();
			}
		} else {
			res.push_back(u);
		}
	}
	return res;
}

void get_new_supply_storage(
	const std::vector<VertexT>& supplies,
	std::vector<SupplyID>& supply_storage,
	const std::unordered_map<VertexT, SupplyID>& vertex_to_supply_id,
	size_t num_of_supplies_to_collect,
	const std::vector<VertexT>& H_path) {
	std::vector<VertexT>              collected_supplies;
	const std::unordered_set<VertexT> supply_set{supplies.begin(), supplies.end()};
	for (const auto& v : H_path) {
		if (supply_set.contains(v)) {
			collected_supplies.push_back(v);
		}
	}

	std::size_t supply_storage_idx = 0;
	for (std::size_t i = 0; i < num_of_supplies_to_collect; ++i) {
		if (supply_storage_idx == supply_storage.size()) {
			return;
		}
		if (supply_storage[supply_storage_idx] == 0) {
			supply_storage[supply_storage_idx] = vertex_to_supply_id.at(collected_supplies[i]);
			++supply_storage_idx;
		}
	}
}

std::vector<VertexT> ember_rescue(
	std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT>>> G,
	VertexT entry,
	const std::unordered_set<VertexT>& supplies,
	const std::unordered_set<VertexT>& exits,
	std::vector<SupplyID>& supply_storage,
	const std::unordered_map<VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID> found_supply_ids) {
	const auto uncollected_supplies = get_supplies_to_collect(
		supplies,
		vertex_to_supply_id,
		found_supply_ids,
		supply_storage
	);

	std::size_t num_of_supplies_to_collect = 0;
	for (const auto& id : supply_storage) {
		if (id != 0) {
			++num_of_supplies_to_collect;
		}
	}
	num_of_supplies_to_collect = std::max(num_of_supplies_to_collect, supplies.size());

	std::unordered_map<std::size_t, std::unordered_map<VertexT, VertexT> > prevs;
	for (std::size_t i = 0; i < num_of_supplies_to_collect; ++i) {
		if (G.first[i].size() > 0) {
			prevs[i] = dfs(G.first[i], G.first[i].get_a_vertex());
		}
	}

	Graph F = get_F(G, entry, uncollected_supplies, exits, prevs);

	auto path_matrix = get_path_matrix(F, entry, exits, uncollected_supplies);

	auto path_cost_matrix = get_path_cost_matrix(F, path_matrix);

	auto H_path = dp(entry, uncollected_supplies, exits, path_cost_matrix, num_of_supplies_to_collect);

	auto F_path = get_F_path_from_H_path(H_path, path_matrix);

	auto G_path = get_G_path_from_F_path(G, F_path, prevs);

	get_new_supply_storage(
		uncollected_supplies,
		supply_storage,
		vertex_to_supply_id,
		num_of_supplies_to_collect,
		H_path
	);
	return G_path;
}
