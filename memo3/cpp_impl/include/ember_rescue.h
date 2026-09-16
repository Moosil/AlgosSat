#pragma once
#include <algorithm>
#include <map>
#include <unordered_map>

#include "complexity.h"
#include "facility.h"
#include "graph.h"

using SupplyID = int;

using Facility_ADT = std::pair<std::vector<Graph>, std::set<std::pair<Graph::VertexT, Graph::VertexT> > >;

std::tuple<std::vector<std::size_t>, std::size_t> knapsack(
	std::size_t                     cap,
	const std::vector<std::size_t>& val,
	const std::vector<std::size_t>& cost);

Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path);

const Graph& get_which_wing(
	const Facility_ADT& G,
	Graph::VertexT      v
);

template<typename T>
long long find(const std::vector<T>& l, const T& x, const std::size_t start) {
	Complexity::operation_counter += Complexity::for_outer + 1;
	for (std::size_t i = start; i < l.size(); ++i) {
		Complexity::operation_counter += Complexity::for_inner + Complexity::if_ + 2;
		if (l[i] == x) {
			Complexity::operation_counter += Complexity::return_;
			return static_cast<long long>(i);
		}
	}
	Complexity::operation_counter += Complexity::return_;
	return -1;
}

std::vector<Graph::VertexT> reconstruct_path(
	const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
	Graph::VertexT                                            sink);

std::unordered_map<Graph::VertexT, Graph::VertexT> dijkstra(
	const Graph&   g,
	Graph::VertexT source);

std::vector<Graph::VertexT> dijkstra_to(
	const Graph&   g,
	Graph::VertexT source,
	Graph::VertexT sink);

Graph flatten_graph(const Facility_ADT& G);

std::size_t get_weight_cost(std::size_t weight);

std::vector<Graph::VertexT> get_reduced_supplies(
	const Graph&                                                     g,
	std::unordered_set<Graph::VertexT>                               supplies,
	std::unordered_set<Graph::VertexT, std::size_t>                  supply_weight,
	std::unordered_map<Graph::VertexT, std::size_t>                  supply_value,
	std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > entry_path,
	std::size_t                                                      budget);

Graph::VertexT get_other_junction(const Facility_ADT& G, Graph::VertexT v);

std::unordered_set<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>&           supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	const std::unordered_set<SupplyID>&                 found_supply_ids);

std::map<std::vector<Graph::VertexT>, std::unordered_set<Graph::VertexT> > get_supply_wing_paths(
	const Facility_ADT&                                                     G,
	const std::vector<Graph::VertexT>&                                      supplies,
	const std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> >& entry_to_supply);

void knapsack_supplies(
	std::vector<Graph::VertexT>&                                                     supplies,
	const std::vector<std::size_t>&                                                  supply_weight,
	const std::vector<std::size_t>&                                                  supply_value,
	std::vector<std::size_t>&                                                        supplies_in_junction,
	Graph::VertexT                                                                   entry,
	const std::vector<Graph::VertexT>&                                               backtrack,
	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> >& res);

void clear_junction_path(
	const Facility_ADT&                                                              G,
	Graph::VertexT                                                                   entry,
	Graph::VertexT                                                                   curr,
	std::vector<Graph::VertexT>                                                      backtrack,
	std::vector<Graph::VertexT>                                                      supplies,
	std::vector<std::size_t>                                                         supply_weight,
	std::vector<std::size_t>                                                         supply_value,
	std::map<std::vector<Graph::VertexT>, std::unordered_set<Graph::VertexT> >&      supply_path,
	const std::vector<Graph::VertexT>&                                               inter_wing_path,
	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> >& res);

std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > clear_branch(
	const Facility_ADT&                                                         G,
	Graph::VertexT                                                              entry,
	Graph::VertexT                                                              orig,
	Graph::VertexT                                                              branch,
	const Graph&                                                                orig_wing,
	std::vector<Graph::VertexT>                                                 backtrack,
	std::vector<Graph::VertexT>                                                 supplies,
	std::vector<std::size_t>                                                    supply_weight,
	std::vector<std::size_t>                                                    supply_value,
	std::map<std::vector<Graph::VertexT>, std::unordered_set<Graph::VertexT> >& supply_path,
	std::vector<Graph::VertexT>                                                 inter_wing_path);

std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > ember_rescue(
	const Facility_ADT&                                    G,
	Graph::VertexT                                         entry,
	const std::unordered_set<Graph::VertexT>&              exits,
	std::unordered_set<Graph::VertexT>                     supplies,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_weight,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_value,
	size_t                                                 budget,
	const std::unordered_map<Graph::VertexT, SupplyID>&    vertex_to_supply_id,
	std::unordered_set<SupplyID>                           found_supply_ids
);
