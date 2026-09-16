#include "ember_rescue.h"

#include <queue>
#include <ranges>
#include <stack>

#include "barkeep.h"
#include "complexity.h"

std::vector<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>&           supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	const std::unordered_set<SupplyID>&                 found_supply_ids
) {
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

std::unordered_map<Graph::VertexT, Graph::VertexT> dijkstra(
	const Graph&         g,
	const Graph::VertexT source
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
	Complexity::operation_counter += Complexity::return_;
	return prev;
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
