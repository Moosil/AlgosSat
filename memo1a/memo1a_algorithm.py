import heapq
from itertools import chain

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
	res = {}
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

	return res


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


def get_which_wing(G: tuple[set[nx.Graph], set[tuple[VertexT, VertexT]]], vertex: VertexT) -> nx.Graph:
	for g in G[0]:
		if vertex in g.nodes:
			return g
	raise ValueError(f"vertex {vertex} is not in any graph in G")


def get_wing_rewards_shortest_path(
	source: VertexT, sink: VertexT, prev: dict[VertexT, VertexT | None], supplies: list[VertexT]
) -> list[VertexT]:
	shortest_path = get_pair_shortest_path(source, sink, prev)

	for supply in supplies:
		supply_path = []
		curr = supply
		while curr not in shortest_path:
			supply_path.append(curr)
			curr = prev[curr]

		insert_idx = shortest_path.index(curr)
		shortest_path = shortest_path[:insert_idx + 1] + list(reversed(supply_path)) + [
			supply
		] + supply_path + shortest_path[insert_idx:]

	return shortest_path


def get_apsp_graph(
	G: tuple[set[WingT], set[EdgeT[VertexT]]], supplies: set[VertexT],
	wing_cost_rewards: dict[WingT, dict[EdgeT[VertexT], dict[frozenset[VertexT], tuple[int, list[VertexT]]]]],
	prevs: dict[WingT, dict[VertexT, VertexT | None]]
) -> tuple[dict[EdgeT[WingT], dict[int, list[VertexT]]], dict[WingT, dict[EdgeT[VertexT], dict[frozenset[VertexT], tuple[int, list[VertexT]]]]]]:
	pass


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

	"""get cost of going from entry/junction -> exit/junction in each wing"""
	"""we will use memoisation to lazily """
	wing_cost_rewards: dict[
		WingT, dict[EdgeT[VertexT], dict[frozenset[VertexT], tuple[int, list[VertexT]]]]] = nested_dict()

	"""greedily find first solution"""
	apsp_graph, wing_cost_rewards = get_apsp_graph(G, supplies, wing_cost_rewards, prevs)
	res = nearest_neighbour(apsp_graph, )

	return res, (None, None, None, None, None)
