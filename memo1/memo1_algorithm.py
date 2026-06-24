import heapq
from collections import defaultdict

import networkx as nx

class VertexT:
	pass


def reconstruct_path(came_from: dict[VertexT, VertexT | None], e: VertexT) -> list:
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

	prev: dict[VertexT, VertexT | None] = {source: None}
	pq = [(0., source)]
	heapq.heapify(pq)
	while len(pq) > 0:
		_, u = heapq.heappop(pq)

		# required for the python heapq that doesn't allow changing priority
		if u in visited:
			continue
		visited.add(u)

		if u in sinks:
			res[u] = reconstruct_path(prev, u)
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

def get_unfound_supplies(supplies: set[VertexT], supply_id: dict[VertexT, str], collected_supplies: set[str], supply_storage: list[str | None]) -> set[VertexT]:
	res = set()
	for supply in supplies:
		curr_id = supply_id.get(supply, None)
		if curr_id is not None and curr_id not in collected_supplies and curr_id not in supply_storage:
			res.add(supply)

	return res

def brute_force_recursive(source: VertexT, sinks: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], fuel: int) -> tuple[list[VertexT], int]:
	min_cost = float('infinity')
	min_cost_walk = None

	if fuel == 0:
		for exit in exits:
			cost = pair_path_costs[source][exit]
			if cost < min_cost:
				min_cost_walk = [exit]
				min_cost = cost

	for sink in sinks:
		min_walk_through, cost = brute_force_recursive(sink, sinks.difference({sink}), exits, pair_path_costs, fuel - 1)
		cost += pair_path_costs[source][sink]
		if cost < min_cost:
			min_cost = cost
			min_cost_walk = [sink] + min_walk_through

	return min_cost_walk, min_cost

def brute_force(v_e: VertexT, supplies: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], max_supplies: int) -> list[VertexT]:
	return [v_e] + brute_force_recursive(v_e, supplies, exits, pair_path_costs, max_supplies)[0]

def ember_rescue(g: nx.Graph, v_e: VertexT, exits: set[VertexT], supplies: set[VertexT], supply_id: dict[VertexT, str], supply_storage: list[str], collected_supplies: set[str]) -> list[VertexT]:
	unfound_supplies = get_unfound_supplies(supplies, supply_id, collected_supplies, supply_storage)

	pairs_paths = some_pairs_shortest_path(g, unfound_supplies.union({v_e}), unfound_supplies.union(exits).union({v_e}))
	pairs_paths_costs = get_pairs_path_distances(g, pairs_paths)

	num_supplies_carrying = len([i for i in supply_storage if i is not None])

	super_path = brute_force(v_e, unfound_supplies, exits, pairs_paths_costs, 5 - num_supplies_carrying)

	res = []

	for i in range(len(super_path) - 1):
		pair_path = pairs_paths[super_path[i]][super_path[i + 1]]
		res += pair_path
		if i != len(super_path) - 2:
			res.pop()

	return res

