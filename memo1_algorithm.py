import heapq
from collections import defaultdict

import networkx as nx

class VertexT:
	pass


def reconstruct_path(came_from: dict[VertexT, VertexT], e: VertexT) -> list:
	res = []
	curr = e
	while curr in came_from:
		res.append(curr)
		curr = came_from[curr]
	res.reverse()
	return res

def dijkstra(g: nx.Graph, source: VertexT, sinks: set[VertexT]) -> dict[VertexT, list[VertexT]]:
	res = {}
	dist = {s: float('infinity') for s in g}

	dist[source] = 0

	# visited set replaced update(PQ, v)
	visited = set()

	prev = {}
	pq = [(0., source)]
	heapq.heapify(pq)
	while len(pq) > 0:
		_, u = heapq.heappop(pq)

		# required for the python heapq that:esn't allow changing priority
		if u in visited:
			continue
		visited.add(u)

		if u in sinks:
			res[u] = [source] + reconstruct_path(prev, u)
			if len(res) == len(sinks):
				return res

		for v in g.neighbors(u):
			w = g.get_edge_data(u, v)["weight"]
			if dist[u] + w < dist[v]:
				prev[v] = u
				dist[v] = dist[u] + w
				heapq.heappush(pq, (dist[v], v))

	return res

def some_pairs_shortest_path(g: nx.Graph, sources: set[VertexT], sinks: set[VertexT]) -> dict[VertexT, dict[VertexT, list[VertexT]]]:
	res = defaultdict(dict)
	for source in sources:
		paths = dijkstra(g, source, sinks.difference({source}))
		for sink in sinks.difference({source}):
			res[source][sink] = paths[sink]

	return res

def get_path_length(g: nx.Graph, path: list[VertexT]) -> int:
	return sum(g.get_edge_data(path[i], path[i + 1])["weight"] for i in range(len(path) - 2))

def get_pairs_path_distances(g: nx.Graph, pair_path_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> dict[VertexT, dict[VertexT, int]]:
	res = defaultdict(dict)
	for key_0, value_0 in pair_path_map.items():
		for key_1, value_1 in value_0.items():
			res[key_0][key_1] = get_path_length(g, value_1)

	return res

def get_unfound_supplies(supplies: set[VertexT], supply_id: dict[VertexT, str], collected_supplies: set[str], supply_storage: list[str]) -> set[VertexT]:
	res = set()
	for supply in supplies:
		curr_id = supply_id.get(supply, None)
		if curr_id is not None and curr_id not in collected_supplies and curr_id not in supply_storage:
			res.add(supply)

	return res

def generate_permutations(items: list, len_left: int) -> list[list]:
	if len(items) == 1 and len_left >= 1:
		return [items]
	if len_left == 1:
		res = []
		for i in items:
			res.append([i])
		return res

	res = []
	for i in range(len(items)):
		item = items[i]
		sublist = [items[j] for j in range(len(items)) if j != i]
		for perm in generate_permutations(sublist, len_left - 1):
			res.append([item] + perm)

	return res

def brute_force(g: nx.Graph, v_e: VertexT, sources: set[VertexT], exits: set[VertexT], pair_path_map: dict[VertexT, dict[VertexT, list[VertexT]]], max_supplies: int) -> list[VertexT]:
	pair_path_cost_map = get_pairs_path_distances(g, pair_path_map)
	min_cost_found = float('infinity')
	min_cost_walk = None
	for permutation in generate_permutations(list(sources), max_supplies):
		cost = pair_path_cost_map[v_e][permutation[0]] + \
			sum(pair_path_cost_map[permutation[i]][permutation[i + 1]] for i in range(len(permutation) - 1))

		min_exit_cost = float('infinity')
		min_exit = list(exits)[0]
		end = permutation[len(permutation) - 1]
		for exit_vertex in exits:
			if pair_path_cost_map[end][exit_vertex] < min_exit_cost:
				min_exit = exit_vertex
				min_exit_cost = pair_path_cost_map[end][exit_vertex]
		if cost + min_exit_cost < min_cost_found:
			walk = [v_e] + list(permutation)
			walk.append(min_exit)
			min_cost_walk = walk
			min_cost_found = cost + min_exit_cost
	return min_cost_walk

def ember_rescue(g: nx.Graph, v_e: VertexT, exits: set[VertexT], supplies: set[VertexT], supply_id: dict[VertexT, str], supply_storage: list[str], collected_supplies: set[str]) -> list[VertexT]:
	unfound_supplies = get_unfound_supplies(supplies, supply_id, collected_supplies, supply_storage)

	pairs_paths = some_pairs_shortest_path(g, unfound_supplies.union({v_e}), unfound_supplies.union(exits))

	num_supplies_carrying = len([i for i in supply_storage if i is not None])

	super_path = brute_force(g, v_e, unfound_supplies, exits, pairs_paths, 5 - num_supplies_carrying)

	res = []

	for i in range(len(super_path) - 1):
		pair_path = pairs_paths[super_path[i]][super_path[i + 1]]
		res += pair_path
		if i != len(super_path) - 2:
			res.pop()

	return res

