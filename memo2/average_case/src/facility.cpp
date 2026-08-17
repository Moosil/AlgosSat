#include "facility.h"

#include <numeric>
#include <print>
#include <ranges>

Facility::Facility(const int seed, const std::size_t wing_count, const std::size_t exit_count,
                   const std::size_t supply_count
) : rng(seed) {
	for (Graph::VertexT i = 0; i < wing_count; ++i) {
		wings.push_back(build_wing(WING_COLS, WING_ROWS, i));
	}

	Graph::VertexT no_supply_wing = 3;
	{
		std::uniform_int_distribution<Graph::VertexT> dist01(0, 1);
		std::uniform_int_distribution<Graph::VertexT> dist_wings(0, static_cast<Graph::VertexT>(wing_count) - 1);
		while (exits.size() < exit_count) {
			const Graph::VertexT wing = dist_wings(rng);
			const Graph::VertexT lr = dist01(rng);
			const Graph::VertexT tb = dist01(rng);
			if (const Graph::VertexT candidate = lr * (WING_COLS - 1) * WING_ROWS + tb * (WING_COLS - 1) | (wing << 16);
				!exits.contains(candidate) && candidate != entry) {
				exits.insert(candidate);
			}
		}
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
		Graph::VertexT u1 = r1 + (WING_COLS - 1) * WING_ROWS | (i << 16);
		Graph::VertexT u2 = r1 | ((i + 1) << 16);
		Graph::VertexT v1 = r2 + (WING_COLS - 1) * WING_ROWS | (i << 16);
		Graph::VertexT v2 = r2 | ((i + 1) << 16);
		junctions.emplace(u1, u2);
		junctions.emplace(v1, v2);

		junctions_flat.insert(u1);
		junctions_flat.insert(u2);
		junctions_flat.insert(v1);
		junctions_flat.insert(v2);
	}

	std::vector<std::vector<Graph::VertexT> > wing_deadends(wing_count);
	for (std::size_t i = 0; i < wing_count; ++i) {
		for (const auto& v : wings[i].get_vertices()) {
			if (wings[i].get_degree(v) == 1 && v != entry && !exits.contains(v) && !junctions_flat.contains(v)) {
				wing_deadends[i].push_back(v);
			}
		}
		std::ranges::shuffle(wing_deadends, rng);
	}

	while (supplies.size() < supply_count) {
		bool can_add = false;
		for (std::size_t i = 0; i < wings.size(); ++i) {
			if (i == no_supply_wing) {
				continue;
			}
			if (supplies.size() >= supply_count) {
				break;
			}
			for (const auto& v : wing_deadends[i]) {
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

	if (wing_count >= 2) {
		for (const auto& [u, v, _] : wings[1].get_edges()) {
			Graph::VertexT u_low = static_cast<uint16_t>(u);
			Graph::VertexT v_low = static_cast<uint16_t>(v);
			std::size_t u_col = u_low / WING_ROWS;
			std::size_t v_col = v_low / WING_ROWS;
			wings[1].set_edge_weight(u, v, 1 + static_cast<Graph::WeightT>(std::max(u_col, v_col)) / 3);
		}
		if (wing_count >= 3) {
			std::uniform_int_distribution<Graph::WeightT> dist_weight(1, 5);
			for (std::size_t i = 2; i < wing_count; ++i) {
				for (auto& wing = wings[i]; const auto& [u, v, _] : wing.get_edges()) {
					wing.set_edge_weight(u, v, dist_weight(rng));
				}
			}
		}
	}

	for (auto& wing : wings) {
		for (const auto u : wing.get_vertices()) {
			if (wing.get_degree(u) == 2 && u != entry && !supplies.contains(u) && !exits.contains(u) && !junctions_flat.
			    contains(u)) {
				auto n = wing.get_neighbors(u);
				auto n_keys = n | std::views::keys | std::ranges::to<std::vector>();
				auto n1 = n_keys.front();
				auto n2 = n_keys.back();
				auto w = n[n1] + n[n2];
				wing.remove_vertex(u);
				wing.add_edge(n1, n2, w);
			}
		}
		wing.update();
	}
}

void Facility::carve(Graph& g, const Graph::VertexT u, std::unordered_set<Graph::VertexT>& visited) {
	visited.insert(u);
	Graph::VertexT u_low = static_cast<uint16_t>(u);
	std::vector<Graph::VertexT> neighbours;
	Graph::VertexT row = u_low % WING_ROWS;
	Graph::VertexT col = u_low / WING_ROWS;
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
	Graph res;
	Graph::VertexT vertex_prefix_shifted = vertex_prefix << 16;
	for (uint16_t i = 0; i < columns; ++i) {
		for (uint16_t j = 0; j < rows; ++j) {
			res.add_vertex(i * rows + j | vertex_prefix_shifted);
		}
	}

	carve(res, vertex_prefix_shifted, visited);
	return res;
}
