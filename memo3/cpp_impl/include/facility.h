#pragma once
#include <random>
#include <vector>

#include "graph.h"

class Facility {
public:
	struct pair_hash {
		std::size_t operator()(const std::pair<Graph::VertexT, Graph::VertexT>& v) const {
			return v.first * 31 + v.second;
		}
	};
	static constexpr Graph::VertexT WING_COLS = 10;
	static constexpr Graph::VertexT WING_ROWS = 10;

	std::vector<Graph> wings;
	std::unordered_set<std::pair<Graph::VertexT, Graph::VertexT>, pair_hash> junctions;
	std::unordered_set<Graph::VertexT> exits;
	std::unordered_set<Graph::VertexT> supplies;
	const Graph::VertexT entry{0};

	Facility(int seed, std::size_t wing_count, std::size_t exit_count, std::size_t supply_count);

private:
	std::default_random_engine rng;

	void carve(Graph& g, Graph::VertexT u, std::unordered_set<Graph::VertexT>& visited);

	Graph build_wing(uint16_t columns, uint16_t rows, Graph::VertexT vertex_prefix);
};
