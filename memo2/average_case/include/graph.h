#pragma once
#include <unordered_map>
#include <unordered_set>

class Graph {
public:
	using VertexT = uint32_t;
	using WeightT = int;

	Graph() = default;

	~Graph() = default;

	void add_vertex(VertexT v);

	void remove_vertex(VertexT v);

	void add_edge(VertexT u, VertexT v, WeightT w);

	void set_edge_weight(VertexT u, VertexT v, WeightT w);

	[[nodiscard]] bool contains(VertexT v) const;

	[[nodiscard]] VertexT get_a_vertex() const;

	[[nodiscard]] WeightT get_edge_weight(VertexT u, VertexT v) const;

	[[nodiscard]] std::unordered_map<VertexT, int> get_neighbors(VertexT u) const;

	[[nodiscard]] std::size_t get_degree(VertexT u) const;

	[[nodiscard]] std::size_t size() const;

	[[nodiscard]] std::vector<VertexT> get_vertices() const;

	[[nodiscard]] std::vector<std::tuple<VertexT, VertexT, WeightT>> get_edges() const;

	void update();

private:
	std::unordered_map<VertexT, std::unordered_map<VertexT, int> > adj;
	std::unordered_set<VertexT> inactive;
};
