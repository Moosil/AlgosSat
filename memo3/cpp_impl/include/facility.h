#pragma once
#include <array>
#include <random>
#include <set>
#include <vector>

#include "graph.h"

class Facility {
public:
	static constexpr Graph::VertexT WING_COLS = 10;
	static constexpr Graph::VertexT WING_ROWS = 10;

	std::vector<Graph> wings;
	Graph flat_graph;
	std::set<std::pair<Graph::VertexT, Graph::VertexT> > junctions;
	std::unordered_set<Graph::VertexT> exits;
	std::unordered_set<Graph::VertexT> supplies;
	std::unordered_map<Graph::VertexT, std::size_t> weight;
	std::unordered_map<Graph::VertexT, std::size_t> value;
	std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::size_t> > dist;
	std::unordered_map<Graph::VertexT, std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > > path;
	const Graph::VertexT entry{0};
	std::size_t full_budget{};
	std::size_t drone_capacity;

	Facility(
		int         seed,
		std::size_t wing_count,
		std::size_t supply_count,
		std::size_t exit_count,
		std::size_t drone_capacity);

	void print() const;

	[[nodiscard]] std::tuple<std::vector<Graph::VertexT>, std::vector<size_t>, std::vector<std::unordered_set<
		Graph::VertexT> > > get_plan_data(
		const std::vector<std::tuple<Graph::VertexT, size_t, size_t, size_t> >& plan) const;

	static Graph::VertexT get_vertex(std::size_t wing, std::size_t col, std::size_t row);

	static std::array<Graph::VertexT, 3> get_vertex_tuple(Graph::VertexT v);

	void set_budget();

private:
	std::default_random_engine rng;

	void carve(Graph& g, Graph::VertexT u, std::unordered_set<Graph::VertexT>& visited);

	Graph build_wing(uint16_t columns, uint16_t rows, Graph::VertexT vertex_prefix);

	std::size_t trip_cost(const std::vector<Graph::VertexT>& trip);

	std::size_t exit_leg();

	std::size_t plan_cost(const std::vector<std::vector<Graph::VertexT> >& plan);

	std::vector<Graph::VertexT> best_order(const std::vector<Graph::VertexT>& units);

	std::vector<std::vector<Graph::VertexT> > exemplar_a_nearest_fill(
		const std::vector<Graph::VertexT>& pool);
};