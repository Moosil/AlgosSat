import heapq
from itertools import chain

import networkx as nx


class VertexT: pass


SupplyID = int

SupplyStorage = tuple[
	list[VertexT], tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]]


# # Source - https://stackoverflow.com/a/13276237
# # Posted by Sasha Chedygov, modified by community. See post 'Timeline' for change history
# # Retrieved 2026-06-23, License - CC BY-SA 3.0
# class TwoWayDict(dict):
#     def __init__(self, dictionary: dict):
#         super().__init__(chain.from_iterable(((k, v), (v, k)) for k, v in dictionary.items()))
#
#     @classmethod
#     def __class_getitem__(cls, key):
#         return f"TwoWayDict[{key.__name__}]"
#
#     def __setitem__(self, key, value):
#         # Remove any previous connections with these values
#         if key in self:
#             del self[key]
#         if value in self:
#             del self[value]
#         dict.__setitem__(self, key, value)
#         dict.__setitem__(self, value, key)
#
#     def __delitem__(self, key):
#         dict.__delitem__(self, self[key])
#         dict.__delitem__(self, key)
#
#     def __len__(self):
#         """Returns the number of connections"""
#         return dict.__len__(self) // 2


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


def get_supplies_to_collect(supplies: set[VertexT], vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID], supply_storage: SupplyStorage) -> set[VertexT]:
	return supplies.difference((s for s in supplies if vertex_to_supply_id[s] in found_supply_ids or vertex_to_supply_id[s] in supply_storage))


def ember_rescue(
		G: nx.Graph,
		entry: VertexT,
		exits: set[VertexT],
		supplies: set[VertexT],
		supply_storage: SupplyStorage,
		vertex_to_supply_id: dict[VertexT, SupplyID],
		found_supply_ids: set[SupplyID]
) -> SupplyStorage:
	res: list[VertexT] = []

	"""Get supplies that could be collected in the graph"""
	supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

	"""Get number of supplies to find"""
	number_of_supplies_to_collect = max(len(supplies), len([i for i in supply_storage if i is not None]))

	prevs: dict = {}
	wing: nx.Graph
	for wing in G:
		"""Get entry/junction -> exit/junction pair paths"""
		prevs[wing] = dijkstra(wing, list(wing.nodes)[0])

	wing_cost_rewards: dict[nx.Graph, dict[VertexT, ]]


	return res, (None, None, None, None, None)
