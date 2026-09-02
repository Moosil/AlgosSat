import heapq
import itertools
from collections import defaultdict
from typing import Generator, Iterable

import networkx as nx


class VertexT:
    pass


WingT = nx.Graph

SupplyID = int

"""https://www.geeksforgeeks.org/dsa/0-1-knapsack-problem-dp-10/#space-optimized-approach-on-x-w-time-and-ow-space"""


def knapsack(cap: int, val: list[int], wt: list[int]) -> tuple[list[int], int]:
    """
    Solves the 0-1 knapsack problem
    W: capacity
    val: value
    wt: weight
    """

    # Initializing dp list
    dp = [0] * (cap + 1)
    old_res = [[]] * (cap + 1)
    new_res = [[]] * (cap + 1)

    # Taking first i elements
    for i in range(len(wt)):

        # Starting from back, so that we also have data of
        # previous computation of i-1 items
        for j in range(cap, wt[i] - 1, -1):
            curr = dp[j - wt[i]] + val[i]
            if dp[j] < curr:
                dp[j] = curr
                new_res[j] = [i] + old_res[j - wt[i]]

        old_res = new_res

    return old_res[cap], dp[cap]

def bin_pack(sizes: list[int], count: list[int], cap: int) -> list[list[int]]:
    """FFD"""
    bins = [[]]
    for i, s in enumerate(sizes):
        count[i] -= 1
        added = False
        for b in bins:
            if sum(b) + s <= cap:
                b.append(s)
                added = True
        if not added:
            bins.append([s])

    return bins




def get_path_length(g: nx.Graph, path: list[VertexT]) -> int:
    return sum(g.get_edge_data(path[i], path[i + 1])["weight"] for i in range(len(path) - 1))


def get_which_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], vertex: VertexT) -> WingT:
    for g in G[0]:
        if vertex in g.nodes:
            return g
    raise ValueError(f"vertex {vertex} is not in any graph in G")


def get_vertices_in_wing(wing: WingT, vertices: Iterable[VertexT]) -> Generator[VertexT]:
    return (v for v in vertices if v in wing.nodes)


def get_junctions_in_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], wing: WingT) -> Generator[VertexT]:
    return get_vertices_in_wing(wing, itertools.chain(*G[1]))


def get_other_junction(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], j: VertexT):
    res = [v for v in G[1] if v[0] == j or v[1] == j][0]
    if res[0] == j:
        return res[1]
    else:
        return res[0]


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


def reconstruct_path(came_from: dict[VertexT, VertexT | None], e: VertexT) -> list[VertexT]:
    res = []
    curr = e
    while curr in came_from:
        res.append(curr)
        curr = came_from[curr]
    res.reverse()
    return res


def dijkstra(g: nx.Graph, source: VertexT) -> dict[VertexT, VertexT | None]:
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

        for v in g.neighbors(u):
            w = g.get_edge_data(u, v)["weight"]
            if dist[u] + w < dist[v]:
                prev[v] = u
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))

    return prev


def flatten_graph(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]]) -> nx.Graph:
    res = nx.Graph()
    for wing in G[0]:
        for v in wing.nodes:
            res.add_node(v)
        for (u, v, w) in wing.edges.data("weight", default=1):
            res.add_edge(u, v, weight=w)
    for ju, jv in G[1]:
        res.add_edge(ju, jv, weight=1)
    return res


def reduce_supplies(supplies: set[VertexT], supply_weights: dict[VertexT, int], supply_priorities: dict[VertexT, int], entry_to_supply_distances: dict[VertexT, int], energy_cap: int) -> list[VertexT]:
    supplies_ordered = list(supplies)

    ks, tot = knapsack(energy_cap, [supply_priorities[u] for u in supplies_ordered], [(supply_weights[u] + 1) * entry_to_supply_distances[u] for u in supplies_ordered])

    return [supplies_ordered[i] for i in ks]


def pack_supplies(to_pack: dict[int, list[VertexT]]) -> list[list[VertexT]]:
    sizes = list(sorted(to_pack.keys()))
    packs = bin_pack(sizes, [len(to_pack[s]) for s in sizes], 5)
    res = []
    for pack in packs:
        curr = []
        for w in pack:
            curr.append(to_pack[w].pop())
        res.append(curr)
    return res


def clear_branch(g: nx.Graph, entry: VertexT, supplies_to_collect: dict[VertexT, int]):
    res = []

    prevs: dict[VertexT, tuple[VertexT, int]]

    stack = [(list(g.neighbors(entry))[0], [entry])]

    while len(stack) > 0:
        curr, branch_prevs = stack.pop(0)
        new_branch_prevs = branch_prevs.copy()

        prev = branch_prevs[-1]
        supplies_on_path = defaultdict(list[VertexT])
        while g.degree[curr] == 2:
            new_branch_prevs.append(curr)
            n: list | VertexT = list(g.neighbors(curr))
            if n[0] == prev:
                n = n[1]
            else:
                n = n[0]

            prev = curr
            curr = n
            if curr in supplies_to_collect:
                supplies_on_path[supplies_to_collect[curr]].append(curr)

        new_branch_prevs.append(curr)
        if curr in supplies_to_collect:
            supplies_on_path[supplies_to_collect[curr]].append(curr)
        if g.degree[curr] == 1:
            runs = pack_supplies(supplies_on_path)
            filled_w_supplies = 1
            for run in runs:
                if sum(supplies_to_collect[s] for s in run) == 5:
                    res.append((run, [branch_prevs[0]] * len(run)))
                else:
                    new_vertices = []
                    for i in range(len(run)):
                        new_vertex = branch_prevs[-filled_w_supplies - i]
                        while new_vertex in supplies_to_collect:
                            filled_w_supplies += 1
                            new_vertex = branch_prevs[-filled_w_supplies - i]
                        supplies_to_collect[new_vertex] = supplies_to_collect.pop(run[i])
                        new_vertices.append(new_vertex)
                    res.append(([r for r in run], new_vertices))
                    filled_w_supplies += len(run)

            ordered = list(set(new_branch_prevs).intersection(supplies_to_collect))
            ks, tot = knapsack(5, [supplies_to_collect[s] for s in ordered], [supplies_to_collect[s] for s in ordered])
            while tot == 5:
                res.append(([ordered[k] for k in ks], [branch_prevs[0]] * len(ks)))
                for k in ks:
                    supplies_to_collect.pop(ordered[k])
                ordered = list(set(new_branch_prevs).intersection(supplies_to_collect))
                ks, tot = knapsack(5, [supplies_to_collect[s] for s in ordered], [supplies_to_collect[s] for s in ordered])
        else:
            ordered = list(set(new_branch_prevs).intersection(supplies_to_collect))
            ks, tot = knapsack(5, [supplies_to_collect[s] for s in ordered], [supplies_to_collect[s] for s in ordered])
            while tot == 5:
                res.append(([ordered[k] for k in ks], [branch_prevs[0]] * len(ks)))
                for k in ks:
                    supplies_to_collect.pop(ordered[k])
                ordered = list(set(new_branch_prevs).intersection(supplies_to_collect))
                ks, tot = knapsack(5, [supplies_to_collect[s] for s in ordered], [supplies_to_collect[s] for s in ordered])

            for n in g.neighbors(curr):
                if n in new_branch_prevs:
                    continue
                stack.append((n, new_branch_prevs))

    return res


def ember_rescue(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]],
    entry: VertexT,
    exits: set[VertexT],
    supplies: set[VertexT],
    supply_weights: dict[VertexT, int],
    supply_priorities: dict[VertexT, int],
    vertex_to_supply_id: dict[VertexT, SupplyID],
    found_supply_ids: set[SupplyID],
    energy_amount: int
    ):

    flat_G = flatten_graph(G)
    salient = list(supplies) + [entry] + list(exits)
    prevs = {v: dijkstra(flat_G, v) for v in salient}
    pair_paths = {u: {v: reconstruct_path(prevs[u], v) for v in salient if v != u} for u in salient}
    pair_distances = {u: {v: get_path_length(flat_G, pair_paths[u][v]) for v in salient if v != u} for u in salient}

    exit_run = reconstruct_path(prevs[entry], list(exits)[0])
    exit_run_cost = get_path_length(flat_G, exit_run)
    for ex in exits:
        if ex == exit_run[-1]:
            continue
        curr = reconstruct_path(prevs[entry], ex)
        curr_cost = get_path_length(flat_G, curr)
        if curr_cost < exit_run_cost:
            exit_run = curr
            exit_run_cost = curr_cost

    """knapsack problem on the possible runs"""
    reduced_supplies = reduce_supplies(supplies, supply_weights, supply_priorities, pair_distances[entry], energy_amount - exit_run_cost)

    def pretty_string(run: tuple[list[VertexT], list[VertexT]]) -> str:
        return f"{", ".join(str(i) for i in run[0])} -> {", ".join(str(i) for i in run[1])}"

    def pretty_print(runs) -> None:
        for run in runs:
            if len(run[0]) == 0:
                continue

            print(pretty_string(run)) #  + f" weight total: {sum([supply_weights[s] for s in run[0]])}"

    print(f"total supply candidates: {len(reduced_supplies)}")
    print(f"number of weight 1 supplies: {len(list(filter(lambda x: supply_weights[x] == 1, reduced_supplies)))}")
    pretty_print(clear_branch(flat_G, entry, {s: supply_weights[s] for s in reduced_supplies}))
