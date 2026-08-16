import heapq
from collections import defaultdict
from itertools import chain
from typing import Generator, Iterable

import networkx as nx


class VertexT:
    pass

total_ops = 0
from complexity import Complexity

WingT = nx.Graph

SupplyID = int

SupplyStorage = tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]


def dfs(g: nx.Graph, source: VertexT) -> dict[VertexT, VertexT | None]:
    global total_ops
    visited = set()
    prev: dict[VertexT, VertexT | None] = dict({source: None})
    stack: list[VertexT] = [source]

    total_ops += 3 + Complexity.braced_init()

    while len(stack) > 0:
        total_ops += 3
        u = stack.pop()
        total_ops += 1

        total_ops += Complexity._for(0)
        for v in g.neighbors(u):
            total_ops += 2 + Complexity._if()
            if v not in visited:
                prev[v] = u
                stack.append(v)
                visited.add(v)
                total_ops += 4 + Complexity.braced_init()

    return prev


def get_path_from_dfs(source: VertexT, sink: VertexT, prev: dict[VertexT, VertexT | None]) -> list[VertexT]:
    global total_ops
    left_path = [source]
    right_path = [sink]
    left = source
    right = sink
    total_ops += 4 + Complexity.braced_init()
    while True:
        total_ops += 3 + Complexity._while(lambda x: 0, 0)
        total_ops += 1 + Complexity._if()
        if prev[left] is not None:
            total_ops += 3
            left = prev[left]
            left_path.append(left)

        total_ops += 1 + Complexity._if()
        if prev[right] is not None:
            total_ops += 3
            right = prev[right]
            right_path.append(right)

        rl_idx = len(left_path)
        if right in left_path:
            rl_idx = left_path.index(right) + 1
        total_ops += Complexity._for(rl_idx) + (2 + Complexity._if()) * rl_idx

        if right in left_path:
            total_ops += 3 + Complexity.braced_init() + 2 * len(left_path) + 4 * len(right_path) + Complexity._return()
            right_index = left_path.index(right)
            return left_path[:right_index] + list(reversed(right_path))

        rl_idx = len(left_path)
        if left in right_path:
            rl_idx = right_path.index(right) + 1
        total_ops += Complexity._for(rl_idx) + (2 + Complexity._if()) * rl_idx

        if left in right_path:
            total_ops += 3 + Complexity.braced_init() + 2 * len(left_path) + 3 * len(right_path) + Complexity._return()
            left_index = right_path.index(left)
            return left_path + list(reversed(right_path[:left_index]))


def get_supplies_to_collect(
    supplies: set[VertexT], vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID],
    supply_storage: SupplyStorage
) -> set[VertexT]:
    global total_ops
    total_ops += Complexity.get_supplies_to_collect(len(supplies), len(supply_storage))
    return supplies.difference(
        (s for s in supplies if vertex_to_supply_id[s] in found_supply_ids or vertex_to_supply_id[s] in supply_storage)
    )

def get_vertices_in_wing(wing: WingT, vertices: Iterable[VertexT]) -> Generator[VertexT]:
    return (v for v in vertices if v in wing.nodes)


def get_junctions_in_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], wing: WingT) -> Generator[VertexT]:
    return get_vertices_in_wing(wing, chain(*G[1]))

def get_which_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], vertex: VertexT) -> WingT:
    global total_ops
    total_ops += Complexity.get_which_wing(len(G[0]))
    for g in G[0]:
        if vertex in g.nodes:
            return g
    raise ValueError(f"vertex {vertex} is not in any graph in G")


def reconstruct_path(came_from: dict[VertexT, VertexT | None], e: VertexT) -> list[VertexT]:
    global total_ops
    total_ops += Complexity.reconstruct_path(len(came_from))
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
    prev: dict[VertexT, VertexT | None] = {source: None}

    dist[source] = 0

    # visited set replaced update(PQ, v)
    visited = set()

    pq = [(0., source)]
    heapq.heapify(pq)

    global total_ops
    total_ops += (4 + len(g.nodes) + 1
                + Complexity._for(len(g.nodes)) + 1 + len(g.nodes) * 2
                + Complexity._for(len(g.nodes)) + 1 + len(g.nodes) * 2 + 1)

    total_ops += Complexity._while(lambda x: 0, 0)
    while len(pq) > 0:
        total_ops += Complexity._while(lambda x: 1, 1) + 2
        _, u = heapq.heappop(pq)

        # required for the python heapq that doesn't allow changing priority
        if u in visited:
            continue
        visited.add(u)

        total_ops += 2
        if u in sinks:
            total_ops += 1
            res[u] = reconstruct_path(prev, u)
            total_ops += 3 + Complexity._if()
            if len(res) == len(sinks):
                total_ops += Complexity._return()
                return res

        total_ops += Complexity._for(len(list(g.neighbors(u)))) + Complexity.get_neighbours(len(g.nodes))
        for v in g.neighbors(u):
            w = g.get_edge_data(u, v)["weight"]
            total_ops += 4 + Complexity._if()
            if dist[u] + w < dist[v]:
                total_ops += 6
                prev[v] = u
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))

    return res


def get_path_matrix(g: nx.Graph, entry: VertexT, exits: set[VertexT], supplies: set[VertexT]) -> dict[VertexT, dict[VertexT, list[VertexT]]]:
    global total_ops
    total_ops += 1
    res: dict[VertexT, dict[VertexT, list[VertexT]]] = defaultdict(dict)
    total_ops += Complexity.braced_init() + 1 + Complexity._for(len(supplies) + 1)
    for source in supplies.union([entry]):
        total_ops += 1
        res[source] = dijkstra(g, source, supplies.union(exits))

    total_ops += Complexity._return()
    return res


def get_path_length(g: nx.Graph, path: list[VertexT]) -> int:
    global total_ops
    total_ops += Complexity.get_path_length(len(path))
    return sum(g.get_edge_data(path[i], path[i + 1])["weight"] for i in range(len(path) - 1))


def get_path_cost_matrix(g: nx.Graph, pair_path_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> dict[VertexT, dict[VertexT, int]]:
    global total_ops
    total_ops += 1
    res: dict[VertexT, dict[VertexT, int]] = defaultdict(dict)
    total_ops += 1 + Complexity._for(len(pair_path_map))
    for source, sink_dict in pair_path_map.items():
        total_ops += 3
        total_ops += Complexity._for(len(sink_dict))
        for sink, path in sink_dict.items():
            total_ops += 1
            res[source][sink] = get_path_length(g, path)

    total_ops += Complexity._return()
    return res


class DpImpl:
    memo: dict[tuple[VertexT, frozenset[VertexT]], tuple[list[VertexT], int]]
    def __init__(self):
        self.__name__ = "dp"

    def __call__(self, entry: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], max_supplies: int):
        global total_ops
        self.memo = {}
        self.counter = [0] * (max_supplies + 1)
        res = [entry] + self.dp(entry, supplies, exits, dist_matrix, max_supplies)[0]
        total_ops += 3 + Complexity.braced_init() + Complexity._return() + Complexity._for(len(res)) + len(res)
        return res

    def dp(self, source: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int):
        global total_ops
        total_ops += Complexity.braced_init() + 1 + 1 + Complexity._if()
        key = (source, frozenset(supplies))
        if key in self.memo:
            total_ops += Complexity._return() + 1
            return self.memo[key]

        total_ops += 3 + Complexity._if()
        if fuel == 0:
            total_ops += Complexity._for(len(exits))
            random_sink = list(exits)[0]
            min_cost = dist_matrix[source][random_sink]
            min_cost_walk = [random_sink]
            for sink in exits.difference([random_sink]):
                total_ops += 3
                cost = dist_matrix[source][sink]
                total_ops += 1 + Complexity._if()
                if cost < min_cost:
                    total_ops += 2 + Complexity.braced_init()
                    min_cost_walk = [sink]
                    min_cost = cost
        else:
            total_ops += Complexity._for(len(supplies))
            total_ops += 2 + Complexity.braced_init() + 1
            total_ops += 8 + 1 + Complexity._if()
            random_sink = list(supplies)[0]
            min_cost_walk, min_cost = self.dp(random_sink, supplies.difference([random_sink]), exits, dist_matrix, fuel - 1)
            min_cost_walk = [random_sink] + min_cost_walk
            min_cost += dist_matrix[source][random_sink]
            total_ops += 2 + Complexity.braced_init() + Complexity._for(len(min_cost_walk)) + len(min_cost_walk)
            for supply in supplies.difference([random_sink]):
                total_ops += 2 + Complexity.braced_init() + 1
                total_ops += 8 + 1 + Complexity._if()
                min_walk_through, cost = self.dp(supply, supplies.difference([supply]), exits, dist_matrix, fuel - 1)
                cost += dist_matrix[source][supply]
                if cost < min_cost:
                    total_ops += 2 + Complexity.braced_init() + Complexity._for(len(min_cost_walk)) + len(min_cost_walk)
                    min_cost = cost
                    min_cost_walk = [supply] + min_walk_through

        total_ops += Complexity._return() + 2 * Complexity.braced_init() + 1
        self.counter[fuel] += 1
        self.memo[key] = min_cost_walk, min_cost
        return min_cost_walk, min_cost


def get_F_path_from_H_path(super_path: list[VertexT], apsp_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> list[VertexT]:
    global total_ops
    res = []
    total_ops += 1 + 2 + Complexity._for(len(super_path) - 1)
    for i in range(len(super_path) - 1):
        total_ops += 6
        pair_path = apsp_map[super_path[i]][super_path[i + 1]]
        total_ops += 2 + Complexity._for(len(pair_path) - 1)
        total_ops += (len(pair_path) - 1) * 2
        res += pair_path
        if i != len(super_path) - 2:
            res.pop()

    total_ops += 3 + Complexity._return()
    return res


def get_G_path_from_F_path(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], super_path: list[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> list[VertexT]:
    global total_ops
    res = []
    total_ops += 1 + 2 + Complexity._for(len(super_path) - 1)
    for i in range(len(super_path) - 1):
        total_ops += 5 + 2
        u, v = super_path[i], super_path[i + 1]
        u_wing, v_wing = get_which_wing(G, u), get_which_wing(G, v)
        total_ops += 1 + Complexity._if()
        if u_wing == v_wing:
            pair_path = get_path_from_dfs(u, v, prevs[u_wing])
            total_ops += 1 + 2 + Complexity._for(len(pair_path) - 1) + (len(pair_path) - 1) * 2
            res += pair_path
            res.pop()
        else:
            total_ops += 1
            res.append(u)
    total_ops += 3 + Complexity._return()
    res.append(super_path[-1])
    return res


def get_F(G, entry, supplies, exits, prevs):
    global total_ops
    total_ops += 1 + 2 + Complexity.braced_init()
    total_ops += Complexity._for(len(supplies) + len(exits) + 1) + (len(supplies) + len(exits) + 1)

    res = nx.Graph()
    res.add_node(entry)

    res.add_nodes_from(supplies)

    res.add_nodes_from(exits)

    total_ops += 1 + Complexity._for(len(G[1]))
    for u, v in G[1]:
        total_ops += 7 + 6 + 2 * Complexity.braced_init()
        res.add_node(u)
        res.add_node(v)
        res.add_edge(u, v, weight=1)

    for wing in G[0]:
        total_ops += 1 + 5 + Complexity.braced_init()
        salient_in_wing = list(get_vertices_in_wing(wing, (entry,))) + list(get_vertices_in_wing(wing, exits)) + list(get_vertices_in_wing(wing, supplies)) + list(get_vertices_in_wing(wing, [u for u, _ in G[1]] + [v for _, v in G[1]]))
        total_ops += Complexity._for(len(salient_in_wing))
        for i in range(len(salient_in_wing)):
            total_ops += Complexity._for(len(salient_in_wing))
            for j in range(i + 1, len(salient_in_wing)):
                total_ops += 5 + 3 + 1
                u, v = salient_in_wing[i], salient_in_wing[j]
                path = get_path_from_dfs(u, v, prevs[wing])
                res.add_edge(u, v, weight=get_path_length(wing, path))

    total_ops += Complexity._return()
    return res


def ember_rescue(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]],
    entry: VertexT,
    exits: set[VertexT],
    supplies: set[VertexT],
    supply_storage: SupplyStorage,
    vertex_to_supply_id: dict[VertexT, SupplyID],
    found_supply_ids: set[SupplyID]
) -> tuple[list[VertexT], SupplyStorage, int]:
    global total_ops
    total_ops = 0
    res: list[VertexT]
    """Get supplies that could be collected in the graph"""
    total_ops += 1
    supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

    """Get number of supplies to find"""
    total_ops += (1 + Complexity._for(len(supply_storage)) + len(supply_storage) * (2 * Complexity._if())
                  + len([s for s in supply_storage if s is not None]) * 2)
    total_ops += 2 + Complexity.max()
    number_of_supplies_to_collect = min(len(supplies), len([None for i in supply_storage if i is None]))

    """Get entry/junction -> exit/junction pair paths"""
    total_ops += (1 + Complexity._for(len(G[0])) + len(G[0]) * (3 + Complexity._if())
                  + len([w for w in G[0] if len(w.nodes) > 0])) * 3
    prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: dfs(wing, list(wing.nodes)[0]) for wing in G[0]}

    total_ops += 1
    salient_graph = get_F(G, entry, supplies, exits, prevs)

    """supplies apsp"""
    total_ops += 1
    apsp_map = get_path_matrix(salient_graph, entry, exits, supplies)
    total_ops += 1
    apsp_dist_map = get_path_cost_matrix(salient_graph, apsp_map)

    """stage 2"""
    total_ops += 1
    super_path = DpImpl()(entry, supplies, exits, apsp_dist_map, number_of_supplies_to_collect)

    total_ops += 1
    res = get_F_path_from_H_path(super_path, apsp_map)
    total_ops += 1
    res = get_G_path_from_F_path(G, res, prevs)

    total_ops += 1
    total_ops += (1 + Complexity._for(len(res)) + len(res) * (1 + Complexity._if())
                  + len([v for v in res if v in supplies]))
    total_ops += 1 + Complexity._for(number_of_supplies_to_collect) + number_of_supplies_to_collect
    j: int = 0
    collected_supplies = [v for v in res if v in supplies]
    supply_storage = list(supply_storage)
    for i in range(len(supply_storage)):
        total_ops += 2 + Complexity._if()
        if j >= number_of_supplies_to_collect:
            break
        total_ops += 2 + Complexity._if()
        if supply_storage[i] is None:
            total_ops += 3
            supply_storage[i] = vertex_to_supply_id[collected_supplies[j]]
            j += 1

    total_ops += Complexity._return()
    supply_storage = tuple(supply_storage)

    total_ops += Complexity._return() + Complexity.braced_init()
    return res, supply_storage, total_ops