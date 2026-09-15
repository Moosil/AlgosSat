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

void Graph::set_edge_weight(VertexT u, VertexT v, WeightT w) {
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
	for (const auto& u : adj | std::views::keys) {
		if (!inactive.contains(u)) {
			return u;
		}
	}
	throw std::runtime_error("Graph is fully inactive, get_a_vertex() requires graph is not empty.");
}

Graph::WeightT Graph::get_edge_weight(const VertexT u, const VertexT v) const {
	return adj.at(u).at(v);
}

std::unordered_map<Graph::VertexT, int> Graph::get_neighbors(const VertexT u) const {
	std::unordered_map<VertexT, int> res{};
	for (const auto& [v, w] : adj.at(u)) {
		if (!inactive.contains(v)) {
			res[v] = w;
		}
	}
	return res;
}

std::size_t Graph::get_degree(const VertexT u) const {
	std::size_t res{0};
	for (const auto& v : get_neighbors(u) | std::views::keys) {
		if (!inactive.contains(v)) {
			res++;
		}
	}
	return res;
}

std::size_t Graph::size() const {
	return adj.size() - inactive.size();
}

std::vector<Graph::VertexT> Graph::get_vertices() const {
	std::vector<VertexT> res{};
	for (const auto u : adj | std::views::keys) {
		if (!inactive.contains(u)) {
			res.push_back(u);
		}
	}
	return res;
}

std::vector<std::tuple<Graph::VertexT, Graph::VertexT, Graph::WeightT>> Graph::get_edges() const {
	std::vector<std::tuple<VertexT, VertexT, WeightT>> res{};
	for (const auto u : adj | std::views::keys) {
		if (!inactive.contains(u)) {
			for (const auto& [v, w] : get_neighbors(u)) {
				if (!inactive.contains(v)) {
					res.emplace_back(u, v, w);
				}
			}
		}
	}
	return res;
}

void Graph::update() {
	for (const auto vertex : inactive) {
		adj.erase(vertex);
	}

	for (auto& n : adj | std::views::values) {
		for (const auto vertex : inactive) {
			n.erase(vertex);
		}
	}

	inactive.clear();
}
