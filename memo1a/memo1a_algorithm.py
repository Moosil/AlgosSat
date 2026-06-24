import heapq
from itertools import chain
from typing import Generator, Iterable

import networkx as nx


class VertexT: pass


EdgeT = frozenset

WingT = nx.Graph

SupplyID = int

SupplyStorage = tuple[
	list[VertexT], tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]]

# Source - https://stackoverflow.com/a/8702435
# Posted by Hugo Walter, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-23, License - CC BY-SA 3.0
from collections import defaultdict

nested_dict = lambda: defaultdict(nested_dict)


def dijkstra(g: nx.Graph, source: VertexT) -> dict[VertexT, VertexT | None]:
	dist = {s: float('infinity') for s in g}

	dist[source] = 0

	# visited set replaced update(PQ, v)
	visited = set()

	prev: dict[VertexT, VertexT | None] = dict({source: None})
	pq = [(0., source)]
	heapq.heapify(pq)
	while len(pq) > 0:
		_, u = heapq.heappop(pq)

		# required for the python heapq that doesn't allow changing priority
		if u in visited:
			continue
		visited.add(u)

		for v in g.neighbors(u):
			w = g.get_edge_data(u, v)["weight"]
			if dist[u] + w < dist[v]:
				prev[v] = u
				dist[v] = dist[u] + w
				heapq.heappush(pq, (dist[v], v))

	return prev


def get_pair_shortest_path(source: VertexT, sink: VertexT, prev: dict[VertexT, VertexT | None]) -> list[VertexT]:
	left_path = [source]
	right_path = [sink]
	left = source
	right = sink
	while left not in right_path and right not in left_path:
		if prev[left] is not None:
			left = prev[left]
			left_path.append(left)
		if prev[right] is not None:
			right = prev[right]
			right_path.append(right)

	if right in left_path:
		right_index = left_path.index(right)
		return left_path[:right_index] + list(reversed(right_path[:-1]))
	if left in right_path:
		left_index = right_path.index(left)
		return right_path[:left_index] + list(reversed(left_path[:-1]))
	raise ValueError(f"prev does not contain the vertices: {source} and {sink}")


def get_supplies_to_collect(
	supplies: set[VertexT], vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID],
	supply_storage: SupplyStorage
) -> set[VertexT]:
	return supplies.difference(
		(s for s in supplies if vertex_to_supply_id[s] in found_supply_ids or vertex_to_supply_id[s] in supply_storage)
	)

def get_which_wing(G: tuple[set[WingT], set[EdgeT[VertexT]]], vertex: VertexT) -> WingT:
	for g in G[0]:
		if vertex in g.nodes:
			return g
	raise ValueError(f"vertex {vertex} is not in any graph in G")

def get_vertices_in_wing(wing: WingT, vertices: Iterable[VertexT]) -> Generator[VertexT]:
	return (v for v in vertices if v in wing.nodes)

def get_junctions_in_wing(G: tuple[set[WingT], set[EdgeT[VertexT]]], wing: WingT) -> Generator[VertexT]:
	return get_vertices_in_wing(wing, chain(*G[1]))

def get_junction_other(G: tuple[set[WingT], set[EdgeT[VertexT]]], junction: VertexT) -> VertexT:
	edge = list(next(filter(lambda e: junction in e, G[1])))
	if edge[0] == junction:
		return edge[1]
	else:
		return edge[0]

def reconstruct_path(G: tuple[set[WingT], set[EdgeT[VertexT]]], came_from: dict[VertexT, VertexT | None], e: VertexT, prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> list:
	meta_path = []
	curr = e
	while curr in came_from:
		meta_path.append(curr)
		curr = came_from[curr]
	meta_path.reverse()

	res = []
	for i in range(len(meta_path) - 1):
		u = meta_path[i]
		v = meta_path[i + 1]
		u_wing = get_which_wing(G, u)
		v_wing = get_which_wing(G, v)
		if u_wing == v_wing:
			res += get_pair_shortest_path(u, v, prevs[u_wing])[:-1]
		else:
			res.append(u)

	res.append(meta_path[-1])

	return res

def dijkstra_meta(G: tuple[set[WingT], set[EdgeT[VertexT]]], source: VertexT, sinks: set[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> dict[VertexT, list[VertexT]]:
	res = {}
	dist = {source: 0}

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
			res[u] = reconstruct_path(G, prev, u, prevs)
			if len(res) == len(sinks):
				return res

		u_wing = get_which_wing(G, u)

		for v in get_junctions_in_wing(G, u_wing):
			w = len(get_pair_shortest_path(u, v, prevs[u_wing]))
			if v not in dist or dist[u] + w < dist[v]:
				prev[v] = u
				dist[v] = dist[u] + w
				heapq.heappush(pq, (dist[v], v))

			other_v = get_junction_other(G, v)
			if other_v not in dist or dist[v] + 1 < dist[other_v]:
				prev[other_v] = v
				dist[other_v] = dist[v] + 1
				heapq.heappush(pq, (dist[other_v], other_v))
		for v in get_vertices_in_wing(u_wing, sinks):
			w = len(get_pair_shortest_path(u, v, prevs[u_wing]))
			if v not in dist or dist[u] + w < dist[v]:
				prev[v] = u
				dist[v] = dist[u] + w
				heapq.heappush(pq, (dist[v], v))

	return res

def get_apsp(G: tuple[set[WingT], set[EdgeT[VertexT]]], entry: VertexT, exits: set[VertexT], supplies: set[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> dict[EdgeT[VertexT], list[VertexT]]:
	res: dict[EdgeT[VertexT], list[VertexT]] = {}
	for source in supplies.union((entry,)):
		dijkstra_res = dijkstra_meta(G, source, supplies.union(exits), prevs)
		for sink in dijkstra_res:
			res[EdgeT((source, sink))] = dijkstra_res[sink]

	return res

def get_path_length(G: tuple[set[WingT], set[EdgeT[VertexT]]], path: list[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> int:
	res = 0
	for i in range(len(path) - 1):
		u = path[i]
		v = path[i + 1]
		u_wing = get_which_wing(G, u)
		v_wing = get_which_wing(G, v)
		if u_wing == v_wing:
			res += len(get_pair_shortest_path(u, v, prevs[u_wing])[:-1])
		else:
			res += 1

	return res


def get_apsp_dist(G: tuple[set[WingT], set[EdgeT[VertexT]]], pair_path_map: dict[EdgeT[VertexT], list[VertexT]], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> dict[EdgeT[VertexT], int]:
	res: dict[EdgeT[VertexT], int] = {}
	for edge, path in pair_path_map.items():
		res[edge] = get_path_length(G, path, prevs)

	return res

def brute_force_recursive(source: VertexT, sinks: set[VertexT], exits: set[VertexT], pair_path_costs: dict[EdgeT[VertexT], int], fuel: int) -> tuple[list[VertexT], int]:
	min_cost = float('infinity')
	min_cost_walk = None

	if fuel == 0:
		for exit in exits:
			cost = pair_path_costs[EdgeT((source, exit))]
			if cost < min_cost:
				min_cost_walk = [exit]
				min_cost = cost

	for sink in sinks:
		min_walk_through, cost = brute_force_recursive(sink, sinks.difference({sink}), exits, pair_path_costs, fuel - 1)
		cost += pair_path_costs[EdgeT((source, sink))]
		if cost < min_cost:
			min_cost = cost
			min_cost_walk = [sink] + min_walk_through

	return min_cost_walk, min_cost

def brute_force(entry: VertexT, supplies: set[VertexT], exits: set[VertexT], pair_path_costs: dict[EdgeT[VertexT], int], max_supplies: int) -> list[VertexT]:
	return [entry] + brute_force_recursive(entry, supplies, exits, pair_path_costs, max_supplies)[0]

def ember_rescue(
	G: tuple[set[WingT], set[EdgeT[VertexT]]],
	entry: VertexT,
	exits: set[VertexT],
	supplies: set[VertexT],
	supply_storage: SupplyStorage,
	vertex_to_supply_id: dict[VertexT, SupplyID],
	found_supply_ids: set[SupplyID]
) -> SupplyStorage:
	res: list[VertexT]

	"""Get supplies that could be collected in the graph"""
	supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

	"""Get number of supplies to find"""
	number_of_supplies_to_collect = max(len(supplies), len([i for i in supply_storage if i is not None]))

	"""Get entry/junction -> exit/junction pair paths"""
	prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: dijkstra(wing, list(wing.nodes)[0]) for wing in G[0]}

	"""supplies apsp"""
	apsp_map = get_apsp(G, entry, exits, supplies, prevs)
	apsp_dist_map = get_apsp_dist(G, apsp_map, prevs)

	"""get good first guess"""
	super_path = brute_force(entry, supplies, exits, apsp_dist_map, number_of_supplies_to_collect)

	res = [entry]
	for i in range(len(super_path) - 1):
		pair_path = apsp_map[EdgeT((super_path[i], super_path[i + 1]))]
		res += pair_path
		if i != len(super_path) - 2:
			res.pop()

	return res, (None, None, None, None, None)
