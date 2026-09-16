#pragma once
#include <array>
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

	static constexpr Graph::VertexT WING_COLS    = 10;
	static constexpr Graph::VertexT WING_ROWS    = 10;
	static constexpr std::size_t    SUPPLY_COUNT = 50;
	static constexpr std::size_t    CAPACITY     = 5;

	std::vector<Graph>                                                                                    wings;
	Graph                                                                                                 flat_graph;
	std::unordered_set<std::pair<Graph::VertexT, Graph::VertexT>, pair_hash>                              junctions;
	std::unordered_set<Graph::VertexT>                                                                    exits;
	std::unordered_set<Graph::VertexT>                                                                    supplies;
	std::unordered_map<Graph::VertexT, std::size_t>                                                       weight;
	std::unordered_map<Graph::VertexT, std::size_t>                                                       value;
	std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::size_t> >                  dist;
	std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > > path;
	const Graph::VertexT                                                                                  entry{0};
	std::size_t                                                                                           full_budget;

	explicit Facility(int seed);

	static Graph::VertexT get_vertex(std::size_t wing, std::size_t col, std::size_t row);

	static std::array<Graph::VertexT, 3> get_vertex_tuple(const Graph::VertexT v);

private:
	std::default_random_engine rng;

	void carve(Graph& g, Graph::VertexT u, std::unordered_set<Graph::VertexT>& visited);

	Graph build_wing(uint16_t columns, uint16_t rows, Graph::VertexT vertex_prefix);

	std::size_t trip_cost(const std::vector<Graph::VertexT>& trip);

	std::size_t exit_leg();

	std::size_t plan_cost(const std::vector<std::vector<Graph::VertexT> >& plan);

	std::vector<Graph::VertexT> best_order(const std::vector<Graph::VertexT>& units);

	std::vector<std::vector<Graph::VertexT> > exemplar_a_nearest_fill(
		const std::vector<Graph::VertexT>& pool,
		std::size_t                        budget);

	void set_budget();
};