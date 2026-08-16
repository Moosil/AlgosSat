#pragma once
#include <algorithm>
#include <unordered_map>

#include "graph.h"

using VertexT  = Graph::VertexT;
using SupplyID = int;
using WeightT  = Graph::WeightT;

std::unordered_map<VertexT, VertexT> dfs(const Graph& g, VertexT source);

std::vector<VertexT> get_path_from_dfs(
	VertexT                              source,
	VertexT                              sink,
	std::unordered_map<VertexT, VertexT> prev);

std::vector<VertexT> get_supplies_to_collect(
	const std::unordered_set<VertexT>&           supplies,
	const std::unordered_map<VertexT, SupplyID>& vertex_to_supply_id,
	std::unordered_set<SupplyID>&                found_supply_ids,
	const std::vector<SupplyID>&                 supply_storage);

WeightT get_path_length(const Graph& wing, const std::vector<VertexT>& path);

Graph get_F(
	const std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT> > >& G,
	VertexT                                                                                 entry,
	const std::vector<VertexT>&                                                             supplies,
	const std::unordered_set<VertexT>&                                                      exits,
	const std::unordered_map<std::size_t, std::unordered_map<VertexT, VertexT> >&           prevs);

std::vector<VertexT> reconstruct_path(const std::unordered_map<VertexT, VertexT>& prev, VertexT sink);

std::unordered_map<VertexT, std::vector<VertexT> > dijkstra(
	const Graph&                       g,
	VertexT                            source,
	const std::unordered_set<VertexT>& sinks);

std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT> > > get_path_matrix(
	const Graph&                F,
	VertexT                     entry,
	std::unordered_set<VertexT> exits,
	std::vector<VertexT>        supplies);

std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT> > get_path_cost_matrix(
	const Graph&                                                                            F,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT> > >& path_matrix);

std::pair<std::vector<VertexT>, WeightT> dp_recursive(
	VertexT                                                                   source,
	const std::vector<VertexT>&                                               supplies,
	const std::unordered_set<VertexT>&                                        exits,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT> >& path_cost_matrix,
	size_t                                                                    fuel,
	uint32_t                                                                  mask,
	std::unordered_map<uint64_t, std::pair<std::vector<VertexT>, WeightT> >&  memo
);

std::vector<VertexT> dp(
	VertexT                                                                   entry,
	const std::vector<VertexT>&                                               supplies,
	const std::unordered_set<VertexT>&                                        exits,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT> >& path_cost_matrix,
	size_t                                                                    fuel);

std::vector<VertexT> get_F_path_from_H_path(
	const std::vector<VertexT>&                                                             H_path,
	const std::unordered_map<VertexT, std::unordered_map<VertexT, std::vector<VertexT> > >& path_matrix);

std::size_t get_which_wing(
	const std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT> > >& G,
	VertexT                                                                                 v);

std::vector<VertexT> get_G_path_from_F_path(
	const std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT> > >& G,
	const std::vector<VertexT>&                                                             F_path,
	const std::unordered_map<std::size_t, std::unordered_map<VertexT, VertexT> >&           prevs);

void get_new_supply_storage(
	const std::vector<VertexT>&                  supplies,
	std::vector<SupplyID>&                 supply_storage,
	const std::unordered_map<VertexT, SupplyID>& vertex_to_supply_id,
	size_t                                       num_of_supplies_to_collect,
	const std::vector<VertexT>&                  H_path);

std::vector<VertexT> ember_rescue(
	std::pair<std::vector<Graph>, std::unordered_set<std::pair<VertexT, VertexT> > > G,
	VertexT                                                                          entry,
	const std::unordered_set<VertexT>&                                               supplies,
	const std::unordered_set<VertexT>&                                               exits,
	std::vector<SupplyID>&                                                           supply_storage,
	const std::unordered_map<VertexT, SupplyID>&                                     vertex_to_supply_id,
	std::unordered_set<SupplyID>                                                     found_supply_ids
);
