#include "ember_rescue.h"

#include <map>
#include <queue>
#include <ranges>
#include <stack>

#include "barkeep.h"

std::tuple<std::vector<std::size_t>, std::size_t> knapsack_capacity(
	const std::size_t               cap,
	const std::vector<std::size_t>& val,
	const std::vector<std::size_t>& cost) {
	std::vector<std::size_t> dp(cap + 1);
	Complexity::push_stack("knapsack");
	Complexity::add(3);
	std::vector<std::vector<std::size_t> > res(cap + 1);
	std::vector<std::vector<std::size_t> > new_res(cap + 1);

	Complexity::add(Complexity::for_outer);
	Complexity::add((Complexity::for_inner + 3 + 2 * Complexity::braced_init) * (cap + 1));

	Complexity::add(Complexity::for_outer + 1);
	for (std::size_t i = 0; i < cost.size(); ++i) {
		Complexity::add(Complexity::for_inner + 4);
		const std::size_t cost_i = cost.at(i);
		Complexity::add(Complexity::while_outer + 1);
		for (std::size_t j = cap; j >= cost_i; --j) {
			Complexity::add(5);
			const std::size_t curr = dp.at(j - cost_i) + val.at(i);

			Complexity::add(Complexity::if_ + 2);
			if (dp.at(j) < curr) {
				Complexity::add(2 + Complexity::braced_init);
				dp[j]      = curr;
				new_res[j] = {i};
				new_res.reserve(1 + res.at(j - cost_i).size());
				Complexity::add(Complexity::for_outer + 2);
				Complexity::add((Complexity::for_inner + 2) * res.at(j - cost_i).size());
				new_res[j].append_range(res.at(j - cost_i));
			}

			Complexity::add(2);
		}
		Complexity::add(1);
		res = new_res;
	}

	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return {res.at(cap), dp.at(cap)};
}

// Neal Young (https://cstheory.stackexchange.com/users/8237/neal-young), Is the knapsack variant with small profit and unlimited repetition of items NP-hard?, URL (version: 2020-08-20): https://cstheory.stackexchange.com/q/47443
std::tuple<std::vector<std::size_t>, std::size_t> knapsack_value(
	const std::size_t               cap,
	const std::vector<std::size_t>& val,
	const std::vector<std::size_t>& cost) {
	Complexity::push_stack("knapsack");
	Complexity::add(1 + Complexity::for_outer);
	std::size_t total_val = 0;
	for (const std::size_t v : val) {
		Complexity::add(Complexity::for_inner + 2);
		total_val += v;
	}

	std::vector<std::size_t> dp(total_val + 1);
	Complexity::add(3);
	std::vector<std::vector<std::size_t> > res(total_val + 1);
	std::vector<std::vector<std::size_t> > new_res(total_val + 1);

	Complexity::add(Complexity::for_outer);
	Complexity::add((Complexity::for_inner + 3 + 2 * Complexity::braced_init) * (total_val + 1));

	Complexity::add(Complexity::for_outer + 1);
	for (std::size_t i = 0; i < cost.size(); ++i) {
		Complexity::add(Complexity::for_inner + 4);
		const std::size_t val_i = val.at(i);
		Complexity::add(Complexity::while_outer + 1);
		for (std::size_t j = total_val; j >= val_i; --j) {
			Complexity::add(5);
			const std::size_t curr = dp.at(j - val_i) + cost.at(i);
			Complexity::add(Complexity::if_ + 2);
			if (dp.at(j) < curr) {
				Complexity::add(2 + Complexity::braced_init);
				dp[j]      = curr;
				new_res[j] = {i};
				new_res.reserve(1 + res.at(j - val_i).size());
				Complexity::add(Complexity::for_outer + 2);
				Complexity::add((Complexity::for_inner + 2) * res.at(j - val_i).size());
				new_res[j].append_range(res.at(j - val_i));
			}

			Complexity::add(2);
		}
		Complexity::add(1);
		res = new_res;
	}

	Complexity::add(1 + Complexity::while_outer + 1);
	for (; total_val > 0; --total_val) {
		Complexity::add(Complexity::while_inner + 1 + Complexity::if_ + 2);
		if (dp.at(total_val) <= cap) {
			Complexity::add(Complexity::return_ + Complexity::braced_init + 2);
			Complexity::pop_stack();
			return {res.at(total_val), dp.at(total_val)};
		}
		Complexity::add(2);
		--total_val;
	}
	Complexity::add(Complexity::return_ + 2 * Complexity::braced_init);
	Complexity::pop_stack();
	return {{}, 0};
}

Graph::WeightT get_path_length(const Graph& wing, const std::vector<Graph::VertexT>& path) {
	Complexity::push_stack("get_path_length");
	Complexity::add(Complexity::if_ + 2);
	if (path.empty()) {
		Complexity::add(Complexity::return_);
		Complexity::pop_stack();
		return 0;
	}
	Complexity::add(3 + Complexity::for_outer);
	Graph::WeightT res = 0;
	for (std::size_t i = 0; i < path.size() - 1; ++i) {
		Complexity::add(Complexity::for_inner + 5 + Complexity::get_edge_weight);
		res += wing.get_edge_weight(path.at(i), path.at(i + 1));
	}
	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return res;
}

const Graph& get_which_wing(
	const Facility_ADT&  G,
	const Graph::VertexT v
) {
	Complexity::push_stack("get_which_wing");
	Complexity::add(Complexity::for_outer + 1);
	for (const Graph& g : G.first) {
		Complexity::add(Complexity::for_inner + Complexity::if_ + 2);
		if (g.contains(v)) {
			Complexity::add(Complexity::return_);
			Complexity::pop_stack();
			return g;
		}
	}
	throw std::runtime_error("Imaginary vertex in get_which_wing");
}

std::vector<Graph::VertexT> reconstruct_path(
	const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
	const Graph::VertexT                                      sink
) {
	Complexity::push_stack("reconstruct_path");
	Complexity::add(1 + Complexity::braced_init + 1);
	std::vector    res  = {sink};
	Graph::VertexT curr = sink;
	Complexity::add(Complexity::while_outer + 1);
	while (prev.contains(curr)) {
		Complexity::add(Complexity::while_inner + 1 + 3);
		curr = prev.at(curr);
		res.push_back(curr);
	}
	Complexity::add(Complexity::reverse(res.size()) + Complexity::return_);
	std::ranges::reverse(res);
	Complexity::pop_stack();
	return res;
}

std::vector<Graph::VertexT> reconstruct_path_to(
	const std::unordered_map<Graph::VertexT, Graph::VertexT>& prev,
	const Graph::VertexT                                      source,
	const Graph::VertexT                                      sink
) {
	Complexity::push_stack("reconstruct_path_to");
	std::vector    left_path{source};
	std::vector    right_path{sink};
	Graph::VertexT left  = source;
	Graph::VertexT right = sink;
	Complexity::add(4 + 2 * Complexity::braced_init);

	Complexity::add(Complexity::while_outer);
	while (prev.contains(left) || prev.contains(right)) {
		Complexity::add(Complexity::while_inner + 3);
		if (prev.contains(left)) {
			Complexity::add(3);
			left = prev.at(left);
			left_path.push_back(left);
		}
		Complexity::add(1 + Complexity::if_);

		if (prev.contains(right)) {
			Complexity::add(3);
			right = prev.at(right);
			right_path.push_back(right);
		}
		Complexity::add(1 + Complexity::if_);


		Complexity::add(
			Complexity::for_outer + 1 + left_path.size() * (
				Complexity::for_inner + 2 + Complexity::if_)
		);
		if (const auto it = std::ranges::find(left_path, right);
			it != left_path.end()) {
			Complexity::add(
				1 + Complexity::for_outer + std::distance(left_path.begin(), it) * (
					Complexity::for_inner + 2) + 1 + Complexity::for_outer + right_path.size() * (
					Complexity::for_inner + 4)
				+ Complexity::return_
			);
			std::vector<Graph::VertexT> res{left_path.begin(), it};
			res.append_range(std::views::reverse(right_path));
			Complexity::pop_stack();
			return res;
		}

		Complexity::add(
			Complexity::for_outer + 1 + right_path.size() * (
				Complexity::for_inner + 2 + Complexity::if_)
		);
		if (const auto it = std::ranges::find(right_path, left);
			it != right_path.end()) {
			Complexity::add(
				1 + Complexity::for_outer + left_path.size() * (Complexity::for_inner + 2)
				+ 1 + Complexity::for_outer + std::distance(right_path.begin(), it) * (Complexity::for_inner + 3) +
				Complexity::return_
			);
			left_path.append_range(
				std::ranges::subrange(
					std::make_reverse_iterator(it),
					std::make_reverse_iterator(right_path.begin())
				)
			);
			Complexity::pop_stack();
			return left_path;
		}
	}
	throw std::runtime_error{"Opps"};
}

std::unordered_map<Graph::VertexT, Graph::VertexT> dijkstra(
	const Graph&         g,
	const Graph::VertexT source
) {
	Complexity::push_stack("dijkstra");
	Complexity::add(1);
	std::unordered_map<Graph::VertexT, Graph::WeightT> dist;

	Complexity::add(Complexity::for_outer + 1);
	for (const Graph::VertexT v : g.get_vertices()) {
		Complexity::add(Complexity::for_inner + 1);
		dist[v] = std::numeric_limits<Graph::WeightT>::max();
	}

	Complexity::add(1);
	dist[source] = 0;

	Complexity::add(1);
	std::unordered_map<Graph::VertexT, Graph::VertexT> prev;

	Complexity::add(1 + Complexity::for_outer);
	Complexity::add(g.size() * (Complexity::for_inner + 2));
	std::priority_queue<std::pair<int64_t, Graph::VertexT> > pq;
	pq.emplace(0, source);

	Complexity::add(Complexity::while_outer + 2);
	while (!pq.empty()) {
		const auto [d, u] = pq.top();
		pq.pop();
		if (dist.at(u) < static_cast<std::size_t>(-d)) {
			continue;
		}
		Complexity::add(Complexity::while_inner + 2 + 1);

		Complexity::add(Complexity::for_outer + Complexity::get_neighbours(g.size()));
		for (const auto [v, w] : g.get_neighbours(u)) {
			Complexity::add(Complexity::for_inner + Complexity::get_edge_weight + 1);
			Complexity::add(Complexity::if_ + 4);
			if (dist.at(u) + w < dist.at(v)) {
				Complexity::add(6);
				prev[v] = u;
				dist[v] = dist.at(u) + w;
				pq.emplace(-static_cast<int64_t>(dist.at(v)), v);
			}
		}
	}
	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return prev;
}

Graph flatten_graph(const Facility_ADT& G) {
	Complexity::push_stack("flatten_graph");
	Complexity::add(Complexity::for_outer + 2);
	Graph res{};
	for (const Graph& wing : G.first) {
		Complexity::add(Complexity::for_inner + Complexity::for_outer + 1);
		for (const Graph::VertexT v : wing.get_vertices()) {
			Complexity::add(Complexity::for_inner + 1);
			res.add_vertex(v);
		}
		Complexity::add(Complexity::for_outer + 1);
		for (const auto& [u, v, w] : wing.get_edges()) {
			Complexity::add(Complexity::for_inner + 6);
			res.add_edge(u, v, w);
		}
	}

	Complexity::add(Complexity::for_outer + 2);
	for (const auto [u, v] : G.second) {
		Complexity::add(Complexity::for_inner + 3);
		res.add_edge(u, v, 1);
	}
	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return res;
}

std::size_t get_weight_cost(const std::size_t weight, const std::size_t drone_capacity, const std::size_t path_length) {
	Complexity::push_stack("get_weight_cost");
	Complexity::add(Complexity::if_ + 2);
	if (static_cast<float>(weight) >= .75 * static_cast<float>(drone_capacity)) {
		Complexity::add(Complexity::return_ + 1);
		Complexity::pop_stack();
		return static_cast<std::size_t>(ceil((static_cast<float>(weight) + 2) * static_cast<float>(path_length)));
	}

	Complexity::add(Complexity::return_ + 2);
	Complexity::pop_stack();
	return static_cast<std::size_t>(ceil(
		(static_cast<float>(weight) + 1 + static_cast<float>(weight) / static_cast<float>(drone_capacity)) *
		static_cast<float>(path_length)
	));
}

std::vector<Graph::VertexT> get_reduced_supplies(
	const Graph&                                                            g,
	const std::unordered_set<Graph::VertexT>&                               supplies,
	const std::unordered_map<Graph::VertexT, std::size_t>&                  supply_weight,
	const std::unordered_map<Graph::VertexT, std::size_t>&                  supply_value,
	const std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> >& entry_path,
	const std::size_t                                                       budget,
	const std::size_t                                                       drone_capacity) {
	Complexity::push_stack("get_reduced_supplies");
	Complexity::add(3);
	std::vector<Graph::VertexT> supplies_ordered{};
	supplies_ordered.reserve(supplies.size());
	std::vector<std::size_t> supply_value_ordered{};
	supply_value_ordered.reserve(supplies.size());
	std::vector<std::size_t> supply_cost_ordered{};
	supply_cost_ordered.reserve(supplies.size());

	Complexity::add(Complexity::for_outer);
	for (const Graph::VertexT v : supplies) {
		Complexity::add(Complexity::for_inner + 2 + Complexity::if_);
		if (const std::size_t w = supply_weight.at(v);
			w < drone_capacity) {
			Complexity::add(Complexity::for_inner + 5);
			supply_value_ordered.push_back(supply_value.at(v));
			supply_cost_ordered.push_back(
				get_weight_cost(w, drone_capacity, get_path_length(g, entry_path.at(v)))
			);
			supplies_ordered.push_back(v);
		}
	}

	Complexity::add(Complexity::for_outer + 3);
	std::vector<Graph::VertexT> res{};
	for (const std::size_t i : std::get<0>(knapsack_value(budget, supply_value_ordered, supply_cost_ordered))) {
		Complexity::add(Complexity::for_inner + 2);
		res.push_back(supplies_ordered.at(i));
	}
	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return res;
}

Graph::VertexT get_other_junction(const Facility_ADT& G, const Graph::VertexT v) {
	Complexity::push_stack("get_other_junction");
	Complexity::add(Complexity::for_outer + 1);
	for (const auto [ju, jv] : G.second) {
		Complexity::add(Complexity::for_inner + 2 + Complexity::if_);
		if (ju == v) {
			Complexity::add(Complexity::return_ + 1);
			Complexity::pop_stack();
			return jv;
		}
		Complexity::add(2 + Complexity::if_);
		if (jv == v) {
			Complexity::add(Complexity::return_ + 1);
			Complexity::pop_stack();
			return ju;
		}
	}
	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return v;
}

std::unordered_set<Graph::VertexT> get_supplies_to_collect(
	const std::unordered_set<Graph::VertexT>&           supplies,
	const std::unordered_map<Graph::VertexT, SupplyID>& vertex_to_supply_id,
	const std::unordered_set<SupplyID>&                 found_supply_ids) {
	Complexity::push_stack("get_supplies_to_collect");
	Complexity::add(1 + Complexity::for_outer);
	std::unordered_set<Graph::VertexT> res{};
	for (const Graph::VertexT supply : supplies) {
		Complexity::add(Complexity::for_inner + Complexity::if_ + 3);
		if (!found_supply_ids.contains(vertex_to_supply_id.at(supply))) {
			Complexity::add(1);
			res.insert(supply);
		}
	}
	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return res;
}

std::map<std::vector<Graph::VertexT>, std::unordered_set<size_t> > get_supply_wing_paths(
	const Facility_ADT&                                                     G,
	const std::vector<Graph::VertexT>&                                      supplies,
	const std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> >& entry_to_supply) {
	Complexity::push_stack("get_supply_wing_paths");
	Complexity::add(1 + 1 + Complexity::for_outer);
	std::unordered_set<Graph::VertexT> junctions{};
	for (const auto [ju, jv] : G.second) {
		Complexity::add(Complexity::for_inner + 4);
		junctions.insert(ju);
		junctions.insert(jv);
	}

	Complexity::add(2 + Complexity::for_outer);
	std::map<std::vector<Graph::VertexT>, std::unordered_set<std::size_t> > res{};
	for (std::size_t s_idx = 0; s_idx < supplies.size(); ++s_idx) {
		Complexity::add(
			Complexity::for_inner + 8 + 2 * Complexity::braced_init +
			Complexity::for_outer
		);
		std::vector<Graph::VertexT> junction_path{};
		const auto&                 curr_path = entry_to_supply.at(supplies.at(s_idx));
		Graph::VertexT              curr      = curr_path.at(0);
		Graph::VertexT              next      = curr_path.at(1);
		for (std::size_t i = 0; i < curr_path.size() - 2; ++i) {
			Complexity::add(Complexity::for_inner + 3 + Complexity::if_);
			if (junctions.contains(curr) && next == get_other_junction(G, curr)) {
				Complexity::add(2);
				junction_path.push_back(curr);
				junction_path.push_back(next);
			}
			Complexity::add(3);
			curr = next;
			next = curr_path.at(i + 2);
		}

		if (res.contains(junction_path)) {
			res[junction_path].insert(s_idx);
		} else {
			res[junction_path] = {s_idx};
		}
	}

	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return res;
}

void knapsack_supplies(
	std::vector<Graph::VertexT>&                                                     supplies,
	const std::vector<std::size_t>&                                                  supply_weight,
	const std::vector<std::size_t>&                                                  supply_value,
	std::vector<std::size_t>&                                                        supplies_in_junction,
	const std::size_t                                                                drone_capacity,
	const Graph::VertexT                                                             entry,
	const std::vector<Graph::VertexT>&                                               backtrack,
	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> >& res) {
	Complexity::push_stack("knapsack_supplies");
	Complexity::add(1 + Complexity::for_outer);
	std::size_t total_weight = 0;

	for (const std::size_t s_idx : supplies_in_junction) {
		Complexity::add(Complexity::for_inner + 3);
		total_weight += supply_weight.at(s_idx);
	}

	Complexity::add(Complexity::while_outer + 1);
	while (total_weight >= drone_capacity) {
		Complexity::add(Complexity::while_inner + 1);

		Complexity::add(2 + Complexity::for_outer);
		std::vector<std::size_t> in_junction_weight{};
		in_junction_weight.reserve(supplies_in_junction.size());

		for (const std::size_t s_idx : supplies_in_junction) {
			Complexity::add(Complexity::for_inner + 4);
			in_junction_weight.push_back(supply_weight.at(s_idx));
		}
		const auto sack = knapsack_capacity(drone_capacity, in_junction_weight, in_junction_weight);

		Complexity::add(Complexity::for_outer + 2);
		std::unordered_map<Graph::VertexT, std::vector<std::size_t> > sack_items{};
		for (const std::size_t ij_idx : std::get<0>(sack)) {
			Complexity::add(4 + Complexity::if_ + 1);
			const std::size_t in_junction_idx = supplies_in_junction.at(ij_idx);
			if (const Graph::VertexT curr_supply = supplies.at(in_junction_idx);
				sack_items.contains(curr_supply)) {
				Complexity::add(2);
				sack_items[curr_supply].push_back(in_junction_idx);
			} else {
				Complexity::add(1 + Complexity::braced_init);
				sack_items[curr_supply] = {in_junction_idx};
			}
		}

		std::vector<std::size_t> extra_supplies{}; {
			Complexity::add(5 + Complexity::while_outer + 1);
			std::size_t total_sack_weight = 0;
			bool        collecting_strays = false;
			for (long long i = static_cast<long long>(backtrack.size()) - 1; i >= 0; --i) {
				Complexity::add(1 + Complexity::while_inner + 2 + Complexity::if_ + 1);
				if (Graph::VertexT curr_pos = backtrack.at(i);
					sack_items.contains(curr_pos)) {
					Complexity::add(2 + Complexity::for_outer);
					collecting_strays = true;
					for (const std::size_t s_idx : sack_items.at(curr_pos)) {
						Complexity::add(Complexity::for_inner + 3 + Complexity::while_outer + 2);
						std::size_t w          = supply_weight.at(s_idx);
						std::size_t drop_count = 1;
						while (total_sack_weight + w > drone_capacity) {
							Complexity::add(
								Complexity::for_inner + 16 + Complexity::braced_init +
								Complexity::while_outer + 3
							);
							const std::size_t del_s_idx = extra_supplies.back();
							extra_supplies.pop_back();
							Graph::VertexT del_pos = backtrack.at(i + drop_count);
							while (del_pos != supplies[del_s_idx] && find(supplies, del_pos, 0) != -1) {
								Complexity::add(Complexity::while_inner + 1 + 5);
								++drop_count;
								del_pos = backtrack.at(i + drop_count);
							}
							std::size_t del_w = supply_weight.at(del_s_idx);
							res.emplace_back(del_pos, 2, del_w, supply_value.at(del_s_idx));
							total_sack_weight   -= del_w;
							supplies[del_s_idx] = del_pos;
							++drop_count;
						}
						Complexity::add(4 + Complexity::braced_init);
						total_sack_weight += w;
						res.emplace_back(curr_pos, 3, w, supply_value.at(s_idx));
					}
				} else {
					Complexity::add(Complexity::if_);
					if (collecting_strays) {
						Complexity::add(1 + Complexity::while_outer + 1);
						std::size_t s_idx = find(supplies, curr_pos, 0);
						while (s_idx != -1) {
							Complexity::add(Complexity::while_inner + 1 + Complexity::if_);
							if (find(supplies_in_junction, s_idx, 0) != -1) {
								Complexity::add(2 + 2 + Complexity::if_);
								if (const std::size_t w = supply_weight.at(s_idx);
									total_sack_weight + w <= drone_capacity) {
									Complexity::add(Complexity::braced_init + 5);
									total_sack_weight += w;
									res.emplace_back(curr_pos, 3, w, supply_value.at(s_idx));
									extra_supplies.push_back(s_idx);
								}
							}
							Complexity::add(1);
							s_idx = find(supplies, curr_pos, s_idx + 1);
						}
					}
				}
				Complexity::add(2);
			}
		}

		Complexity::add(1 + Complexity::for_outer);
		for (const std::size_t i : std::get<0>(sack)) {
			Complexity::add(Complexity::for_inner + 10 + Complexity::braced_init);
			const std::size_t s_idx = supplies_in_junction.at(i);
			supplies[s_idx]         = entry;
			supplies_in_junction.erase(supplies_in_junction.begin() + static_cast<long long>(i));
			std::size_t w = supply_weight.at(s_idx);
			total_weight  -= w;
			res.emplace_back(entry, 2, w, supply_value.at(s_idx));
		}
		for (const std::size_t s_idx : extra_supplies) {
			Complexity::add(Complexity::for_inner + 7 + Complexity::braced_init);
			supplies[s_idx] = entry;
			std::size_t w   = supply_weight.at(s_idx);
			total_weight    -= w;
			res.emplace_back(entry, 2, w, supply_value.at(s_idx));
		}
	}
	Complexity::pop_stack();
}

void clear_junction_path(
	const Facility_ADT&                                                              G,
	const Graph::VertexT                                                             entry,
	const Graph::VertexT                                                             curr,
	const std::vector<Graph::VertexT>&                                               backtrack,
	std::vector<Graph::VertexT>&                                                     supplies,
	const std::vector<std::size_t>&                                                  supply_weight,
	const std::vector<std::size_t>&                                                  supply_value,
	std::map<std::vector<Graph::VertexT>, std::unordered_set<size_t> >&              supply_path,
	const std::vector<Graph::VertexT>&                                               inter_wing_path,
	const std::size_t                                                                drone_capacity,
	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> >& res) {
	Complexity::push_stack("clear_junction_path");
	Complexity::add(1 + 1 + Complexity::if_);
	const Graph::VertexT junction_other = get_other_junction(G, curr);
	if (junction_other == curr) {
		Complexity::add(Complexity::return_);
		return;
	}

	Complexity::add(3);
	auto new_inter_wing_path = inter_wing_path;
	new_inter_wing_path.push_back(curr);
	new_inter_wing_path.push_back(junction_other);

	Complexity::add(1 + 1 + 2 + Complexity::for_outer);
	bool        worth_doing = false;
	std::size_t min_length  = new_inter_wing_path.size();
	for (const auto& k : supply_path | std::views::keys) {
		Complexity::add(2 + Complexity::if_);
		if (k.size() >= min_length) {
			Complexity::add(Complexity::for_inner + Complexity::for_outer + 2);
			worth_doing = true;
			for (std::size_t i = 0; i < min_length; ++i) {
				Complexity::add(Complexity::for_inner + Complexity::if_ + 3);
				if (k.at(i) != new_inter_wing_path.at(i)) {
					Complexity::add(1 + Complexity::break_);
					worth_doing = false;
					break;
				}
			}
		}
		Complexity::add(Complexity::if_);
		if (worth_doing) {
			Complexity::add(Complexity::break_);
			break;
		}
	}

	Complexity::add(Complexity::if_);
	if (worth_doing) {
		Complexity::add(6 + Complexity::braced_init + Complexity::for_outer);
		res.emplace_back(curr, 1, 0, 0);
		auto curr_backtrack = backtrack;
		curr_backtrack.push_back(junction_other);

		const Graph              wing = get_which_wing(G, junction_other);
		std::vector<std::size_t> surviving_supplies{};
		for (const Graph::VertexT n : wing.get_neighbours(junction_other) | std::views::keys) {
			Complexity::add(2 + Complexity::braced_init + Complexity::if_ + 2);
			std::vector new_branch_prevs = {junction_other};

			if (const auto branch_res = clear_branch(
					G,
					entry,
					junction_other,
					n,
					wing,
					new_branch_prevs,
					supplies,
					supply_weight,
					supply_value,
					supply_path,
					new_inter_wing_path,
					drone_capacity
				);
				!branch_res.empty()) {
				Complexity::add(1 + Complexity::braced_init + Complexity::for_outer);
				res.emplace_back(junction_other, 1, 0, 0);
				for (const auto& i : branch_res) {
					Complexity::add(2 + Complexity::for_inner);
					res.push_back(i);
				}

				Complexity::add(1 + 1 + Complexity::for_outer);
				std::vector<std::size_t> supplies_in_junction{};
				for (const std::size_t s_idx : supply_path.at(new_inter_wing_path)) {
					Complexity::add(Complexity::for_inner + 2 + Complexity::if_);
					if (supplies.at(s_idx) == junction_other) {
						Complexity::add(1);
						supplies_in_junction.push_back(s_idx);
					}
				}

				knapsack_supplies(
					supplies,
					supply_weight,
					supply_value,
					supplies_in_junction,
					drone_capacity,
					entry,
					curr_backtrack,
					res
				);

				Complexity::add(3 + Complexity::if_);
				if (const std::size_t supply_count = supplies_in_junction.size();
					supply_count != 0) {
					Complexity::add(1 + Complexity::for_outer);
					std::vector<std::size_t> storage{};
					for (const std::size_t s_idx : supplies_in_junction) {
						Complexity::add(Complexity::for_inner + 4 + Complexity::braced_init);
						storage.push_back(s_idx);
						res.emplace_back(junction_other, 3, supply_weight.at(s_idx), supply_value.at(s_idx));
					}

					Complexity::add(1 + Complexity::for_outer);
					std::unordered_set<Graph::VertexT> supplies_set{};
					supplies_set.reserve(supply_count);
					for (const Graph::VertexT s : supplies) {
						Complexity::add(Complexity::for_inner + 1);
						supplies_set.insert(s);
					}
					Complexity::add(4 + Complexity::while_outer + 3);

					std::size_t storage_len = storage.size();
					for (long long i = static_cast<long long>(backtrack.size()) - 1; i >= 0; --i) {
						Complexity::add(Complexity::while_inner + 3 + 3 + Complexity::if_);
						if (!supplies_set.contains(backtrack.at(i))) {
							Complexity::add(12 + Complexity::braced_init);
							std::size_t s_idx = storage.at(storage_len - 1);
							storage.pop_back();
							supplies[s_idx] = backtrack.at(i);
							res.emplace_back(backtrack.at(i), 2, supply_weight.at(s_idx), supply_value.at(s_idx));
							surviving_supplies.push_back(s_idx);
							if (--storage_len == 0) {
								break;
							}
						}
						Complexity::add(2);
					}

					Complexity::add(1 + Complexity::if_);
					if (storage_len != 0) {
						Complexity::add(2 + Complexity::while_outer + 1);
						Graph::VertexT curr_pos = backtrack.front();
						for (; storage_len != 0; --storage_len) {
							std::size_t s_idx = storage.at(storage_len - 1);
							supplies[s_idx]   = curr_pos;
							res.emplace_back(curr_pos, 2, supply_weight.at(s_idx), supply_value.at(s_idx));
						}
					}

					Complexity::add(Complexity::if_ + 1);
					if (supply_count >= 2) {
						Complexity::add(1 + Complexity::braced_init);
						res.emplace_back(curr, 1, 0, 0);
					}
				}
			}
		}

		knapsack_supplies(
			supplies,
			supply_weight,
			supply_value,
			surviving_supplies,
			drone_capacity,
			entry,
			backtrack,
			res
		);

		Complexity::add(Complexity::if_ + 1);
		if (supply_path.contains(new_inter_wing_path)) {
			Complexity::add(5);
			supply_path[inter_wing_path].insert_range(supply_path.at(new_inter_wing_path));
			supply_path.erase(new_inter_wing_path);
		}
	}
}

std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > clear_branch(
	const Facility_ADT&                                                 G,
	const Graph::VertexT                                                entry,
	const Graph::VertexT                                                orig,
	const Graph::VertexT                                                branch,
	const Graph&                                                        orig_wing,
	std::vector<Graph::VertexT>&                                        backtrack,
	std::vector<Graph::VertexT>&                                        supplies,
	const std::vector<std::size_t>&                                     supply_weight,
	const std::vector<std::size_t>&                                     supply_value,
	std::map<std::vector<Graph::VertexT>, std::unordered_set<size_t> >& supply_path,
	const std::vector<Graph::VertexT>&                                  inter_wing_path,
	const size_t                                                        drone_capacity) {
	Complexity::push_stack("clear_branch");
	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > res{};

	Complexity::add(4 + Complexity::get_neighbours(orig_wing.size()) + Complexity::while_outer + 2);
	Graph::VertexT branch_pos = branch;
	Graph::VertexT prev       = orig;
	backtrack.push_back(branch_pos);

	clear_junction_path(
		G,
		entry,
		branch_pos,
		backtrack,
		supplies,
		supply_weight,
		supply_value,
		supply_path,
		inter_wing_path,
		drone_capacity,
		res
	);
	auto neighbours = orig_wing.get_neighbour_vertices(branch_pos);
	while (neighbours.size() == 2) {
		Complexity::add(
			Complexity::while_inner + 2 + Complexity::if_ + 2 + 2 + 1 +
			Complexity::get_neighbours(orig_wing.size()) + 1
		);
		if (neighbours.front() == prev) {
			prev       = branch_pos;
			branch_pos = neighbours.back();
		} else {
			prev       = branch_pos;
			branch_pos = neighbours.front();
		}
		neighbours = orig_wing.get_neighbour_vertices(branch_pos);
		backtrack.push_back(branch_pos);

		clear_junction_path(
			G,
			entry,
			branch_pos,
			backtrack,
			supplies,
			supply_weight,
			supply_value,
			supply_path,
			inter_wing_path,
			drone_capacity,
			res
		);
	}

	Complexity::add(2 + Complexity::if_ + 1);
	if (const auto branch_degree = neighbours.size();
		branch_degree >= 3) {
		Complexity::add(Complexity::for_outer);
		for (const Graph::VertexT n : neighbours) {
			Complexity::add(Complexity::for_inner + Complexity::if_ + 1);
			if (n != prev) {
				Complexity::add(1 + Complexity::for_outer);
				Complexity::add(backtrack.size() * (Complexity::for_inner + 1));
				auto       new_backtrack(backtrack);
				const auto branch_res = clear_branch(
					G,
					entry,
					branch_pos,
					n,
					orig_wing,
					new_backtrack,
					supplies,
					supply_weight,
					supply_value,
					supply_path,
					inter_wing_path,
					drone_capacity
				);
				Complexity::add(
					Complexity::for_outer + branch_res.size() * (
						Complexity::for_inner + 1)
				);
				res.append_range(branch_res);
			}
		}
	}

	std::vector<std::size_t> supply_to_collect{};
	Complexity::add(Complexity::if_ + 1);
	if (supply_path.contains(inter_wing_path)) {
		Complexity::add(1 + Complexity::for_outer + backtrack.size() * (Complexity::for_inner + 1)); {
			const auto backtrack_set = backtrack | std::ranges::to<std::set>();

			Complexity::add(1 + Complexity::for_outer + 1);
			for (std::size_t s_idx = 0; s_idx < supplies.size(); ++s_idx) {
				Complexity::add(Complexity::for_inner + Complexity::if_ + 8);
				if (supplies.at(s_idx) != entry && backtrack_set.contains(supplies.at(s_idx)) && supply_path.at(
					    inter_wing_path
				    ).contains(s_idx)) {
					Complexity::add(1);
					supply_to_collect.push_back(s_idx);
				}
			}
		}
	}

	knapsack_supplies(supplies, supply_weight, supply_value, supply_to_collect, drone_capacity, entry, backtrack, res);

	Complexity::add(2 + Complexity::for_outer);

	std::vector<std::size_t>                                      storage{};
	std::unordered_map<Graph::VertexT, std::vector<std::size_t> > vertex_to_collect{};
	for (const std::size_t s_idx : supply_to_collect) {
		Complexity::add(Complexity::for_inner + 2 + Complexity::if_ + 1);
		if (Graph::VertexT v = supplies.at(s_idx);
			vertex_to_collect.contains(v)) {
			Complexity::add(2);
			vertex_to_collect[v].push_back(s_idx);
		} else {
			Complexity::add(1 + Complexity::braced_init);
			vertex_to_collect[v] = {s_idx};
		}
	}

	Complexity::add(3 + Complexity::if_ + 1);
	Graph::VertexT curr_pos;
	if (auto res_len = static_cast<long long>(res.size()) - 1;
		res_len != -1) {
		Complexity::add(2 + Complexity::if_ + 5);
		auto res_last = res.at(res_len);
		if (std::get<0>(res_last) != entry && std::get<1>(res_last) == 2) {
			Complexity::add(3 + Complexity::if_ + 3);
			curr_pos = std::get<0>(res.at(res_len - 1));

			if (curr_pos != branch_pos && curr_pos != entry) {
				Complexity::add(Complexity::while_outer + 3);
				while (std::get<0>(res_last) == curr_pos) {
					Complexity::add(Complexity::while_inner + 1 + 2 + 2 + Complexity::while_outer + 2);
					res.pop_back();
					--res_len;

					auto& candidates = vertex_to_collect.at(curr_pos);
					for (auto k = static_cast<long long>(candidates.size()) - 1; k >= 0; --k) {
						Complexity::add(Complexity::while_inner + 1 + Complexity::if_ + 7 + 2);
						if (const std::size_t s_idx = candidates.at(k);
							supply_weight.at(s_idx) == std::get<2>(res_last) &&
							supply_value.at(s_idx) == std::get<3>(res_last)) {
							Complexity::add(2 + Complexity::break_);
							storage.push_back(s_idx);
							candidates.erase(candidates.begin() + k);
							break;
						}
					}
					Complexity::add(2);
					res_last = res.at(res_len);
				}

				Complexity::add(Complexity::while_outer + 1);
				while (res_len >= 0) {
					Complexity::add(Complexity::while_inner + 1 + 2 + Complexity::if_);
					if (std::get<1>(res_last) == 3) {
						Complexity::add(Complexity::break_);
						break;
					}
					Complexity::add(2 + Complexity::if_);
					if (std::get<1>(res_last) == 2) {
						Complexity::add(4 + 2 + Complexity::for_outer);
						auto& candidates = vertex_to_collect.at(std::get<0>(res_last));
						res.pop_back();
						--res_len;

						for (auto k = static_cast<long long>(candidates.size()) - 1; k >= 0; --k) {
							Complexity::add(Complexity::while_inner + 1 + Complexity::if_ + 7 + 2);
							if (const std::size_t s_idx = candidates.at(k);
								supply_weight.at(s_idx) == std::get<2>(res_last) && supply_value.at(s_idx) ==
								std::get<
									3>(res_last)) {
								Complexity::add(2 + Complexity::break_);
								storage.push_back(s_idx);
								candidates.erase(candidates.begin() + k);
								break;
							}
						}
					}
					Complexity::add(2);
					res_last = res.at(res_len);
				}
			}
		}
	}

	Complexity::add(2 + Complexity::while_outer + 1);
	auto i = static_cast<long long>(backtrack.size()) - 1;
	while (i >= 0) {
		Complexity::add(Complexity::while_inner + 1 + 3 + Complexity::if_);
		curr_pos = backtrack.at(i);
		if (curr_pos == orig) {
			Complexity::add(Complexity::break_);
			break;
		}

		Complexity::add(Complexity::if_ + 1);
		if (vertex_to_collect.contains(curr_pos)) {
			Complexity::add(4 + Complexity::while_outer + 1);
			auto& curr_pos_supplies = vertex_to_collect.at(curr_pos);
			for (auto j = static_cast<long long>(curr_pos_supplies.size() - 1); j >= 0; --j) {
				Complexity::add(Complexity::while_inner + Complexity::if_ + 2);
				if (find(storage, curr_pos_supplies.at(j), 0) == -1) {
					Complexity::add(7 + Complexity::braced_init);
					std::size_t s_idx = curr_pos_supplies.at(j);
					curr_pos_supplies.erase(curr_pos_supplies.begin() + j);
					storage.push_back(s_idx);
					res.emplace_back(curr_pos, 3, supply_weight.at(s_idx), supply_value.at(s_idx));
				}
				Complexity::add(2);
			}
		}
		Complexity::add(2);
		--i;
	}

	Complexity::add(1 + Complexity::for_outer);
	std::unordered_set<Graph::VertexT> supplies_set{};
	supplies_set.reserve(supplies.size());
	for (const Graph::VertexT s : supplies) {
		Complexity::add(Complexity::for_inner + 1);
		supplies_set.insert(s);
	}

	Complexity::add(2 + Complexity::while_outer + 3);
	std::size_t storage_len = storage.size();
	if (storage_len != 0) {
		while (i >= 0) {
			Complexity::add(Complexity::while_inner + 3 + 3 + 2 + Complexity::if_);
			curr_pos = backtrack.at(i);
			if (!supplies_set.contains(curr_pos)) {
				Complexity::add(11 + Complexity::braced_init);
				std::size_t s_idx = storage.at(storage_len - 1);
				storage.pop_back();
				supplies[s_idx] = backtrack.at(i);
				res.emplace_back(backtrack.at(i), 2, supply_weight.at(s_idx), supply_value.at(s_idx));
				if (--storage_len == 0) {
					break;
				}
			}
			Complexity::add(2);
			--i;
		}
	}

	Complexity::add(1 + Complexity::if_);
	if (storage_len != 0) {
		Complexity::add(2 + Complexity::while_outer + 1);
		Graph::VertexT curr_backtrack = backtrack.front();
		for (; storage_len != 0; --storage_len) {
			std::size_t s_idx = storage[storage_len - 1];
			supplies[s_idx]   = curr_backtrack;
			res.emplace_back(curr_backtrack, 2, supply_weight.at(s_idx), supply_value.at(s_idx));
		}
	}

	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	Complexity::pop_stack();
	return res;
}

std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > ember_rescue(
	const Facility_ADT&                                    G,
	Graph::VertexT                                         entry,
	const std::unordered_set<Graph::VertexT>&              exits,
	std::unordered_set<Graph::VertexT>                     supplies,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_weight,
	const std::unordered_map<Graph::VertexT, std::size_t>& supply_value,
	const std::size_t                                      budget,
	const std::size_t                                      drone_capacity,
	const std::unordered_map<Graph::VertexT, SupplyID>&    vertex_to_supply_id,
	const std::unordered_set<SupplyID>&                    found_supply_ids
) {
	Complexity::push_stack("ember_rescue");
	Complexity::add(1);
	supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids);

	Complexity::add(3 + Complexity::for_outer);
	const Graph                                                      flat_G     = flatten_graph(G);
	auto                                                             entry_prev = dijkstra(flat_G, entry);
	std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > entry_path{};
	for (const Graph::VertexT v : supplies) {
		Complexity::add(Complexity::for_inner + 1);
		entry_path[v] = reconstruct_path(entry_prev, v);
	}

	Complexity::add(2 + Complexity::for_outer);
	std::vector<Graph::VertexT> exit_run{};
	std::size_t                 exit_run_cost = std::numeric_limits<std::size_t>::max();
	for (const Graph::VertexT e : exits) {
		Complexity::add(Complexity::for_inner + 2 + Complexity::if_ + 3);
		const auto curr = reconstruct_path(entry_prev, e);
		if (const Graph::WeightT curr_cost = get_path_length(flat_G, curr);
			curr_cost < exit_run_cost) {
			Complexity::add(2);
			exit_run      = curr;
			exit_run_cost = curr_cost;
		}
	}

	Complexity::add(2);
	auto reduced_supplies = get_reduced_supplies(
		flat_G,
		supplies,
		supply_weight,
		supply_value,
		entry_path,
		budget - exit_run_cost,
		drone_capacity
	);
	Complexity::add(Complexity::for_outer);

	Complexity::add(1);
	const std::map<std::vector<Graph::VertexT>, std::unordered_set<std::size_t> > supply_wing_paths =
			get_supply_wing_paths(G, reduced_supplies, entry_path);

	Complexity::add(3 + Complexity::for_outer);
	const Graph              entry_wing = get_which_wing(G, entry);
	std::vector<std::size_t> supply_weight_ordered{};
	supply_weight_ordered.reserve(reduced_supplies.size());
	std::vector<std::size_t> supply_value_ordered{};
	supply_weight_ordered.reserve(supply_value_ordered.size());
	for (const Graph::VertexT s : reduced_supplies) {
		Complexity::add(Complexity::for_inner + 4);
		supply_weight_ordered.push_back(supply_weight.at(s));
		supply_value_ordered.push_back(supply_value.at(s));
	}

	Complexity::add(2 + Complexity::get_neighbours(flat_G.size()) + Complexity::for_outer);
	std::vector<std::tuple<Graph::VertexT, std::size_t, std::size_t, std::size_t> > res{};
	Graph::VertexT                                                                  prev_pos = entry;
	for (const Graph::VertexT n : flat_G.get_neighbours(entry) | std::views::keys) {
		Complexity::add(Complexity::for_inner + 2 + 3 * Complexity::braced_init);
		std::vector backtrack              = {entry};
		auto        curr_supply_wing_paths = supply_wing_paths;
		const auto  curr_plan              = clear_branch(
			G,
			entry,
			entry,
			n,
			entry_wing,
			backtrack,
			reduced_supplies,
			supply_weight_ordered,
			supply_value_ordered,
			curr_supply_wing_paths,
			{},
			drone_capacity
		);
		for (const auto& i : curr_plan) {
			Complexity::add(Complexity::for_inner + 3 + Complexity::if_);
			if (Graph::VertexT curr_pos = std::get<0>(i);
				curr_pos != prev_pos) {
				Complexity::add(Complexity::for_outer);
				for (const Graph::VertexT v : reconstruct_path_to(entry_prev, prev_pos, curr_pos)) {
					Complexity::add(Complexity::for_inner + 1 + Complexity::braced_init);
					res.emplace_back(v, 1, 0, 0);
				}
				Complexity::add(1);
				prev_pos = curr_pos;
			}
			Complexity::add(1 + 1 + Complexity::braced_init);
			res.push_back(i);
		}
	}

	Complexity::add(Complexity::if_ + 1);
	if (prev_pos != entry) {
		Complexity::add(Complexity::for_outer);
		for (const Graph::VertexT v : reconstruct_path_to(entry_prev, prev_pos, entry)) {
			Complexity::add(Complexity::for_inner + 1 + Complexity::braced_init);
			res.emplace_back(v, 1, 0, 0);
		}
	}

	Complexity::add(Complexity::for_outer);
	for (const Graph::VertexT v : exit_run) {
		Complexity::add(Complexity::for_inner + 1 + Complexity::braced_init);
		res.emplace_back(v, 1, 0, 0);
	}

	Complexity::add(Complexity::return_);
	Complexity::pop_stack();
	return res;
}
