#pragma once
#include <algorithm>
#include <unordered_map>

#include "facility.h"
#include "graph.h"

using SupplyID = int;

using Facility_ADT = std::pair<std::vector<Graph>, std::unordered_set<std::pair<Graph::VertexT, Graph::VertexT>,
	Facility::pair_hash> >;

std::vector<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>&           supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID>&                       found_supply_ids);

Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path);

std::vector<Graph::VertexT> reconstruct_path(
	const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
	Graph::VertexT                                            sink);

std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > dijkstra(
	const Graph&   g,
	Graph::VertexT source);

std::size_t get_which_wing(
	const Facility_ADT& G,
	Graph::VertexT      v);

std::vector<Graph::VertexT> ember_rescue(
	const Facility_ADT&                                    G,
	Graph::VertexT                                         entry,
	const std::unordered_set<Graph::VertexT>&              exits,
	const std::unordered_set<Graph::VertexT>&              supplies,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_weight,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_value,
	const std::unordered_map<Graph::VertexT, SupplyID>&    vertex_to_supply_id,
	std::unordered_set<SupplyID>                           found_supply_ids
);
