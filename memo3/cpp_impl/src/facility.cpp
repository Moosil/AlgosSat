#include "facility.h"

#include <assert.h>
#include <numeric>
#include <print>
#include <ranges>

Facility::Facility(const int seed):
	flat_graph{},
	rng(seed) {
	std::size_t wing_count = 2 + (seed % 3);
	for (Graph::VertexT i = 0; i < wing_count; ++i) {
		wings.push_back(build_wing(WING_COLS, WING_ROWS, i));
	}

	Graph::VertexT no_supply_wing = 3; {
		std::uniform_int_distribution<Graph::VertexT> dist_wings(0, static_cast<Graph::VertexT>(wing_count) - 1);
		if (wing_count >= 3) {
			no_supply_wing = dist_wings(rng);
		}
	}

	std::unordered_set<Graph::VertexT> junctions_flat;
	for (Graph::VertexT i = 0; i < wing_count - 1; ++i) {
		std::vector<Graph::VertexT> rows(WING_ROWS - 4);
		std::iota(rows.begin(), rows.end(), 2);
		std::ranges::shuffle(rows, rng);
		Graph::VertexT r1 = rows[0];
		Graph::VertexT r2 = rows[1];
		Graph::VertexT u1 = get_vertex(i, WING_COLS - 1, r1);
		Graph::VertexT u2 = get_vertex(i + 1, 0, r1);
		Graph::VertexT v1 = get_vertex(i, WING_COLS - 1, r2);
		Graph::VertexT v2 = get_vertex(i, 0, r2);
		junctions.emplace(u1, u2);
		junctions.emplace(v1, v2);

		junctions_flat.insert(u1);
		junctions_flat.insert(u2);
		junctions_flat.insert(v1);
		junctions_flat.insert(v2);
	}

	exits.insert(get_vertex(wing_count - 1, WING_COLS - 1, WING_ROWS - 1));
	exits.insert(get_vertex(wing_count - 1, WING_COLS - 1, 0));

	std::vector<std::vector<Graph::VertexT> > tier_1(wing_count);
	std::vector<std::vector<Graph::VertexT> > tier_2(wing_count);
	for (std::size_t i = 0; i < wing_count; ++i) {
		for (const auto& v : wings[i].get_vertices()) {
			if (v != entry && !exits.contains(v) && !junctions_flat.contains(v)) {
				if (std::size_t degree = wings[i].get_degree(v);
					degree == 1) {
					tier_1[i].push_back(v);
				} else if (degree == 2) {
					tier_2[i].push_back(v);
				}
			}
		}
		std::ranges::shuffle(tier_1[i], rng);
		std::ranges::shuffle(tier_2[i], rng);
	}

	for (const auto& tier : {tier_1, tier_2}) {
		while (supplies.size() < SUPPLY_COUNT) {
			bool can_add = false;
			for (std::size_t i = 0; i < wings.size(); ++i) {
				if (i == no_supply_wing) {
					continue;
				}
				if (supplies.size() >= SUPPLY_COUNT) {
					break;
				}
				for (const auto& v : tier[i]) {
					if (!supplies.contains(v)) {
						supplies.insert(v);
						can_add = true;
						break;
					}
				}
			}
			if (!can_add) {
				break;
			}
		}
	}
	assert(supplies.size() == SUPPLY_COUNT);

	for (const auto& [u, v, _] : wings[1].get_edges()) {
		Graph::VertexT u_low = static_cast<uint16_t>(u);
		Graph::VertexT v_low = static_cast<uint16_t>(v);
		std::size_t    u_col = u_low / WING_ROWS;
		std::size_t    v_col = v_low / WING_ROWS;
		wings[1].set_edge_weight(u, v, 1 + static_cast<Graph::WeightT>(std::max(u_col, v_col)) / 3);
	}
	if (wing_count >= 3) {
		std::uniform_int_distribution<Graph::WeightT> dist_weight(1, 5);
		for (std::size_t i = 2; i < wing_count; ++i) {
			for (auto&       wing = wings[i];
			     const auto& [u, v, _] : wing.get_edges()) {
				wing.set_edge_weight(u, v, dist_weight(rng));
			}
		}
	}

	for (const auto& wing : wings) {
		for (const auto& u : wing.get_vertices()) {
			flat_graph.add_vertex(u);
		}
		for (const auto& [u, v, w] : wing.get_edges()) {
			flat_graph.add_edge(u, v, w);
		}
	}
	for (const auto& [u, v] : junctions) {
		flat_graph.add_edge(u, v, 1);
	} {
		std::uniform_int_distribution<std::size_t> dist_weight(1, 3);
		std::uniform_int_distribution<std::size_t> dist_value(1, 5);
		for (const auto& s : supplies) {
			weight[s] = dist_weight(rng);
			value[s]  = dist_value(rng);
		}

		for (const auto& v : supplies) {
			path[v] = flat_graph.sssp(v);
			dist[v] = flat_graph.sssp_dist(v, path[v]);
		}
	}

	set_budget();
}

Graph::VertexT Facility::get_vertex(const std::size_t wing, const std::size_t col, const std::size_t row) {
	return row + col * WING_ROWS | (wing << 16);
}

std::array<Graph::VertexT, 3> Facility::get_vertex_tuple(const Graph::VertexT v) {
	const auto low = static_cast<uint16_t>(v);
	return {v >> 16, low / WING_COLS, low % WING_COLS};
}

void Facility::carve(Graph& g, const Graph::VertexT u, std::unordered_set<Graph::VertexT>& visited) {
	visited.insert(u);
	Graph::VertexT              u_low = static_cast<uint16_t>(u);
	std::vector<Graph::VertexT> neighbours;
	Graph::VertexT              row = u_low % WING_ROWS;
	Graph::VertexT              col = u_low / WING_ROWS;
	if (row != 0) {
		neighbours.push_back(u - 1);
	}
	if (row != WING_ROWS - 1) {
		neighbours.push_back(u + 1);
	}
	if (col != 0) {
		neighbours.push_back(u - WING_ROWS);
	}
	if (col != WING_COLS - 1) {
		neighbours.push_back(u + WING_ROWS);
	}
	std::ranges::shuffle(neighbours, rng);
	for (const auto& v : neighbours) {
		if (!visited.contains(v)) {
			g.add_edge(u, v, 1);
			carve(g, v, visited);
		}
	}
}

Graph Facility::build_wing(const uint16_t columns, const uint16_t rows, const Graph::VertexT vertex_prefix) {
	std::unordered_set<Graph::VertexT> visited;
	Graph                              res;
	Graph::VertexT                     vertex_prefix_shifted = vertex_prefix << 16;
	for (uint16_t i = 0; i < columns; ++i) {
		for (uint16_t j = 0; j < rows; ++j) {
			res.add_vertex(i * rows + j | vertex_prefix_shifted);
		}
	}

	carve(res, vertex_prefix_shifted, visited);
	return res;
}

std::size_t Facility::trip_cost(const std::vector<Graph::VertexT>& trip) {
	std::size_t    res  = 0;
	std::size_t    load = 0;
	Graph::VertexT prev = entry;
	for (const auto& v : trip) {
		res  += (1 + load) * dist[prev][v];
		load += weight[v];
		prev = v;
	}
	res += (1 + load) * dist[prev][entry];
	return res;
}

std::size_t Facility::exit_leg() {
	std::size_t res = -1;
	for (const auto& v : exits) {
		if (const std::size_t curr = dist[entry][v];
			res == -1 || curr < res) {
			res = curr;
		}
	}
	return res;
}

std::size_t Facility::plan_cost(const std::vector<std::vector<Graph::VertexT> >& plan) {
	std::size_t res = 0;
	for (const auto& t : plan) {
		res += trip_cost(t);
	}
	return res + exit_leg();
}

std::vector<Graph::VertexT> Facility::best_order(const std::vector<Graph::VertexT>& units) {
	if (units.size() <= 1) {
		return units;
	}

	std::size_t                 min_cost = -1;
	std::vector<Graph::VertexT> best;
	for (std::size_t i = 0; i < units.size(); ++i) {
		std::vector                 curr     = {units[i]};
		std::vector<Graph::VertexT> instance = units;
		instance.erase(instance.begin() + static_cast<std::vector<Graph::VertexT>::difference_type>(i));
		curr.append_range(best_order(instance));
		if (const std::size_t curr_cost = trip_cost(curr);
			curr_cost < min_cost) {
			min_cost = curr_cost;
			best     = curr;
		}
	}
	return best;
}

std::vector<std::vector<Graph::VertexT> > Facility::exemplar_a_nearest_fill(
	const std::vector<Graph::VertexT>& pool,
	std::size_t                        budget) {
	auto                                      remaining = pool;
	std::vector<std::vector<Graph::VertexT> > plan{};
	std::size_t                               spent         = 0;
	const std::size_t                         exit_leg_cost = exit_leg();

	while (!remaining.empty()) {
		std::vector<Graph::VertexT> trip{};
		Graph::VertexT              prev = entry;
		std::size_t                 load = 0;
		while (true) {
			Graph::VertexT* to_add   = nullptr;
			std::size_t     min_dist = -1;
			for (auto& v : remaining) {
				if (std::ranges::contains(trip, v) && load + weight[v] <= CAPACITY) {
					if (!to_add || dist[prev][v] < min_dist) {
						min_dist = dist[prev][v];
						to_add   = &v;
					}
				}
			}
			if (!to_add) {
				break;
			}
			trip.push_back(*to_add);
			load += weight[*to_add];
			prev = *to_add;
		}
		if (trip.empty()) {
			break;
		}
		trip                   = best_order(trip);
		const std::size_t cost = trip_cost(trip);
		if (spent + cost + exit_leg_cost > budget) {
			break;
		}
		spent += cost;
		plan.push_back(trip);
		for (const auto& v : trip) {
			remaining.erase(std::ranges::find(remaining, v));
		}
	}
	return plan;
}

void Facility::set_budget() {
	const auto full_plan = exemplar_a_nearest_fill(
		supplies | std::ranges::to<std::vector>(),
		std::numeric_limits<std::size_t>::max()
	);
	const auto full_extraction_cost = plan_cost(full_plan);
	full_budget                     = full_extraction_cost;
}