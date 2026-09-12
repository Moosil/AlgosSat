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


# def bin_pack(weights: list[int], cap: int) -> list[list[int]]:
#     """FFD"""
#     bins = [[]]
#     for w in weights:
#         added = False
#         for b in bins:
#             if sum(b) + w <= cap:
#                 b.append(w)
#                 added = True
#         if not added:
#             bins.append([w])
#
#     return bins


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


def dijkstra_to(g: nx.Graph, source: VertexT, sink: VertexT) -> list[VertexT]:
    dist = {s: float('infinity') for s in g}

    dist[source] = 0

    # visited set replaced update(PQ, v)
    visited = set()

    prev: dict[VertexT, VertexT | None] = {source: None}
    pq = [(0., source)]
    heapq.heapify(pq)
    while len(pq) > 0:
        _, u = heapq.heappop(pq)

        if u == sink:
            return reconstruct_path(prev, sink)

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

    raise RuntimeError("bro how tf did it get here")


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


def reduce_supplies(
    supplies: set[VertexT], supply_weights: dict[VertexT, int], supply_priorities: dict[VertexT, int],
    entry_to_supply_distances: dict[VertexT, int], energy_cap: int
    ) -> list[VertexT]:
    supplies_ordered = list(supplies)

    ks, tot = knapsack(
        energy_cap, [supply_priorities[u] for u in supplies_ordered],
        [(supply_weights[u] + 1) * entry_to_supply_distances[u] for u in supplies_ordered]
        )

    return [supplies_ordered[i] for i in ks]


def knapsack_supplies(
    supplies: list[VertexT], supply_weights: list[int], supplies_in_junction: list[int],
    entry: VertexT, prevs: list[VertexT], res: list[str | VertexT]
    ) -> None:
    total_weight = sum(supply_weights[s] for s in supplies_in_junction)
    while total_weight >= 5:
        sack, sack_weight = knapsack(
            5, [supply_weights[i] for i in supplies_in_junction],
            [supply_weights[i] for i in supplies_in_junction]
            )

        """collect supplies in sack on the way back"""
        sack_items = defaultdict(list)
        for s in sack:
            sack_items[supplies[supplies_in_junction[s]]].append(supplies_in_junction[s])
        curr_weight = 0
        curr_extra_supplies = []

        for i in range(len(prevs) - 1, -1, -1):
            c_prevs = prevs[i]
            if c_prevs in sack_items:
                for supply_i in sack_items[c_prevs]:
                    w = supply_weights[supply_i]
                    drop_i = 1
                    while curr_weight + w > 5:
                        drop_supply_i = curr_extra_supplies.pop()
                        p_prevs = prevs[i - drop_i]
                        res.append(p_prevs)
                        res.append("drop")
                        curr_weight -= supply_weights[drop_supply_i]
                        supplies[drop_supply_i] = p_prevs
                        drop_i += 1

                    curr_weight += w
                    res.append(c_prevs)
                    res.append("pickup")
            elif c_prevs in supplies:
                supply_i = supplies.index(c_prevs)
                w = supply_weights[supply_i]
                if curr_weight + w <= 5:
                    curr_weight += w
                    res.append(c_prevs)
                    res.append("pickup")
                    curr_extra_supplies.append(supply_i)

        res.append(entry)
        for s in sack:
            i = supplies_in_junction[s]
            # order matters
            total_weight -= supply_weights[i]
            supplies[i] = None
            supplies_in_junction.pop(s)
            res.append("drop")
        for s in curr_extra_supplies:
            # order matters
            total_weight -= supply_weights[s]
            supplies[s] = None
            res.append("drop")


def get_curr_pos(res, orig):
    for r in reversed(res):
        if not isinstance(r, str):
            return r
    return orig


def clear_junction_path(G, supplies, supply_weights, entry, prevs, inter_wing_path, supply_paths, curr, res):
    junction_other = None
    for j in G[1]:
        if curr == j[0]:
            junction_other = j[1]
            break
        elif curr == j[1]:
            junction_other = j[0]
            break

    if junction_other is not None and junction_other not in inter_wing_path:
        new_inter_wing_path = tuple(list(inter_wing_path) + [curr, junction_other])
        worth_doing = False
        for k in supply_paths:
            if k[:len(new_inter_wing_path)] == new_inter_wing_path:
                worth_doing = True
                break

        if worth_doing:
            res.append(curr)
            n_wing = get_which_wing(G, junction_other)
            surviving_supplies = []
            for n in n_wing.neighbors(junction_other):
                new_branch_prevs = [junction_other]
                branch_res = clear_branch(
                    G, entry, junction_other, n, n_wing, new_branch_prevs, supply_paths,
                    supply_weights, supplies, new_inter_wing_path
                )
                if len(branch_res) > 0:
                    res.append(junction_other)
                    res += branch_res

                    supplies_in_junction = [s for s in supply_paths[new_inter_wing_path] if
                                            supplies[s] is not None and supplies[s] == junction_other]

                    knapsack_supplies(supplies, supply_weights, supplies_in_junction, entry, prevs, res)

                    if len(supplies_in_junction) > 0:
                        storage = []
                        for s in supplies_in_junction:
                            storage.append(s)
                            res.append("pickup")

                        i = len(prevs) - 1
                        while i >= 0 and len(storage) > 0:
                            if prevs[i] not in supplies:
                                s = storage.pop()
                                supplies[s] = prevs[i]
                                res.append(prevs[i])
                                surviving_supplies.append(s)
                                res.append("drop")
                                if len(storage) == 0:
                                    break
                            i -= 1

                        if i == -1 and len(storage) != 0:
                            c_prevs = prevs[0]
                            res.append(c_prevs)
                            while len(storage) > 0:
                                if c_prevs == entry:
                                    supplies[storage.pop()] = None
                                else:
                                    supplies[storage.pop()] = c_prevs
                                res.append("drop")

                    if len(supplies_in_junction) > 1:
                        res.append(curr)

            knapsack_supplies(supplies, supply_weights, surviving_supplies, entry, prevs, res)

            if new_inter_wing_path in supply_paths:
                supply_paths[inter_wing_path] |= supply_paths.pop(new_inter_wing_path)


def clear_branch(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, orig: VertexT, branch: VertexT,
    orig_wing: WingT, prevs: list[VertexT], supply_paths: dict[tuple[VertexT, ...], set[int]],
    supply_weights: list[int], supplies: list[VertexT], inter_wing_path: tuple[VertexT, ...]
    ) -> list[
    str | VertexT]:
    res = []

    curr = branch
    prev = orig
    prevs.append(curr)

    clear_junction_path(G, supplies, supply_weights, entry, prevs, inter_wing_path, supply_paths, curr, res)
    while orig_wing.degree[curr] == 2:
        n = list(orig_wing.neighbors(curr))
        if n[0] == prev:
            prev = curr
            curr = n[1]
        else:
            prev = curr
            curr = n[0]
        prevs.append(curr)

        clear_junction_path(G, supplies, supply_weights, entry, prevs, inter_wing_path, supply_paths, curr, res)

    degree = orig_wing.degree[curr]
    if degree == 3:
        for n in orig_wing.neighbors(curr):
            if n == prev:
                continue
            branch_res = clear_branch(
                G, entry, curr, n, orig_wing, prevs.copy(), supply_paths, supply_weights,
                supplies, inter_wing_path
                )
            if len(branch_res) > 0:
                res.append(curr)
                res += branch_res

    supplies_in_wing_to_collect = list(
        i for i in range(len(supplies)) if supplies[i] in prevs and i in supply_paths[inter_wing_path]
    )

    knapsack_supplies(supplies, supply_weights, supplies_in_wing_to_collect, entry, prevs, res)

    curr_pos = curr
    storage = []
    supply_vertex_in_wing_to_collect = defaultdict(list)
    for s in supplies_in_wing_to_collect:
        supply_vertex_in_wing_to_collect[supplies[s]].append(s)

    if get_curr_pos(res, orig) != entry and len(res) > 0 and res[-1] == "drop":
        i: int = len(res) - 2
        while i >= 0:
            if not isinstance(res[i], str):
                curr_pos = res[i]
                break
            i -= 1

        unchanged_res = res.copy()
        if curr_pos != curr and curr_pos != entry:
            res.pop(-1)
            drops = len(res) - i
            for j in range(drops):
                res.pop(i)
                storage.append(supply_vertex_in_wing_to_collect[curr_pos].pop())

            i -= 1
            while i >= 0:
                if res[i] == "pickup":
                    break
                elif res[i] == "drop":
                    storage.append(supply_vertex_in_wing_to_collect[res[i - 1]].pop())
                    res.pop(i)
                    i -= 1
                res.pop(i)
                i -= 1

    i: int = len(prevs) - 1
    while i >= 0:
        c_prevs = prevs[i]
        if c_prevs == orig:
            break

        if c_prevs in supply_vertex_in_wing_to_collect:
            c_i = len(supply_vertex_in_wing_to_collect[c_prevs]) - 1
            while c_i >= 0:
                if supply_vertex_in_wing_to_collect[c_prevs][c_i] not in storage:
                    storage.append(supply_vertex_in_wing_to_collect[c_prevs].pop(c_i))
                    res.append(c_prevs)
                    res.append("pickup")
                c_i -= 1

        i -= 1

    while i >= 0 and len(storage) > 0:
        c_prevs = prevs[i]
        if c_prevs not in supplies:
            if c_prevs == entry:
                supplies[storage.pop()] = None
            else:
                supplies[storage.pop()] = c_prevs
            res.append(c_prevs)
            res.append("drop")
            if len(storage) == 0:
                break

        i -= 1

    if i == -1 and len(storage) != 0:
        c_prevs = prevs[0]
        res.append(c_prevs)
        while len(storage) > 0:
            if c_prevs == entry:
                supplies[storage.pop()] = None
            else:
                supplies[storage.pop()] = c_prevs
            res.append("drop")

    return res


def get_supply_wing_paths(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], supplies: list[VertexT],
    entry_to_supply: dict[VertexT, list[VertexT]]
    ) -> dict[tuple[VertexT, ...], set[int]]:
    junctions = set()
    for j in G[1]:
        junctions.add(j[0])
        junctions.add(j[1])

    res = defaultdict(set)
    for s in range(len(supplies)):
        junction_path = []
        curr_path = entry_to_supply[supplies[s]]
        for i in range(len(curr_path)):
            if curr_path[i] in junctions and curr_path[i + 1] == get_other_junction(G, curr_path[i]):
                junction_path.append(curr_path[i])
                junction_path.append(curr_path[i + 1])

        res[tuple(junction_path)].add(s)

    return res


def ember_rescue(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, exits: set[VertexT],
    supplies: set[VertexT], supply_weights: dict[VertexT, int], supply_priorities: dict[VertexT, int],
    vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID], energy_amount: int
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
    reduced_supplies = reduce_supplies(
        supplies, supply_weights, supply_priorities, pair_distances[entry],
        energy_amount - exit_run_cost
        )

    supply_wing_paths = get_supply_wing_paths(G, reduced_supplies, pair_paths[entry])

    # print(f"supply candidates: {reduced_supplies}")
    # print(f"number of supplies: {len(reduced_supplies)}")
    next_v = list(flat_G.neighbors(entry))[0]
    supply_weight_idx = [supply_weights[s] for s in reduced_supplies]
    super_path = clear_branch(
        G, entry, entry, next_v, get_which_wing(G, entry), [entry], supply_wing_paths, supply_weight_idx,
        reduced_supplies, tuple()
        )
    res = super_path
    res = []
    prev_pos = entry
    prev_wing = get_which_wing(G, prev_pos)
    curr_drops = 0
    for i in range(len(super_path)):
        curr = super_path[i]
        if isinstance(curr, str):
            if curr == "drop":
                curr_drops += 1
                res.append(curr)
            if curr == "pickup":
                if curr_drops > 0:
                    for j in range(len(res) - 1, -1, -1):
                        if res[j] == "drop":
                            res.pop(j)
                            break
                    curr_drops -= 1
                else:
                    res.append(curr)
        else:
            curr_wing = get_which_wing(G, curr)
            if curr_wing == prev_wing:
                res += dijkstra_to(curr_wing, prev_pos, curr)[1:]
            else:
                res += dijkstra_to(flat_G, prev_pos, curr)[1:]
                prev_wing = get_which_wing(G, curr)

            prev_pos = curr
            curr_drops = 0

    res += exit_run[1:]
    return res
