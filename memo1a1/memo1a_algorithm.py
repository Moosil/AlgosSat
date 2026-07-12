import heapq
from collections import defaultdict
from itertools import chain
from typing import Generator, Iterable

import networkx as nx
import numpy as np


class VertexT:
    pass


WingT = nx.Graph

SupplyID = int

SupplyStorage = tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]


def bfs(g: nx.Graph, source: VertexT) -> dict[VertexT, VertexT | None]:
    dist = {s: float('infinity') for s in g}

    dist[source] = 0

    visited = set()

    prev: dict[VertexT, VertexT | None] = dict({source: None})
    stack: list[VertexT] = [source]
    while len(stack) > 0:
        u = stack.pop()

        if u in visited:
            continue

        visited.add(u)

        for v in g.neighbors(u):
            w = g.get_edge_data(u, v)["weight"]
            if dist[u] + w < dist[v]:
                prev[v] = u
                dist[v] = dist[u] + w
                stack.append(v)

    return prev


def get_path_from_bfs(source: VertexT, sink: VertexT, prev: dict[VertexT, VertexT | None]) -> list[VertexT]:
    left_path = [source]
    right_path = [sink]
    left = source
    right = sink
    while True:
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


def get_new_supply_storage(
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

def reconstruct_path(came_from: dict[VertexT, VertexT | None], e: VertexT) -> list[VertexT]:
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


def get_path_matrix(g: nx.Graph, entry: VertexT, exits: set[VertexT], supplies: set[VertexT]) -> dict[VertexT, dict[VertexT, list[VertexT]]]:
    res: dict[VertexT, dict[VertexT, list[VertexT]]] = defaultdict(dict)
    for source in supplies.union([entry]):
        res[source] = dijkstra(g, source, supplies.union(exits))

    return res


def get_path_length(g: nx.Graph, path: list[VertexT]) -> int:
    return sum(g.get_edge_data(path[i], path[i + 1])["weight"] for i in range(len(path) - 1))


def get_path_cost_matrix(g: nx.Graph, pair_path_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> dict[VertexT, dict[VertexT, int]]:
    res: dict[VertexT, dict[VertexT, int]] = defaultdict(dict)
    for source, sink_dict in pair_path_map.items():
        for sink, path in sink_dict.items():
            res[source][sink] = get_path_length(g, path)

    return res


def nearest_neighbour(source: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int) -> tuple[list[VertexT], int]:
    sinks = supplies.copy()
    res: list[VertexT] = [source]
    cost: int = 0
    curr = source
    while fuel >= 1:
        min_found = list(sinks)[0]
        min_cost = dist_matrix[curr][min_found]
        for sink in sinks:
            curr_cost = dist_matrix[curr][sink]
            if curr_cost < min_cost:
                min_found = sink
                min_cost = curr_cost

        sinks.remove(min_found)
        res.append(min_found)
        curr = min_found
        cost += min_cost
        fuel -= 1

    min_found = list(exits)[0]
    min_cost = dist_matrix[curr][min_found]
    for sink in exits:
        curr_cost = dist_matrix[curr][sink]
        if curr_cost < min_cost:
            min_found = sink
            min_cost = curr_cost

    res.append(min_found)
    cost += min_cost
    return res, cost


def lin_kernighan(source: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int) -> list[VertexT]:
    ub, ub_cost = nearest_neighbour(source, supplies, exits, dist_matrix, fuel)
    supplies = {s for s in supplies if s in ub}
    exits = {x for x in exits if x in ub}
    dist_matrix = {k0: {k1: v1 for k1, v1 in v0.items() if k1 in ub} for k0, v0 in dist_matrix.items() if k0 in ub}
    return _lin_kernighan(source, supplies, exits, dist_matrix, (ub, ub_cost))[0]


def _lin_kernighan(entry: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], ub: tuple[list[VertexT], int]) -> tuple[list[VertexT], int]:
    BACKTRACK_DEPTH = 5
    INFEASIBLE_DEPTH = 2

    def reconstruct_walk_set(edges: set[tuple[VertexT, VertexT]]) -> list[VertexT]:
        edges = edges.copy()
        curr_edge = next(filter(lambda x: x[0] == entry, edges))
        res: list[VertexT] = [entry]

        while len(edges) > 1:
            prev = next(filter(lambda x: x != res[-1], curr_edge))
            res.append(prev)
            edges.remove(curr_edge)
            curr_edge = next(filter(lambda x: x[0] == prev or x[1] == prev, edges))
        res.append(next(filter(lambda x: x != prev, curr_edge)))

        return res

    def symmetric_difference(set0: set, set1: set) -> set:
        return set0.union(set1).difference(set0.intersection(set1))

    def has_alternating(edges0: set[tuple[VertexT, VertexT]], edges1: set[tuple[VertexT, VertexT]]) -> bool:
        edges = symmetric_difference(edges0, edges1)
        try:
            counter = defaultdict(float)
            for u, v in edges:
                counter[u] += 1
                counter[v] += 1

            for v in supplies:
                if counter[v] != 2:
                    return False

            if sum(counter[v] for v in exits) != 1:
                return False

            if counter[entry] != 1:
                return False

            curr_edge = next(filter(lambda x: x[0] == entry, edges))
            res: list[VertexT] = [entry]

            while len(edges) > 1:
                prev = next(filter(lambda x: x != res[-1], curr_edge))
                res.append(prev)
                edges.remove(curr_edge)
                curr_edge = next(filter(lambda x: x[0] == prev or x[1] == prev, edges))

            if next(filter(lambda x: x != prev, list(edges)[0])) not in exits:
                return False

            return True
        except:
            return False

    def get_swap(v0, v1):
        if v1 == entry:
            return v1, v0
        if v0 in exits:
            return v1, v0
        return v0, v1

    for u in supplies:
        dist_matrix[u].pop(u)

    stack: list[tuple[VertexT, int, int]] = [(u, 0, 0) for u in dist_matrix]

    best_walk = {(ub[0][i], ub[0][i + 1]) for i in range(len(ub[0]) - 1)}
    best_swaps: set = set()
    best_gain: int = 1
    savings: int = -best_gain

    while best_gain != 0:
        savings += best_gain
        best_gain = 0
        curr: list[VertexT | None] = [None] * 2 * (len(supplies) + 1 + len(exits))
        while len(stack) > 0:
            u, i, g = stack.pop()
            curr[i] = u
            curr_swaps = {get_swap(curr[j], curr[j + 1]) for j in range(i)}
            if i % 2 == 0:
                if g > 0 and g > best_gain and has_alternating(best_walk, curr_swaps):
                    best_swaps = curr_swaps
                    best_gain = g
                early_ret: int = 2
                if u in exits:
                    for v in dist_matrix[entry]:
                        if v not in exits:
                            if (v, u) in set(best_walk).difference(curr_swaps):
                                if i <= INFEASIBLE_DEPTH or ((v, u) not in best_walk.union(curr_swaps) and has_alternating(best_walk, curr_swaps)):
                                    stack.append((v, i + 1, g + dist_matrix[v][u]))
                                    early_ret -= 1
                                    if early_ret == 0:
                                        break
                else:
                    for v in dist_matrix[u]:
                        if (u, v) in set(best_walk).difference(curr_swaps):
                            if i <= INFEASIBLE_DEPTH or ((u, v) not in best_walk.union(curr_swaps) and has_alternating(best_walk, curr_swaps)):
                                stack.append((v, i + 1, g + dist_matrix[u][v]))
                                early_ret -= 1
                                if early_ret == 0:
                                    break

                    if u != entry:
                        if (entry, u) in set(best_walk).difference(curr_swaps):
                            if i <= INFEASIBLE_DEPTH or ((entry, u) not in best_walk.union(curr_swaps) and has_alternating(best_walk, curr_swaps)):
                                stack.append((entry, i + 1, g + dist_matrix[entry][u]))
            else:
                if u in exits:
                    for v in dist_matrix[entry]:
                        if v not in exits:
                            if g > dist_matrix[v][u] and (v, u) not in best_walk.union(curr_swaps):
                                stack.append((v, i + 1, g - dist_matrix[v][u]))
                else:
                    for v in dist_matrix[u]:
                        if g > dist_matrix[u][v] and (u, v) not in best_walk.union(curr_swaps):
                            stack.append((v, i + 1, g - dist_matrix[u][v]))

                    if u != entry:
                        if g > dist_matrix[entry][u] and (entry, u) not in best_walk.union(curr_swaps):
                            stack.append((entry, i + 1, g - dist_matrix[entry][u]))

            if len(stack) > 0:
                u, j, g = stack[-1]
                if i <= j:
                    if best_gain > 0:
                        best_walk = symmetric_difference(best_walk, best_swaps)
                    elif i > BACKTRACK_DEPTH:
                        while j > BACKTRACK_DEPTH:
                            _, j, _ = stack.pop()

    return reconstruct_walk_set(best_walk), ub[1] - savings


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


def branch_and_bound(source: VertexT, sinks: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int) -> list[VertexT]:
    def get_lower_bound(partial_sol: list[VertexT], sol_length: int) -> int:
        min_sol_length = float('infinity')

        for ex in exits:
            curr_sol_length = 0
            edges = [(dist_matrix[u][v], u, v) for u in dist_matrix for v in dist_matrix[u] if
                     dist_matrix[u][v] != 0 and (v not in exits or v == ex)]
            verts = [u for u in dist_matrix] + [v for v in dist_matrix[list(dist_matrix.keys())[0]] if
                                                v not in dist_matrix and (v not in exits or v == ex)]
            cc: UnionFind = UnionFind(verts)
            for i in range(len(partial_sol) - 1):
                cc.unite(partial_sol[i], partial_sol[i + 1])
            edges.sort()
            assert partial_sol[0] == source, "fuck"
            united = len(partial_sol) - 1
            if united < fuel + 1:
                for w, u, v in edges:
                    if cc.find(u) != cc.find(v):
                        curr_sol_length += w
                        cc.unite(u, v)
                        united += 1
                        if united == fuel + 1:
                            break

            min_sol_length = min(curr_sol_length, min_sol_length)

        return sol_length + min_sol_length

    def get_upper_bound(partial_sol: list[VertexT], sol_length: int) -> int:
        _entry = partial_sol[-1]
        _supplies = sinks.difference(curr)
        _, _ub_cost = nearest_neighbour(_entry, _supplies, exits, dist_matrix, fuel - len(partial_sol) + 1)
        return sol_length + _ub_cost

    tree = [(0, [source])]
    best_found, ub = nearest_neighbour(source, sinks, exits, dist_matrix, fuel)

    while len(tree) > 0:
        length, curr = tree.pop()

        if len(curr) == fuel + 1:
            min_cost, min_exit = min([(dist_matrix[curr[-1]][exit_v], exit_v) for exit_v in exits])
            length += min_cost
            if length <= ub:
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
            tree.append((length + dist_matrix[curr[-1]][sink], curr + [sink]))

    return best_found


def brute_force_recursive(source: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int) -> tuple[list[VertexT], int]:
    min_cost = float('infinity')
    min_cost_walk = None

    if fuel == 0:
        for sink in exits:
            cost = dist_matrix[source][sink]
            if cost < min_cost:
                min_cost_walk = [sink]
                min_cost = cost
    else:
        for supply in supplies:
            min_walk_through, cost = brute_force_recursive(supply, supplies.difference([supply]), exits, dist_matrix, fuel - 1)
            cost += dist_matrix[source][supply]
            if cost < min_cost:
                min_cost = cost
                min_cost_walk = [supply] + min_walk_through

    return min_cost_walk, min_cost


def brute_force(entry: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], max_supplies: int) -> list[VertexT]:
    return [entry] + brute_force_recursive(entry, supplies, exits, dist_matrix, max_supplies)[0]

class DpImpl:
    memo: dict[tuple[VertexT, frozenset[VertexT]], tuple[list[VertexT], int]]
    def __init__(self):
        self.__name__ = "dp"

    def __call__(self, entry: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], max_supplies: int):
        self.memo = {}
        return [entry] + self.dp(entry, supplies, exits, dist_matrix, max_supplies)[0]

    def dp(self, source: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int):
        key = (source, frozenset(supplies))
        if key in self.memo:
            return self.memo[key]

        if fuel == 0:
            random_sink = list(exits)[0]
            min_cost = dist_matrix[source][random_sink]
            min_cost_walk = [random_sink]
            for sink in exits.difference([random_sink]):
                cost = dist_matrix[source][sink]
                if cost < min_cost:
                    min_cost_walk = [sink]
                    min_cost = cost
        else:
            random_sink = list(supplies)[0]
            min_cost_walk, min_cost = self.dp(random_sink, supplies.difference([random_sink]), exits, dist_matrix, fuel - 1)
            min_cost_walk = [random_sink] + min_cost_walk
            min_cost += dist_matrix[source][random_sink]
            for supply in supplies.difference([random_sink]):
                min_walk_through, cost = self.dp(supply, supplies.difference([supply]), exits, dist_matrix, fuel - 1)
                cost += dist_matrix[source][supply]
                if cost < min_cost:
                    min_cost = cost
                    min_cost_walk = [supply] + min_walk_through

        self.memo[key] = min_cost_walk, min_cost
        return min_cost_walk, min_cost

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
def solve_relaxed_lp(entry: VertexT, exits: set[VertexT], supplies: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]]) -> int:
    # Dual problem started:
    # A = np.array([[1 if i == u or i == v else 0 for i in [entry] + list(supplies) + [exits] + list(supplies)] for u in supplies.union([entry]) for v in supplies.union(exits)])
    # b = np.array([[pair_path_costs[u][v]] for u in supplies.union([entry]) for v in supplies.union(exits)])
    # c = np.ones((1 + len(exits) + 2 * len(supplies), 1))
    #
    # initial = [i for u in supplies.union([entry]) for v in supplies.union(exits)])

    A = np.array(
        [[1 if i == u else 0 for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v] for i in [entry] + list(supplies)] + \
        [[1 if i == v else 0 for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v] for i in list(supplies)]
    )

    # I think exit constraint is linearly dependent (n-dash) it is redundant:
    # [[1 if v in exits else 0 for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v]]

    b = np.ones((2 * len(supplies) + 1, 1))
    c = np.array([[dist_matrix[u][v]] for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v])

    answer = simplex(A, b, c)

    res: int = 0
    mapping = [(u, v) for u in [entry] + list(supplies) for v in list(supplies) + list(exits) if u != v]
    for i, a in enumerate(answer):
        if a[0] > 0:
            edge = mapping[i]
            res += dist_matrix[edge[0]][edge[1]] * a[0]

    return res


def get_F_path_from_H_path(super_path: list[VertexT], apsp_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> list[VertexT]:
    res = []
    for i in range(len(super_path) - 1):
        pair_path = apsp_map[super_path[i]][super_path[i + 1]]
        res += pair_path
        if i != len(super_path) - 2:
            res.pop()

    return res


def get_G_path_from_F_path(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], super_path: list[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> list[VertexT]:
    res = []
    for i in range(len(super_path) - 1):
        u, v = super_path[i], super_path[i + 1]
        u_wing, v_wing = get_which_wing(G, u), get_which_wing(G, v)
        if u_wing == v_wing:
            pair_path = get_path_from_bfs(u, v, prevs[u_wing])
            res += pair_path
            res.pop()
        else:
            res.append(u)
    res.append(super_path[-1])
    return res


def get_F(G, entry, supplies, exits, prevs):
    res = nx.Graph()
    res.add_node(entry)

    res.add_nodes_from(supplies)

    res.add_nodes_from(exits)

    for u, v in G[1]:
        res.add_node(u)
        res.add_node(v)
        res.add_edge(u, v, weight=1)

    for wing in G[0]:
        salient_in_wing = list(get_vertices_in_wing(wing, (entry,))) + list(get_vertices_in_wing(wing, exits)) + list(get_vertices_in_wing(wing, supplies)) + list(get_vertices_in_wing(wing, [u for u, _ in G[1]] + [v for _, v in G[1]]))
        for i in range(len(salient_in_wing)):
            for j in range(i + 1, len(salient_in_wing)):
                u, v = salient_in_wing[i], salient_in_wing[j]
                path = get_path_from_bfs(u, v, prevs[wing])
                res.add_edge(u, v, weight=get_path_length(wing, path))

    return res


def stage_1(G, entry, supplies, exits, supply_storage, vertex_to_supply_id, found_supply_ids):
    """Get supplies that could be collected in the graph"""
    supplies = get_new_supply_storage(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

    """Get number of supplies to find"""
    number_of_supplies_to_collect = min(len(supplies), len([None for i in supply_storage if i is None]))

    """Get entry/junction -> exit/junction pair paths"""
    prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: bfs(wing, list(wing.nodes)[0]) for wing in G[0]}

    salient_graph = get_F(G, entry, supplies, exits, prevs)

    """supplies apsp"""
    apsp_map = get_path_matrix(salient_graph, entry, exits, supplies)
    apsp_dist_map = get_path_cost_matrix(salient_graph, apsp_map)

    return apsp_map, apsp_dist_map, prevs, supplies, number_of_supplies_to_collect


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
    supplies = get_new_supply_storage(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

    """Get number of supplies to find"""
    number_of_supplies_to_collect = min(len(supplies), len([None for i in supply_storage if i is None]))

    """Get entry/junction -> exit/junction pair paths"""
    prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: bfs(wing, list(wing.nodes)[0]) for wing in G[0]}

    salient_graph = get_F(G, entry, supplies, exits, prevs)

    """supplies apsp"""
    apsp_map = get_path_matrix(salient_graph, entry, exits, supplies)
    apsp_dist_map = get_path_cost_matrix(salient_graph, apsp_map)

    """stage 2"""
    super_path = DpImpl()(entry, supplies, exits, apsp_dist_map, number_of_supplies_to_collect)

    res = get_F_path_from_H_path(super_path, apsp_map)
    res = get_G_path_from_F_path(G, res, prevs)

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
