#pragma once
#include <algorithm>
#include <unordered_map>

#include "facility.h"
#include "graph.h"

using SupplyID = int;

using Facility_ADT = std::pair<std::vector<Graph>, std::unordered_set<std::pair<Graph::VertexT, Graph::VertexT>, Facility::pair_hash>>;

std::unordered_map<Graph::VertexT, Graph::VertexT> dfs(const Graph& g, Graph::VertexT source);

std::vector<Graph::VertexT> get_path_from_dfs(
	Graph::VertexT                              source,
	Graph::VertexT                              sink,
	std::unordered_map<Graph::VertexT, Graph::VertexT> prev);

std::vector<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>&           supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID>&                found_supply_ids,
	const std::vector<SupplyID>&                 supply_storage);

Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path);

Graph get_F(
	const Facility_ADT& G,
	Graph::VertexT                                                                                 entry,
	const std::vector<Graph::VertexT>&                                                             supplies,
	const std::unordered_set<Graph::VertexT>&                                                      exits,
	const std::unordered_map<std::size_t, std::unordered_map<Graph::VertexT, Graph::VertexT> >&           prevs);

std::vector<Graph::VertexT> reconstruct_path(const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev, Graph::VertexT sink);

std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > dijkstra(
	const Graph&                       g,
	Graph::VertexT                            source,
	const std::unordered_set<Graph::VertexT>& sinks);

std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > > get_path_matrix(
	const Graph&                F,
	Graph::VertexT                     entry,
	std::unordered_set<Graph::VertexT> exits,
	std::vector<Graph::VertexT>        supplies);

std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> > get_path_cost_matrix(
	const Graph&                                                                            F,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > >& path_matrix);

std::pair<std::vector<Graph::VertexT>, Graph::WeightT> dp_recursive(
	Graph::VertexT                                                                   source,
	const std::vector<Graph::VertexT>&                                               supplies,
	const std::unordered_set<Graph::VertexT>&                                        exits,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> >& path_cost_matrix,
	size_t                                                                    fuel,
	uint32_t                                                                  mask,
	std::unordered_map<uint64_t, std::pair<std::vector<Graph::VertexT>, Graph::WeightT> >&  memo
);

std::vector<Graph::VertexT> dp(
	Graph::VertexT                                                                   entry,
	const std::vector<Graph::VertexT>&                                               supplies,
	const std::unordered_set<Graph::VertexT>&                                        exits,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, Graph::WeightT> >& path_cost_matrix,
	size_t                                                                    fuel);

std::vector<Graph::VertexT> get_F_path_from_H_path(
	const std::vector<Graph::VertexT>&                                                             H_path,
	const std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > >& path_matrix);

std::size_t get_which_wing(
	const Facility_ADT& G,
	Graph::VertexT                                                                                 v);

std::vector<Graph::VertexT> get_G_path_from_F_path(
	const Facility_ADT& G,
	const std::vector<Graph::VertexT>&                                                             F_path,
	const std::unordered_map<std::size_t, std::unordered_map<Graph::VertexT, Graph::VertexT> >&           prevs);

void get_new_supply_storage(
	const std::vector<Graph::VertexT>&                  supplies,
	std::vector<SupplyID>&                 supply_storage,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	size_t                                       num_of_supplies_to_collect,
	const std::vector<Graph::VertexT>&                  H_path);

std::vector<Graph::VertexT> ember_rescue(
	const Facility_ADT& G,
	Graph::VertexT                                                                          entry,
	const std::unordered_set<Graph::VertexT>&                                               supplies,
	const std::unordered_set<Graph::VertexT>&                                               exits,
	std::vector<SupplyID>&                                                           supply_storage,
	const std::unordered_map<Graph::VertexT, SupplyID>&                                     vertex_to_supply_id,
	std::unordered_set<SupplyID>                                                     found_supply_ids
);
