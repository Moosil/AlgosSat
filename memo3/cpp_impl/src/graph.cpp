#include "graph.h"

#include <algorithm>
#include <queue>
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

void Graph::set_edge_weight(const VertexT u, const VertexT v, const WeightT w) {
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

std::vector<Graph::VertexT> Graph::get_neighbour_vertices(const VertexT u) const {
	std::vector<VertexT> res{};
	for (const auto& v : adj.at(u) | std::views::keys) {
		if (!inactive.contains(v)) {
			res.push_back(v);
		}
	}
	return res;
}

std::unordered_map<Graph::VertexT, Graph::WeightT> Graph::get_neighbours(const VertexT u) const {
	std::unordered_map<VertexT, WeightT> res{};
	for (const auto& [v, w] : adj.at(u)) {
		if (!inactive.contains(v)) {
			res[v] = w;
		}
	}
	return res;
}

std::size_t Graph::get_degree(const VertexT u) const {
	std::size_t res{0};
	for (const auto& v : get_neighbours(u) | std::views::keys) {
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

std::vector<std::tuple<Graph::VertexT, Graph::VertexT, Graph::WeightT> > Graph::get_edges() const {
	std::vector<std::tuple<VertexT, VertexT, WeightT> > res{};
	for (const auto u : adj | std::views::keys) {
		if (!inactive.contains(u)) {
			for (const auto& [v, w] : get_neighbours(u)) {
				if (!inactive.contains(v)) {
					res.emplace_back(u, v, w);
				}
			}
		}
	}
	return res;
}

std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > Graph::sssp(VertexT source) const {
	std::unordered_map<VertexT, WeightT> dist;
	for (const auto& v : get_vertices()) {
		dist[v] = std::numeric_limits<WeightT>::max();
	}
	dist[source] = 0;
	std::unordered_map<VertexT, VertexT>                prev;
	std::priority_queue<std::pair<long long, VertexT> > pq;
	pq.emplace(0, source);

	while (!pq.empty()) {
		const auto [d, u] = pq.top();
		pq.pop();
		if (dist[u] < -d) {
			continue;
		}

		for (const auto& [v, w] : get_neighbours(u)) {
			if (dist[u] + w < dist[v]) {
				prev[v] = u;
				dist[v] = dist[u] + w;
				pq.emplace(-static_cast<long long>(dist[v]), v);
			}
		}
	}

	std::unordered_map<VertexT, std::vector<VertexT> > res{};
	for (const auto& v : get_vertices()) {
		res[v] = reconstruct_path(prev, v);
	}
	return res;
}

std::unordered_map<Graph::VertexT, std::size_t> Graph::sssp_dist(const VertexT source) const {
	return sssp_dist(source, sssp(source));
}

std::unordered_map<Graph::VertexT, std::size_t> Graph::sssp_dist(
	const VertexT                                             source,
	const std::unordered_map<VertexT, std::vector<VertexT> >& paths) const {
	std::unordered_map<VertexT, std::size_t> res{};
	for (const auto& [k, p] : paths) {
		res[k] = 0;
		for (std::size_t i = 0; i < p.size() - 1; ++i) {
			res[k] += get_edge_weight(p[i], p[i + 1]);
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

std::vector<Graph::VertexT> Graph::reconstruct_path(const std::unordered_map<VertexT, VertexT>& prev, VertexT sink) {
	std::vector res = {sink};
	while (prev.contains(sink)) {
		sink = prev.at(sink);
		res.push_back(sink);
	}
	std::ranges::reverse(res);
	return res;
}