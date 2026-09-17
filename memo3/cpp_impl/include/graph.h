#pragma once
#include <unordered_map>
#include <unordered_set>

class Graph {
public:
	using VertexT = uint32_t;
	using WeightT = std::size_t;

	Graph() = default;

	~Graph() = default;

	void add_vertex(VertexT v);

	void remove_vertex(VertexT v);

	void add_edge(VertexT u, VertexT v, WeightT w);

	void set_edge_weight(VertexT u, VertexT v, WeightT w);

	[[nodiscard]] bool contains(VertexT v) const;

	[[nodiscard]] VertexT get_a_vertex() const;

	[[nodiscard]] WeightT get_edge_weight(VertexT u, VertexT v) const;

	[[nodiscard]] std::vector<VertexT> get_neighbour_vertices(VertexT u) const;

	[[nodiscard]] std::unordered_map<VertexT, WeightT> get_neighbours(VertexT u) const;

	[[nodiscard]] std::size_t get_degree(VertexT u) const;

	[[nodiscard]] std::size_t size() const;

	[[nodiscard]] std::vector<VertexT> get_vertices() const;

	[[nodiscard]] std::vector<std::tuple<VertexT, VertexT, WeightT> > get_edges() const;

	[[nodiscard]] std::unordered_map<VertexT, std::vector<VertexT> > sssp(VertexT source) const;

	[[nodiscard]] std::unordered_map<VertexT, std::size_t> sssp_dist(VertexT source) const;

	[[nodiscard]] std::unordered_map<VertexT, std::size_t> sssp_dist(
		VertexT                                                   source,
		const std::unordered_map<VertexT, std::vector<VertexT> >& paths) const;

	void update();

private:
	std::unordered_map<VertexT, std::unordered_map<VertexT, WeightT> > adj;
	std::unordered_set<VertexT>                                        inactive;

	static std::vector<VertexT> reconstruct_path(const std::unordered_map<VertexT, VertexT>& prev, VertexT sink);
};