import heapq
from collections import defaultdict
from itertools import chain
from typing import Generator, Iterable

import networkx as nx


class VertexT:
    pass

WingT = nx.Graph

SupplyID = int

SupplyStorage = tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]


def dfs(g: nx.Graph, source: VertexT) -> dict[VertexT, VertexT | None]:
    prev: dict[VertexT, VertexT | None] = dict({source: None})
    stack: list[VertexT] = [source]

    while len(stack) > 0:
        u = stack.pop()

        for v in g.neighbors(u):
            if v not in prev:
                prev[v] = u
                stack.append(v)

    return prev


def get_path_from_dfs(source: VertexT, sink: VertexT, prev: dict[VertexT, VertexT | None]) -> list[VertexT]:
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


class DpImpl:
    memo: dict[tuple[VertexT, frozenset[VertexT]], tuple[list[VertexT], int]]
    def __init__(self):
        self.__name__ = "dp"

    def __call__(self, entry: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], max_supplies: int):
        self.memo = {}
        self.counter = [0] * (max_supplies + 1)
        res = [entry] + self.dp(entry, supplies, exits, dist_matrix, max_supplies)[0]
        return res

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

        self.counter[fuel] += 1
        self.memo[key] = min_cost_walk, min_cost
        return min_cost_walk, min_cost


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
            pair_path = get_path_from_dfs(u, v, prevs[u_wing])
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
                path = get_path_from_dfs(u, v, prevs[wing])
                res.add_edge(u, v, weight=get_path_length(wing, path))

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
    number_of_supplies_to_collect = min(len(supplies), len([None for i in supply_storage if i is None]))

    """Get entry/junction -> exit/junction pair paths"""
    prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: dfs(wing, list(wing.nodes)[0]) for wing in G[0]}

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

