import heapq
from itertools import chain
from typing import Generator, Iterable

import networkx as nx


class VertexT: pass

WingT = nx.Graph

SupplyID = int

SupplyStorage = tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]

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
		return left_path[:right_index] + list(reversed(right_path))
	if left in right_path:
		left_index = right_path.index(left)
		return left_path + list(reversed(right_path[:left_index]))
	raise ValueError(f"prev does not contain the vertices: {source} and {sink}")


def get_supplies_to_collect(
	supplies: set[VertexT], vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID],
	supply_storage: SupplyStorage
) -> set[VertexT]:
	return supplies.difference(
		(s for s in supplies if vertex_to_supply_id[s] in found_supply_ids or vertex_to_supply_id[s] in supply_storage)
	)

def get_which_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], vertex: VertexT) -> WingT:
	for g in G[0]:
		if vertex in g.nodes:
			return g
	raise ValueError(f"vertex {vertex} is not in any graph in G")

def get_vertices_in_wing(wing: WingT, vertices: Iterable[VertexT]) -> Generator[VertexT]:
	return (v for v in vertices if v in wing.nodes)

def get_junctions_in_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], wing: WingT) -> Generator[VertexT]:
	return get_vertices_in_wing(wing, chain(*G[1]))

def get_junction_other(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], junction: VertexT) -> VertexT:
	edge = tuple(next(filter(lambda e: junction in e, G[1])))
	if edge[0] == junction:
		return edge[1]
	else:
		return edge[0]

def reconstruct_path(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], came_from: dict[VertexT, VertexT | None], e: VertexT, prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> list:
	meta_path = []
	curr = e
	while curr in came_from:
		meta_path.append(curr)
		curr = came_from[curr]

	res = []
	for i in range(len(meta_path) - 1, 0, -1):
		u = meta_path[i - 1]
		v = meta_path[i]
		u_wing = get_which_wing(G, u)
		v_wing = get_which_wing(G, v)
		if u_wing == v_wing:
			res += get_pair_shortest_path(v, u, prevs[u_wing])[:-1]
		else:
			res.append(v)

	res.append(meta_path[0])

	return res

def dijkstra_meta(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], source: VertexT, sinks: set[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> dict[VertexT, list[VertexT]]:
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
			w = get_path_length(G, [u, v], prevs)
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
			w = get_path_length(G, [u, v], prevs)
			if v not in dist or dist[u] + w < dist[v]:
				prev[v] = u
				dist[v] = dist[u] + w
				heapq.heappush(pq, (dist[v], v))

	return res

def get_apsp(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, exits: set[VertexT], supplies: set[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> dict[VertexT, dict[VertexT, list[VertexT]]]:
	res: dict[VertexT, dict[VertexT, list[VertexT]]] = defaultdict(dict)
	for source in supplies.union((entry,)):
		dijkstra_res = dijkstra_meta(G, source, supplies.union(exits), prevs)
		for sink in dijkstra_res:
			res[source][sink] = dijkstra_res[sink]

	return res

def get_path_length(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], path: list[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> int:
	res = 0
	for i in range(len(path) - 1):
		u = path[i]
		v = path[i + 1]
		u_wing = get_which_wing(G, u)
		v_wing = get_which_wing(G, v)
		if u_wing == v_wing:
			sub_path = get_pair_shortest_path(u, v, prevs[u_wing])
			for j in range(len(sub_path) - 1):
				res += u_wing.get_edge_data(sub_path[j], sub_path[j + 1])['weight']
		else:
			res += 1

	return res


def get_apsp_dist(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], pair_path_map: dict[VertexT, dict[VertexT, list[VertexT]]], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> dict[VertexT, dict[VertexT, int]]:
	res: dict[VertexT, dict[VertexT, int]] = defaultdict(dict)
	for source, sink_dict in pair_path_map.items():
		for sink, path in sink_dict.items():
			res[source][sink] = get_path_length(G, path, prevs)

	return res

# upper bound
def nearest_neighbour(source: VertexT, sinks: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]]) -> list[VertexT]:
	sinks = sinks.copy()
	res: list[VertexT] = [source]
	cost: int = 0
	curr = source
	while len(sinks) > 0:
		min_found = list(sinks)[0]
		min_cost = pair_path_costs[curr][min_found]
		for sink in sinks:
			curr_cost = pair_path_costs[curr][sink]
			if curr_cost < min_cost:
				min_found = sink
				min_cost = curr_cost

		sinks.remove(min_found)
		res.append(min_found)
		curr = min_found
		cost += min_cost

	min_found = list(exits)[0]
	min_cost = pair_path_costs[curr][min_found]
	for sink in exits:
		curr_cost = pair_path_costs[curr][sink]
		if curr_cost < min_cost:
			min_found = sink
			min_cost = curr_cost

	res.append(min_found)
	cost += min_cost
	return res

def brute_force_recursive(source: VertexT, sinks: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], fuel: int) -> tuple[list[VertexT], int]:
	min_cost = float('infinity')
	min_cost_walk = None

	if fuel == 0:
		for sink in exits:
			cost = pair_path_costs[source][sink]
			if cost < min_cost:
				min_cost_walk = [sink]
				min_cost = cost
	else:
		for sink in sinks:
			min_walk_through, cost = brute_force_recursive(sink, sinks.difference({sink}), exits, pair_path_costs, fuel - 1)
			cost += pair_path_costs[source][sink]
			if cost < min_cost:
				min_cost = cost
				min_cost_walk = [sink] + min_walk_through

	return min_cost_walk, min_cost

def brute_force(entry: VertexT, supplies: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], max_supplies: int) -> list[VertexT]:
	return [entry] + brute_force_recursive(entry, supplies, exits, pair_path_costs, max_supplies)[0]

import numpy as np

# we don't actually need this cause we know a basic feasible solution via nearest neighbour in O(n) time
# def simplex(A: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray | None:
# 	"""
# 	Turns min  cTx:
# 		 s.t. Ax = b;
# 			  x >= 0
# 	Into min  eTz:
# 		 s.t. Ax + Iz = b;
# 			  x >= 0;
# 			  z >= 0
# 	"""
# 	e = np.array([[0] for _ in range(c.shape[0])] + [[1] for _ in range(A.shape[0])])
# 	dummy_A = np.block([[A, np.identity(A.shape[0])]])
# 	dummy_B = np.array([i for i in range(A.shape[1], A.shape[1] + A.shape[0])])
# 	dummy_initial = np.array([np.hstack(([0 for _ in range(A.shape[1])], b.transpose()[0]))]).transpose()
# 	dummy = _simplex(dummy_A, b, e, dummy_B, dummy_initial, np.linalg.inv(np.array([dummy_A[:, i] for i in dummy_B])))
#
# 	non_artificial_vars = dummy[[i for i in range(e.shape[0]) if e[i] != 1]].ravel()
# 	artificial_vars = dummy[[i for i in range(e.shape[0]) if e[i] == 1]].ravel()
#
# 	if np.where(artificial_vars > 0)[0].size == 0:
# 		return _simplex(A, b, c, np.array([i for i in range(non_artificial_vars.shape[0]) if non_artificial_vars[i] != 0]))

def _simplex(A: np.ndarray, b: np.ndarray, c: np.ndarray, basis: np.ndarray, initial: np.ndarray, inv_a_basic: np.ndarray, min: bool) -> np.ndarray | None:
	"""
	Solves min cTx: Ax = b, x >= 0
	"""
	"""https://www.matem.unam.mx/~omar/math340/revised-simplex.html"""
	"""https://people.math.carleton.ca/~kcheung/math/notes/MATH5801/05/5_1_simplex.html"""
	"""https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html"""
	min_mult: int = -1 if min else 1
	non_basic = np.array([i for i in range(c.size) if i not in basis])
	a_non_basic = A[:, non_basic]
	select_k = c[non_basic].transpose() - c[basis].transpose() @ inv_a_basic @ a_non_basic
	k: int = -1
	max_found: int = 0
	for i in range(select_k.size):
		if select_k[0][i] > min_mult * max_found:
			k = i
			max_found = select_k[0][i]

	if k == -1:
		"""optimal solutiuon found"""
		return initial

	k = non_basic[k]

	d = inv_a_basic @ min_mult * A[:, k]

	initial_basic = initial[basis]

	t = max([initial_basic[i][0] / min_mult * d[i] for i in range(len(initial_basic)) if min_mult * d[i] > 0])

	def get_next_x(i: int) -> int:
		if i == k:
			return t
		if i in non_basic:
			return 0
		for l in range(len(basis)):
			if basis[l] == i:
				return initial_basic[l][0] - min_mult * t * d[l]
		raise IndexError("basis does not contain i somehow...")

	next_x = np.array([[get_next_x(i)] for i in range(initial.shape[0])])

	E = np.identity(inv_a_basic.shape[1])
	i: int = -1
	for j in range(d.shape[0]):
		if initial_basic[j][0] - min_mult * t * d[j] == 0:
			i = j
			break

	if i == -1:
		raise IndexError("shouldn't happen")

	i = basis[i]
	E[:, i] = d
	next_inv_a_basic = np.linalg.inv(E) @ inv_a_basic

	next_basic = np.array([j for j in range(next_x.shape[0]) if (j in basis and j != i) or j == k])

	return _simplex(A, b, c, next_basic, next_x, next_inv_a_basic, min)

# lower bound by solving dual
def solve_relaxed_lp(entry: VertexT, exits: set[VertexT], supplies: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], upper_bound_path: list[VertexT]) -> int:
	# Dual problem started:
	# A = np.array([[1 if i == u or i == v else 0 for i in [entry] + list(supplies) + [exits] + list(supplies)] for u in supplies.union([entry]) for v in supplies.union(exits)])
	# b = np.array([[pair_path_costs[u][v]] for u in supplies.union([entry]) for v in supplies.union(exits)])
	# c = np.ones((1 + len(exits) + 2 * len(supplies), 1))
	#
	# initial = [i for u in supplies.union([entry]) for v in supplies.union(exits)])

	A = np.array(
		[[1 if i == u     else 0 for i in [entry] + list(supplies) for _ in list(supplies) + list(exits)] for u in [entry] + list(supplies)] + \
		[[1 if i == v     else 0 for _ in [entry] + list(supplies) for i in list(supplies) + list(exits)] for v in list(supplies)] + \
		[[1 if v in exits else 0 for _ in [entry] + list(supplies) for v in list(supplies) + list(exits)]]
		)
	b = np.ones((1 + len(exits) + 2 * len(supplies), 1))
	c = np.array([[pair_path_costs[u][v]] for u in supplies.union([entry]) for v in supplies.union(exits)])

	initial = np.array([[1 if u in upper_bound_path and upper_bound_path[upper_bound_path.index(u) + 1] == v else 0] for u in supplies.union([entry]) for v in supplies.union(exits)])

	basis = np.array([i for i in range(initial.shape[0]) if initial[i] == [1]])
	i: int = 0
	while len(basis) < A.shape[0]:
		if list(A[:, i]) not in list(list(arr) for arr in A[:, basis].transpose()):
			basis = np.append(basis, [i])
		i += 1
	basis.sort()

	A_basis = np.array([A[:, i] for i in basis])
	print(np.linalg.matrix_rank(A))

	answer = simplex(A, b, c, basis, initial, np.linalg.inv(A_basis), True)

	res: int = 0
	mapping = [(u, v) for u in supplies.union([entry]) for v in supplies.union(exits)]
	for i, a in enumerate(answer):
		if a > 0:
			edge = mapping[i]
			res += pair_path_costs[edge[0]][edge[1]] * a


def get_path_from_super_path(super_path: list[VertexT], apsp_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> list[VertexT]:
	res = []
	for i in range(len(super_path) - 1):
		pair_path = apsp_map[super_path[i]][super_path[i + 1]]
		res += pair_path
		if i != len(super_path) - 2:
			res.pop()

	return res


def ember_rescue(
	G: tuple[set[WingT], set[tuple[VertexT, VertexT]]],
	entry: VertexT,
	exits: set[VertexT],
	supplies: set[VertexT],
	supply_storage: SupplyStorage,
	vertex_to_supply_id: dict[VertexT, SupplyID],
	found_supply_ids: set[SupplyID]
) -> tuple[list[VertexT], SupplyStorage]:
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
	super_path_greedy = nearest_neighbour(entry, supplies, exits, apsp_dist_map)
	lower_bound = solve_relaxed_lp(entry, exits, supplies, apsp_dist_map, super_path_greedy)
	print(lower_bound)

	"""brute-force"""
	super_path = brute_force(entry, supplies, exits, apsp_dist_map, number_of_supplies_to_collect)

	res = get_path_from_super_path(super_path, apsp_map)

	j: int = 0
	collected_supplies = [v for v in res if v in supplies]
	supply_storage = list(supply_storage)
	for i in range(len(supply_storage)):
		if j >= number_of_supplies_to_collect:
			break
		if supply_storage[i] is None:
			supply_storage[i] = vertex_to_supply_id[collected_supplies[j]]
			j += 1

	supply_storage = tuple(supply_storage)

	return res, supply_storage, get_path_from_super_path(super_path_greedy, apsp_map)
