#include "ember_rescue.h"

#include <map>
#include <queue>
#include <ranges>
#include <stack>

#include "barkeep.h"

std::tuple<std::vector<std::size_t>, std::size_t> knapsack(
	const std::size_t               cap,
	const std::vector<std::size_t>& val,
	const std::vector<std::size_t>& cost) {
	std::vector<std::size_t> dp{};
	Complexity::operation_counter += 3;
	dp.reserve(cap + 1);
	std::vector<std::vector<std::size_t> > res{};
	res.reserve(cap + 1);
	std::vector<std::vector<std::size_t> > new_res{};
	new_res.reserve(cap + 1);

	Complexity::operation_counter += Complexity::for_outer;
	for (std::size_t i = 0; i <= cap; ++i) {
		Complexity::operation_counter += Complexity::for_inner + 3 + 2 * Complexity::braced_init;
		dp.push_back(0);
		res.emplace_back();
		new_res.emplace_back();
	}

	Complexity::operation_counter += Complexity::for_outer + 1;
	for (std::size_t i = 0; i < cost.size(); ++i) {
		Complexity::operation_counter += Complexity::for_inner + 4;
		std::size_t j                 = cap;
		const auto  cost_i            = cost[i];
		Complexity::operation_counter += Complexity::while_outer;
		while (j >= cost_i) {
			Complexity::operation_counter += 5;
			const auto curr               = dp[j - cost_i] + val[i];

			Complexity::operation_counter += Complexity::if_ + 2;
			if (dp[j] < curr) {
				Complexity::operation_counter += 2 + Complexity::braced_init;
				dp[j]                         = curr;
				new_res[j]                    = {i};
				Complexity::operation_counter += Complexity::for_outer + 2;
				for (const auto& k : res[j - cost_i]) {
					Complexity::operation_counter += Complexity::for_inner + 2;
					new_res[j].push_back(k);
				}
			}

			Complexity::operation_counter += 2;
			j                             -= 1;
		}
	}

	Complexity::operation_counter += Complexity::return_;
	return {res[cap], dp[cap]};
}

Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path) {
	Complexity::operation_counter += Complexity::if_ + 2;
	if (path.empty()) {
		Complexity::operation_counter += Complexity::return_;
		return 0;
	}
	Complexity::operation_counter += 3 + Complexity::for_outer;
	Graph::WeightT res            = 0;
	for (std::size_t i = 0; i < path.size() - 1; ++i) {
		Complexity::operation_counter += Complexity::for_inner + 5 + Complexity::get_edge_weight;
		res                           += wing.get_edge_weight(path[i], path[i + 1]);
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::size_t get_which_wing(
	const Facility_ADT&  G,
	const Graph::VertexT v
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

std::vector<Graph::VertexT> reconstruct_path(
	const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
	Graph::VertexT                                            sink
) {
	Complexity::operation_counter += 1 + Complexity::braced_init;
	std::vector res               = {sink};
	Complexity::operation_counter += Complexity::while_outer;
	while (prev.contains(sink)) {
		Complexity::operation_counter += Complexity::while_inner + 1 + 3;
		sink                          = prev.at(sink);
		res.push_back(sink);
	}
	Complexity::operation_counter += Complexity::reverse(res.size()) + Complexity::return_;
	std::ranges::reverse(res);
	return res;
}

std::unordered_map<Graph::VertexT, Graph::VertexT> dijkstra(
	const Graph&         g,
	const Graph::VertexT source
) {
	Complexity::operation_counter += 1;
	std::unordered_map<Graph::VertexT, Graph::WeightT> dist;

	Complexity::operation_counter += Complexity::for_outer + 1;
	for (const auto& v : g.get_vertices()) {
		Complexity::operation_counter += Complexity::for_inner + 1;
		dist[v]                       = std::numeric_limits<Graph::WeightT>::max();
	}

	Complexity::operation_counter += 1;
	dist[source]                  = 0;

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

		Complexity::operation_counter += Complexity::for_outer + Complexity::get_neighbours(g.size());
		for (const auto& [v, w] : g.get_neighbors(u)) {
			Complexity::operation_counter += Complexity::for_inner + Complexity::get_edge_weight + 1;
			Complexity::operation_counter += Complexity::if_ + 4;
			if (dist[u] + w < dist[v]) {
				Complexity::operation_counter += 6;
				prev[v]                       = u;
				dist[v]                       = dist[u] + w;
				pq.emplace(-dist[v], v);
			}
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return prev;
}

std::vector<Graph::VertexT> dijkstra_to(const Graph& g, const Graph::VertexT source, const Graph::VertexT sink) {
	Complexity::operation_counter += 1;
	std::unordered_map<Graph::VertexT, Graph::WeightT> dist;

	Complexity::operation_counter += Complexity::for_outer + 1;
	for (const auto& v : g.get_vertices()) {
		Complexity::operation_counter += Complexity::for_inner + 1;
		dist[v]                       = std::numeric_limits<Graph::WeightT>::max();
	}

	Complexity::operation_counter += 1;
	dist[source]                  = 0;

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
		if (u == sink) {
			Complexity::operation_counter += Complexity::return_;
			return reconstruct_path(prev, sink);
		}

		Complexity::operation_counter += Complexity::for_outer + Complexity::get_neighbours(g.size());
		for (const auto& [v, w] : g.get_neighbors(u)) {
			Complexity::operation_counter += Complexity::for_inner + Complexity::get_edge_weight + 1;
			Complexity::operation_counter += Complexity::if_ + 4;
			if (dist[u] + w < dist[v]) {
				Complexity::operation_counter += 6;
				prev[v]                       = u;
				dist[v]                       = dist[u] + w;
				pq.emplace(-dist[v], v);
			}
		}
	}
	throw std::runtime_error("Imaginary vertex in dijkstra_to");
}

Graph flatten_graph(const Facility_ADT& G) {
	Complexity::operation_counter += Complexity::for_outer + 2;
	Graph res{};
	for (const auto& wing : G.first) {
		Complexity::operation_counter += Complexity::for_inner + Complexity::for_outer + 1;
		for (const auto& v : wing.get_vertices()) {
			Complexity::operation_counter += Complexity::for_inner + 1;
			res.add_vertex(v);
		}
		Complexity::operation_counter += Complexity::for_outer + 1;
		for (const auto& [u, v, w] : wing.get_edges()) {
			Complexity::operation_counter += Complexity::for_inner + 6;
			res.add_edge(u, v, w);
		}
	}

	Complexity::operation_counter += Complexity::for_outer + 2;
	for (const auto& [u, v] : G.second) {
		Complexity::operation_counter += Complexity::for_inner + 3;
		res.add_edge(u, v, 1);
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::size_t get_weight_cost(const std::size_t weight) {
	Complexity::operation_counter += Complexity::return_ + 1;
	Complexity::operation_counter += Complexity::if_ + 1;
	if (weight == 1) {
		return 4 * weight + 5;
	}
	Complexity::operation_counter += Complexity::if_ + 1;
	if (weight == 2) {
		return 4 * weight + 5;
	}
	Complexity::operation_counter += Complexity::if_ + 1;
	if (weight == 3) {
		return 4 * weight + 7;
	}
	Complexity::operation_counter += Complexity::if_ + 1;
	if (weight >= 4) {
		return 4 * weight + 8;
	}
	throw std::runtime_error("weight outside of 1 - 5");
}

std::vector<Graph::VertexT> get_reduced_supplies(
	const Graph&                                                            g,
	const std::unordered_set<Graph::VertexT>&                               supplies,
	const std::unordered_map<Graph::VertexT, std::size_t>&                  supply_weight,
	const std::unordered_map<Graph::VertexT, std::size_t>&                  supply_value,
	const std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> >& entry_path,
	const std::size_t                                                       budget) {
	Complexity::operation_counter += 3;
	std::vector<Graph::VertexT> supplies_ordered{};
	supplies_ordered.reserve(supplies.size());
	std::vector<std::size_t> supply_value_ordered{};
	supply_value_ordered.reserve(supplies.size());
	std::vector<std::size_t> supply_cost_ordered{};
	supply_cost_ordered.reserve(supplies.size());

	Complexity::operation_counter += Complexity::for_outer;
	for (const auto& v : supplies) {
		Complexity::operation_counter += Complexity::for_inner + 7;
		supply_value_ordered.push_back(supply_value.at(v));
		supply_cost_ordered.push_back(get_path_length(g, entry_path.at(v)) * get_weight_cost(supply_weight.at(v)));
		supply_value_ordered.push_back(v);
	}

	Complexity::operation_counter += Complexity::for_outer + 3;
	std::vector<Graph::VertexT> res{};
	for (const auto& i : std::get<0>(knapsack(4 * budget, supply_value_ordered, supply_cost_ordered))) {
		Complexity::operation_counter += Complexity::for_inner + 2;
		res.push_back(supplies_ordered[i]);;
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

Graph::VertexT get_other_junction(const Facility_ADT& G, const Graph::VertexT v) {
	Complexity::operation_counter += Complexity::for_outer + 1;
	for (const auto& [ju, jv] : G.second) {
		Complexity::operation_counter += Complexity::for_inner + 2 + Complexity::if_;
		if (ju == v) {
			Complexity::operation_counter += Complexity::return_ + 1;
			return jv;
		}
		Complexity::operation_counter += 2 + Complexity::if_;
		if (jv == v) {
			Complexity::operation_counter += Complexity::return_ + 1;
			return ju;
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return v;
}

std::vector<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>&           supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	const std::unordered_set<SupplyID>&                 found_supply_ids) {
	Complexity::operation_counter += 1 + Complexity::for_outer;
	std::vector<Graph::VertexT> res{};
	for (const auto& supply : supplies) {
		Complexity::operation_counter += Complexity::for_inner + Complexity::if_ + 3;
		if (!found_supply_ids.contains(vertex_to_supply_id.at(supply))) {
			Complexity::operation_counter += 1;
			res.push_back(supply);
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::map<std::vector<Graph::VertexT>, std::unordered_set<std::size_t> > get_supply_wing_paths(
	const Facility_ADT&                                              G,
	const std::vector<Graph::VertexT>&                               supplies,
	std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > entry_to_supply) {
	Complexity::operation_counter += 1 + 1 + Complexity::for_outer;
	std::unordered_set<Graph::VertexT> junctions{};
	for (const auto& [ju, jv] : G.second) {
		Complexity::operation_counter += Complexity::for_inner + 4;
		junctions.insert(ju);
		junctions.insert(jv);
	}

	Complexity::operation_counter += 2 + Complexity::for_outer;
	std::map<std::vector<Graph::VertexT>, std::unordered_set<std::size_t> > res{};
	for (std::size_t s_idx = 0; s_idx < supplies.size(); ++s_idx) {
		Complexity::operation_counter += Complexity::for_inner + 8 + 2 * Complexity::braced_init +
				Complexity::for_outer;
		std::vector<Graph::VertexT> junction_path{};
		auto                        curr_path = entry_to_supply[supplies[s_idx]];
		auto                        curr      = curr_path.at(0);
		auto                        next      = curr_path.at(1);
		for (std::size_t i = 0; i < curr_path.size() - 1; ++i) {
			Complexity::operation_counter += Complexity::for_inner + 3 + Complexity::if_;
			if (junctions.contains(curr) && next == get_other_junction(G, curr)) {
				Complexity::operation_counter += 2;
				junction_path.push_back(curr);
				junction_path.push_back(next);
			}
			Complexity::operation_counter += 3;
			curr                          = next;
			next                          = curr_path.at(i + 2);
		}

		if (res.contains(junction_path)) {
			res[junction_path].insert(s_idx);
		} else {
			res[junction_path] = {s_idx};
		}
	}

	Complexity::operation_counter += Complexity::return_;
	return res;
}

std::vector<Graph::VertexT> ember_rescue(
	const Facility_ADT&                                    G,
	Graph::VertexT                                         entry,
	const std::unordered_set<Graph::VertexT>&              exits,
	const std::unordered_set<Graph::VertexT>&              supplies,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_weight,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_value,
	const std::unordered_map<Graph::VertexT, SupplyID>&    vertex_to_supply_id,
	std::unordered_set<SupplyID>                           found_supply_ids
) {
	return {};
}
