#pragma once
#include <algorithm>
#include <map>
#include <unordered_map>

#include "complexity.h"
#include "facility.h"
#include "graph.h"

class Drone {
public:
	using SupplyID = int;

	using Facility_ADT = std::pair<std::vector<Graph>, std::set<std::pair<Graph::VertexT, Graph::VertexT> > >;

	explicit Drone(const std::shared_ptr<Complexity>& complexity):
		complexity{complexity} {}

	Drone() = delete;

	std::shared_ptr<Complexity> complexity;

	[[nodiscard]] std::tuple<std::vector<std::size_t>, std::size_t> knapsack_capacity(
		std::size_t                     cap,
		const std::vector<std::size_t>& val,
		const std::vector<std::size_t>& cost) const;

	[[nodiscard]] std::tuple<std::vector<std::size_t>, std::size_t> knapsack_value(
		std::size_t                     cap,
		const std::vector<std::size_t>& val,
		const std::vector<std::size_t>& cost) const;

	[[nodiscard]] Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path) const;

	[[nodiscard]] const Graph& get_which_wing(
		const Facility_ADT& G,
		Graph::VertexT      v
	) const;

	template<typename T>
	long long find(const std::vector<T>& l, const T& x, const std::size_t start) const {
		complexity->push_stack("find");
		complexity->add(Complexity::for_outer + 1);
		for (std::size_t i = start; i < l.size(); ++i) {
			complexity->add(Complexity::for_inner + Complexity::if_ + 2);
			if (l.at(i) == x) {
				complexity->add(Complexity::return_);
				return static_cast<long long>(i);
			}
		}
		complexity->add(Complexity::return_);
		complexity->pop_stack();
		return -1;
	}

	template<typename T>
	void csort(std::vector<T>& l) const {
		complexity->add(1 + Complexity::for_outer);
		const std::size_t n = l.size();
		for (std::size_t i = 1; i < n; ++i) {
			complexity->add(Complexity::for_inner + 4 + Complexity::while_outer + 4);
			T key = l[i];
			int j = static_cast<int>(i) - 1;
			for (; j >= 0 && l[j] < key; --j) {
				complexity->add(Complexity::while_inner + 4 + 6);
				l[j + 1] = l[j];
			}
			complexity->add(2);
			l[j + 1] = key;
		}
	}

	[[nodiscard]] std::vector<Graph::VertexT> reconstruct_path(
		const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
		Graph::VertexT                                            sink) const;

	[[nodiscard]] std::vector<Graph::VertexT> reconstruct_path_to(
		const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
		Graph::VertexT                                            source,
		Graph::VertexT                                            sink
	) const;

	[[nodiscard]] std::unordered_map<Graph::VertexT, Graph::VertexT> dijkstra(
		const Graph&   g,
		Graph::VertexT source) const;

	[[nodiscard]] Graph flatten_graph(const Facility_ADT& G) const;

	[[nodiscard]] std::size_t get_weight_cost(
		std::size_t weight,
		std::size_t cap,
		std::size_t path_len) const;

	[[nodiscard]] std::vector<Graph::VertexT> get_reduced_supplies(
		const Graph&                                                            g,
		const std::unordered_set<Graph::VertexT>&                               supplies,
		const std::unordered_map<Graph::VertexT, std::size_t>&                  supply_weight,
		const std::unordered_map<Graph::VertexT, std::size_t>&                  supply_value,
		const std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> >& entry_path,
		std::size_t                                                             budget,
		std::size_t                                                             drone_capacity) const;

	[[nodiscard]] Graph::VertexT get_other_junction(const Facility_ADT& G, Graph::VertexT v) const;

	[[nodiscard]] std::unordered_set<Graph::VertexT> get_supplies_to_collect(
		const std::unordered_set<Graph::VertexT>&           supplies,
		const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
		const std::unordered_set<SupplyID>&                 found_supply_ids) const;

	[[nodiscard]] std::map<std::vector<Graph::VertexT>, std::unordered_set<size_t> > get_supply_wing_paths(
		const Facility_ADT&                                                     G,
		const std::vector<Graph::VertexT>&                                      supplies,
		const std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> >& entry_to_supply) const;

	void knapsack_supplies(
		std::vector<Graph::VertexT>&                                                     supplies,
		const std::vector<std::size_t>&                                                  supply_weight,
		const std::vector<std::size_t>&                                                  supply_value,
		std::vector<std::size_t>&                                                        supplies_in_junction,
		std::size_t                                                                      drone_capacity,
		Graph::VertexT                                                                   entry,
		const std::vector<Graph::VertexT>&                                               backtrack,
		std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> >& res) const;

	void clear_junction_path(
		const Facility_ADT&                                                              G,
		Graph::VertexT                                                                   entry,
		Graph::VertexT                                                                   curr,
		const std::vector<Graph::VertexT>&                                               backtrack,
		std::vector<Graph::VertexT>&                                                     supplies,
		const std::vector<std::size_t>&                                                  supply_weight,
		const std::vector<std::size_t>&                                                  supply_value,
		std::map<std::vector<Graph::VertexT>, std::unordered_set<size_t> >&              supply_path,
		const std::vector<Graph::VertexT>&                                               inter_wing_path,
		std::size_t                                                                      drone_capacity,
		std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> >& res) const;

	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > clear_branch(
		const Facility_ADT&                                                 G,
		Graph::VertexT                                                      entry,
		Graph::VertexT                                                      orig,
		Graph::VertexT                                                      branch,
		const Graph&                                                        orig_wing,
		std::vector<Graph::VertexT>&                                        backtrack,
		std::vector<Graph::VertexT>&                                        supplies,
		const std::vector<std::size_t>&                                     supply_weight,
		const std::vector<std::size_t>&                                     supply_value,
		std::map<std::vector<Graph::VertexT>, std::unordered_set<size_t> >& supply_path,
		const std::vector<Graph::VertexT>&                                  inter_wing_path,
		std::size_t                                                         drone_capacity) const;

public:
	[[nodiscard]] std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > ember_rescue(
		const Facility_ADT&                                    G,
		Graph::VertexT                                         entry,
		const std::unordered_set<Graph::VertexT>&              exits,
		std::unordered_set<Graph::VertexT>                     supplies,
		const std::unordered_map<Graph::VertexT, std::size_t>& supply_weight,
		const std::unordered_map<Graph::VertexT, std::size_t>& supply_value,
		std::size_t                                            budget,
		std::size_t                                            drone_capacity,
		const std::unordered_map<Graph::VertexT, SupplyID>&    vertex_to_supply_id,
		const std::unordered_set<SupplyID>&                    found_supply_ids
	) const;
};