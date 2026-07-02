import heapq
from itertools import chain
from typing import Generator, Iterable

import networkx as nx
import numpy as np


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

def nearest_neighbour(source: VertexT, sinks: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], fuel: int) -> tuple[list[VertexT], int]:
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
	return res, cost

def lin_kernighan(entry: VertexT, supplies: set[VertexT], exits: set[VertexT], matrix: dict[VertexT, dict[VertexT, int]], ub: list[VertexT]):
	BACKTRACK_DEPTH = 5
	INFEASIBLE_DEPTH = 2

	def reconstruct_walk_set(best_walk: set[tuple[VertexT, VertexT]]) -> list[VertexT]:
		res: list[VertexT] = []
		curr_edge = next(filter(lambda x: x[0] == entry, best_walk))

		while len(best_walk) > 0:
			best_walk.remove(curr_edge)
			res.append(curr_edge[0])
			curr_edge = next(filter(lambda x: x[0] == curr_edge[1], best_walk))

		return res


	def get_alternating(edges0: set[tuple[VertexT, VertexT]], edges1: set[tuple[VertexT, VertexT]]) -> set[tuple[VertexT, VertexT]] | None:
		edges = edges0.union(edges1).difference(edges1)

		try:
			not_visited: set[VertexT] = {entry}.union(exits).union(supplies)
			curr_edge = next(filter(lambda x: x[0] == entry, best_walk))
			while len(edges) > 0:
				if curr_edge[0] not in not_visited:
					return None
				not_visited.remove(curr_edge[0])
				edges.remove(curr_edge)
				curr_edge = next(filter(lambda x: x[0] == curr_edge[1], best_walk))
			if curr_edge[1] not in not_visited or curr_edge[1] not in exits:
				return None
			not_visited.remove(curr_edge[1])
			if len(not_visited) > 0:
				return None

			return edges0.union(edges1).difference(edges1)
		except:
			return None


	stack: list[tuple[VertexT, int, int]] = [(u, 0, 0) for u in matrix]

	best_walk = {(ub[i], ub[i + 1]) for i in range(len(ub) - 1)}
	best_swaps: set = set()
	best_gain: int = 0

	while best_gain == 0:
		curr: list[VertexT] = []
		while len(stack) > 0:
			u, i, g = stack.pop()
			curr[i] = u
			curr_swaps = {(curr[i], curr[i + 1]) for i in range(len(curr) - 1)}
			if i % 2 == 0:
				early_ret: int = 2
				for v in matrix[u]:
					if (u, v) in set(best_walk).difference(curr_swaps):
						if i <= INFEASIBLE_DEPTH or (u in exits and get_alternating(best_walk, curr_swaps) is not None):
							stack.append((v, i + 1, g + matrix[u][v]))
							early_ret -= 1
							if early_ret == 0:
								break
			else:
				if g > 0 and g > best_gain and get_alternating(best_walk, curr_swaps) is not None:
					best_swaps = curr_swaps
					best_gain = g

			u, j, g = stack[-1]
			if i <= j:
				if best_gain > 0:
					best_walk = best_walk.union(best_swaps).difference(best_swaps)
				elif i > BACKTRACK_DEPTH:
					while j > BACKTRACK_DEPTH:
						_, j, _ = stack.pop()

	return reconstruct_walk_set(best_walk)

"""https://www.geeksforgeeks.org/dsa/introduction-to-disjoint-set-data-structure-or-union-find-algorithm/"""
class UnionFind:
	def __init__(self, entries):
		# Initialize the parent array with each
		# element as its own representative
		self.parent = {e: e for e in entries}

	def find(self, i):
		# If i itself is root or representative
		if self.parent[i] == i:
			return i

		# Else recursively find the representative
		# of the parent
		return self.find(self.parent[i])

	def unite(self, i, j):
		# Representative of set containing i
		irep = self.find(i)

		# Representative of set containing j
		jrep = self.find(j)

		# Make the representative of i's set
		# be the representative of j's set
		self.parent[irep] = jrep

def kruskals(partial_sol: list[VertexT], sol_length: int, matrix: dict[VertexT, dict[VertexT, int]]):
	edges = [(matrix[u][v], u, v) for u in matrix for v in matrix[u]]
	verts = [u for u in matrix] + [v for v in matrix[list(matrix.keys())[0]] if v not in matrix]
	cc: UnionFind = UnionFind(verts)
	for i in range(len(partial_sol) - 1):
		cc.unite(partial_sol[i], partial_sol[i + 1])
	edges.sort()
	for w, u, v in edges:
		if cc.find(u) != cc.find(v):
			sol_length += w
			cc.unite(u, v)

	return sol_length

def brute_force_ub(source: VertexT, sinks: set[VertexT], exits: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]], fuel: int) -> list[VertexT]:
	def get_lower_bound(partial_sol: list[VertexT], sol_length: int) -> int:
		return kruskals(partial_sol, sol_length, pair_path_costs)

	def get_upper_bound(partial_sol: list[VertexT], sol_length: int) -> int:
		return sol_length + nearest_neighbour(partial_sol[-1], sinks.difference(curr), exits, pair_path_costs, fuel - len(curr))[1]

	tree = [(0, [source])]
	best_found, ub = nearest_neighbour(source, sinks, exits, pair_path_costs, fuel)

	while len(tree) > 0:
		length, curr = tree.pop()

		if len(curr) == fuel + 1:
			min_cost, min_exit = min([(pair_path_costs[curr[-1]][exit_v], exit_v) for exit_v in exits])
			length += min_cost
			if length < ub:
				best_found = curr + [min_exit]
				ub = length

			continue


		curr_lb = get_lower_bound(curr, length)
		curr_ub = get_upper_bound(curr, length)
		if curr_lb > ub:
			continue

		if curr_ub < ub:
			ub = curr_ub

		for sink in sinks.difference(curr):
			tree.append((length + pair_path_costs[curr[-1]][sink], curr + [sink]))

	return best_found

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

def simplex(A: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray | None:
	"""
	Turns min  cTx:
		 s.t. Ax = b;
			  x >= 0
	Into min  eTz:
		 s.t. Ax + Iz = b;
			  x >= 0;
			  z >= 0
	"""
	e = np.array([[0]] * c.shape[0] + [[1]] * A.shape[0])
	dummy_A = np.block([[A, np.identity(A.shape[0])]])
	artificial_indices = [i for i in range(A.shape[1], A.shape[1] + A.shape[0])]
	dummy_basis = np.array(artificial_indices)
	dummy_initial = np.array([np.hstack(([0] * A.shape[1], b.transpose()[0]))]).transpose()

	dummy, basis = _simplex(dummy_A, b, e, dummy_basis, dummy_initial, np.linalg.inv(dummy_A[:, dummy_basis]), artificial_indices)

	non_artificial_vars = dummy[[i for i in range(e.shape[0]) if e[i] != 1]]

	# we know the problem is solvable, so we're ignoring a case
	# artificial_vars = dummy[[i for i in range(e.shape[0]) if e[i] == 1]].ravel()

	if basis.max() >= A.shape[1]:
		"""bad case"""
		"""hope and pray no cycling <3"""
		for pivrow in range(basis.size):
			if basis[pivrow] > A.shape[1]:
				non_zero_row = [col for col in range(A.shape[1]) if abs(A[pivrow, col]) > 0 and col not in basis]
				if len(non_zero_row) > 0:
					pivcol = non_zero_row[0]
					basis[pivrow] = pivcol
					pivval = A[pivrow, pivcol]
					A[pivrow] = A[pivrow] / pivval
					for irow in range(A.shape[0]):
						if irow != pivrow:
							A[irow] = A[irow] - A[pivrow] * A[irow, pivcol]

		return _simplex(A, b, c, basis, dummy, np.linalg.inv(A[:, basis]))[0]
	else:
		"""good case"""
		return _simplex(A, b, c, basis, non_artificial_vars, np.linalg.inv(A[:, basis]))[0]

def _simplex(A: np.ndarray, b: np.ndarray, c: np.ndarray, basis: np.ndarray, initial: np.ndarray, inv_a_basis: np.ndarray, artificial_rows=None) -> tuple[np.ndarray | None, np.ndarray | None]:
	"""
	Solves min cTx: Ax = b, x >= 0
	"""
	"""https://www.matem.unam.mx/~omar/math340/revised-simplex.html"""
	"""https://people.math.carleton.ca/~kcheung/math/notes/MATH5801/05/5_1_simplex.html"""
	"""https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html"""
	non_basis = np.array([i for i in range(c.size) if i not in basis])
	a_non_basis = A[:, non_basis]
	select_k = c[non_basis].transpose() - c[basis].transpose() @ inv_a_basis @ a_non_basis
	k: int = -1
	max_found: int = 0
	for i in range(select_k.size):
		if select_k[0][i] < max_found:
			k = i
			max_found = select_k[0][i]

	if k == -1:
		"""optimal solution found"""
		return initial, basis
	else:
		k = non_basis[k]

	d = inv_a_basis @ A[:, k]

	initial_basis = initial[basis]

	min_idx = -1
	min_found = float('infinity')
	for i in range(len(initial_basis)):
		if d[i] > 0:
			if initial_basis[i][0] / d[i] < min_found:
				min_found = initial_basis[i][0] / d[i]
				min_idx = i

	if min_idx == -1:
		raise IndexError("not possible")

	t = initial_basis[min_idx][0] / d[min_idx]

	next_x = initial.copy()
	next_x[k] = t

	for i in range(len(basis)):
		next_x[int(basis[i])][0] -= t * d[i]

	inv_E = np.identity(inv_a_basis.shape[1])
	pivot = d[min_idx]

	inv_E[:, min_idx] = -d / pivot
	inv_E[min_idx, min_idx] = 1. / pivot
	next_inv_a_basis = inv_E @ inv_a_basis

	next_basis = basis.copy()
	next_basis[min_idx] = k

	return _simplex(A, b, c, next_basis, next_x, next_inv_a_basis, artificial_rows)

# lower bound by solving dual
def solve_relaxed_lp(entry: VertexT, exits: set[VertexT], supplies: set[VertexT], pair_path_costs: dict[VertexT, dict[VertexT, int]]) -> int:
	# Dual problem started:
	# A = np.array([[1 if i == u or i == v else 0 for i in [entry] + list(supplies) + [exits] + list(supplies)] for u in supplies.union([entry]) for v in supplies.union(exits)])
	# b = np.array([[pair_path_costs[u][v]] for u in supplies.union([entry]) for v in supplies.union(exits)])
	# c = np.ones((1 + len(exits) + 2 * len(supplies), 1))
	#
	# initial = [i for u in supplies.union([entry]) for v in supplies.union(exits)])

	A = np.array(
		[[1 if i == u     else 0 for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v] for i in [entry] + list(supplies)] + \
		[[1 if i == v     else 0 for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v] for i in list(supplies)]
		)

	# I think exit constraint is linearly dependent (n-dash) it is redundant:
	# [[1 if v in exits else 0 for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v]]

	b = np.ones((2 * len(supplies) + 1, 1))
	c = np.array([[pair_path_costs[u][v]] for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v])

	answer = simplex(A, b, c)

	res: int = 0
	mapping = [(u, v) for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v]
	for i, a in enumerate(answer):
		if a[0] > 0:
			edge = mapping[i]
			res += pair_path_costs[edge[0]][edge[1]] * a[0]

	return res


def get_path_from_super_path(super_path: list[VertexT], apsp_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> list[VertexT]:
	res = []
	for i in range(len(super_path) - 1):
		pair_path = apsp_map[super_path[i]][super_path[i + 1]]
		res += pair_path
		if i != len(super_path) - 2:
			res.pop()

	return res

def stage_1(G, entry, exits, supplies, supply_storage, vertex_to_supply_id, found_supply_ids):
	"""Get supplies that could be collected in the graph"""
	supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

	"""Get number of supplies to find"""
	number_of_supplies_to_collect = max(len(supplies), len([i for i in supply_storage if i is not None]))

	"""Get entry/junction -> exit/junction pair paths"""
	prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: dijkstra(wing, list(wing.nodes)[0]) for wing in G[0]}

	"""supplies apsp"""
	apsp_map = get_apsp(G, entry, exits, supplies, prevs)
	apsp_dist_map = get_apsp_dist(G, apsp_map, prevs)
	return apsp_map, apsp_dist_map, number_of_supplies_to_collect

def reconstruct_super_path(super_path, apsp_map, supplies, supply_storage, number_of_supplies_to_collect, vertex_to_supply_id):
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

	return res, supply_storage

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

	apsp_map, apsp_dist_map, number_of_supplies_to_collect = stage_1(G, entry, exits, supplies, supply_storage, vertex_to_supply_id, found_supply_ids)

	"""stage 2"""
	super_path = brute_force(entry, supplies, exits, apsp_dist_map, number_of_supplies_to_collect)

	return reconstruct_super_path(super_path, apsp_map, supplies, supply_storage, number_of_supplies_to_collect, vertex_to_supply_id)
