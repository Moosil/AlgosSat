#include "graph.h"

#include <ranges>
#include <stdexcept>

void Graph::add_vertex(const VertexT v) {
	adj[v] = {};
}

void Graph::remove_vertex(const VertexT v) {
	inactive.insert(v);
}

void Graph::add_edge(const VertexT u, const VertexT v, const WeightT w) {
	adj[u][v] = w;
	adj[v][u] = w;
}

bool Graph::contains(const VertexT v) const {
	return adj.contains(v) && !inactive.contains(v);
}

Graph::VertexT Graph::get_a_vertex() const {
	if (adj.empty()) {
		throw std::runtime_error("Graph is empty, get_a_vertex() requires graph is not empty.");
	}
	return adj.begin()->first;
}

Graph::WeightT Graph::get_edge_weight(const VertexT u, const VertexT v) const {
	return adj.at(u).at(v);
}

const std::unordered_map<Graph::VertexT, int>& Graph::get_neighbors(const VertexT u) const {
	return adj.at(u);
}

std::size_t Graph::size() const {
	return adj.size() - inactive.size();
}

std::vector<Graph::VertexT> Graph::get_vertices() const {
	std::vector<VertexT> res{};
	for (const auto& k : adj | std::views::keys) {
		if (!inactive.contains(k)) {
			res.push_back(k);
		}
	}
	return res;
}
