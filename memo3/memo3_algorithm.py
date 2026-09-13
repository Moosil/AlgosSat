import heapq
import itertools
from collections import defaultdict
from typing import Generator, Iterable

import networkx as nx

VertexT = tuple[int, int, int]

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
    g, supplies: set[VertexT], supply_weights: dict[VertexT, int], supply_priorities: dict[VertexT, int],
    entry_paths: dict[VertexT, list[VertexT]], budget: int
) -> list[VertexT]:
    supply_distances = {v: get_path_length(g, entry_paths[v]) for v in supplies}
    supplies_ordered = list(supplies)

    def get_weight_cost(weight: int) -> int:
        if weight >= 3:
            return int(4 * weight + 2 * 3.5)
        if weight == 2:
            return int(4 * weight + 2 * 2.5)
        if weight == 1:
            return int(4 * weight + 2 * 2.5)
        raise RuntimeError(f"invalid weight")

    ks, tot = knapsack(
        4 * budget, [supply_priorities[u] for u in supplies_ordered],
        [get_weight_cost(supply_weights[u]) * supply_distances[u] for u in supplies_ordered]
    )

    return [supplies_ordered[i] for i in ks]


def knapsack_supplies(supplies: list[VertexT], supply_weights: list[int], supply_priorities: list[int], supplies_in_junction: list[int], entry: VertexT, prevs: list[VertexT], res: list[tuple | VertexT]) -> None:
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
        curr_sack_weight = 0
        curr_extra_supplies = []
        collecting_strays = False
        for i in range(len(prevs) - 1, -1, -1):
            curr_pos = prevs[i]
            if curr_pos in sack_items:
                collecting_strays = True
                for supply_index in sack_items[curr_pos]:
                    curr_w = supply_weights[supply_index]
                    drop_count = 1
                    while curr_sack_weight + curr_w > 5:
                        del_supply_index = curr_extra_supplies.pop()
                        del_pos = prevs[i + drop_count]
                        res.append(del_pos)
                        res.append((-1, supply_weights[del_supply_index], supply_priorities[del_supply_index]))
                        curr_sack_weight -= supply_weights[del_supply_index]
                        supplies[del_supply_index] = del_pos
                        drop_count += 1

                    curr_sack_weight += curr_w
                    res.append(curr_pos)
                    res.append((-2, supply_weights[supply_index], supply_priorities[supply_index]))
            elif collecting_strays and curr_pos in supplies and supplies.index(curr_pos) in supplies_in_junction:
                supply_index = supplies.index(curr_pos)
                curr_weight = supply_weights[supply_index]
                if curr_sack_weight + curr_weight <= 5:
                    curr_sack_weight += curr_weight
                    res.append(curr_pos)
                    res.append((-2, supply_weights[supply_index], supply_priorities[supply_index]))
                    curr_extra_supplies.append(supply_index)

        res.append(entry)
        for i in sack:
            s = supplies_in_junction[i]
            # order matters
            supplies[s] = (0, -1, -1)
            supplies_in_junction.pop(i)
            total_weight -= supply_weights[s]
            res.append((-1, supply_weights[s], supply_priorities[s]))
        for s in curr_extra_supplies:
            supplies[s] = (0, -1, -1)
            total_weight -= supply_weights[s]
            res.append((-1, supply_weights[s], supply_priorities[s]))


def get_curr_pos(res, orig):
    for r in reversed(res):
        if r[0] >= 0:
            return r
    return orig


def clear_junction_path(G, supplies, supply_weights, supply_priorities, entry, prevs, inter_wing_path, supply_paths, curr, res):
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
                branch_res = clear_branch(G, entry, junction_other, n, n_wing, new_branch_prevs, supply_paths, supply_weights, supply_priorities, supplies, new_inter_wing_path)
                if len(branch_res) > 0:
                    res.append(junction_other)
                    res += branch_res

                    supplies_in_junction = [s for s in supply_paths[new_inter_wing_path] if
                                            supplies[s] is not None and supplies[s] == junction_other]

                    knapsack_supplies(supplies, supply_weights, supply_priorities, supplies_in_junction, entry, prevs + [junction_other], res)

                    if len(supplies_in_junction) > 0:
                        storage = []
                        for s in supplies_in_junction:
                            storage.append(s)
                            res.append(junction_other)
                            res.append((-2, supply_weights[s], supply_priorities[s]))

                        i = len(prevs) - 1
                        while i >= 0 and len(storage) > 0:
                            if prevs[i] not in supplies:
                                supply_index = storage.pop()
                                supplies[supply_index] = prevs[i]
                                res.append(prevs[i])
                                surviving_supplies.append(supply_index)
                                res.append((-1, supply_weights[supply_index], supply_priorities[supply_index]))
                                if len(storage) == 0:
                                    break
                            i -= 1

                        if i == -1 and len(storage) != 0:
                            c_prevs = prevs[0]
                            res.append(c_prevs)
                            while len(storage) > 0:
                                supply_index = storage.pop()
                                if c_prevs == entry:
                                    supplies[supply_index] = None
                                else:
                                    supplies[supply_index] = c_prevs
                                res.append((-1, supply_weights[supply_index], supply_priorities[supply_index]))

                    if len(supplies_in_junction) > 1:
                        res.append(curr)

            knapsack_supplies(supplies, supply_weights, supply_priorities, surviving_supplies, entry, prevs, res)

            if new_inter_wing_path in supply_paths:
                supply_paths[inter_wing_path] |= supply_paths.pop(new_inter_wing_path)


def clear_branch(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, orig: VertexT, branch: VertexT,
    orig_wing: WingT, prevs: list[VertexT], supply_paths: dict[tuple[VertexT, ...], set[int]],
    supply_weights: list[int], supply_priorities: list[int], supplies: list[VertexT], inter_wing_path: tuple[VertexT, ...]
) -> list[tuple | VertexT]:
    res = []

    end_branch_pos = branch
    prev = orig
    prevs.append(end_branch_pos)

    clear_junction_path(G, supplies, supply_weights, supply_priorities, entry, prevs, inter_wing_path, supply_paths, end_branch_pos, res)
    while orig_wing.degree[end_branch_pos] == 2:
        n = list(orig_wing.neighbors(end_branch_pos))
        if n[0] == prev:
            prev = end_branch_pos
            end_branch_pos = n[1]
        else:
            prev = end_branch_pos
            end_branch_pos = n[0]
        prevs.append(end_branch_pos)

        clear_junction_path(G, supplies, supply_weights, supply_priorities, entry, prevs, inter_wing_path, supply_paths, end_branch_pos, res)

    end_branch_degree = orig_wing.degree[end_branch_pos]
    if end_branch_degree >= 3:
        for n in orig_wing.neighbors(end_branch_pos):
            if n == prev:
                continue
            branch_res = clear_branch(G, entry, end_branch_pos, n, orig_wing, prevs.copy(), supply_paths, supply_weights, supply_priorities, supplies, inter_wing_path)
            if len(branch_res) > 0:
                res += branch_res

    supply_to_collect = list(
        i for i in range(len(supplies)) if supplies[i] in prevs and i in supply_paths[inter_wing_path]
    )

    knapsack_supplies(supplies, supply_weights, supply_priorities, supply_to_collect, entry, prevs, res)

    curr_pos = end_branch_pos
    storage = []
    vertex_to_collect = defaultdict(list)
    for s in supply_to_collect:
        vertex_to_collect[supplies[s]].append(s)

    if get_curr_pos(res, orig) != entry and len(res) > 0 and res[-1][0] == -1:
        i: int = len(res) - 2
        while i >= 0:
            if res[i][0] >= 0:
                curr_pos = res[i]
                break
            i -= 1

        if curr_pos != end_branch_pos and curr_pos != entry:
            for j in range(len(res) - i - 1):
                _, weight, priority = res.pop(i + 1)
                added = False
                for k in range(len(vertex_to_collect[curr_pos])):
                    supply_index = vertex_to_collect[curr_pos][k]
                    if supply_weights[supply_index] == weight and supply_priorities[supply_index] == priority:
                        storage.append(supply_index)
                        vertex_to_collect[curr_pos].pop(k)
                        added = True
                        break
                assert added, f"no supply with weight {weight} and priority {priority} was found in {vertex_to_collect[curr_pos]} (at {curr_pos})"

            res.pop(i)

            i -= 1
            while i >= 0:
                if res[i][0] == -2:
                    break
                elif res[i][0] == -1:
                    curr_pos = res[i - 1]
                    _, weight, priority = res.pop(i)
                    added = False
                    for j in range(len(vertex_to_collect[curr_pos])):
                        supply_index = vertex_to_collect[curr_pos][j]
                        if supply_weights[supply_index] == weight and supply_priorities[supply_index] == priority:
                            storage.append(supply_index)
                            added = True
                            break
                    assert added, f"no supply with weight {weight} and priority {priority} was found in {vertex_to_collect[curr_pos]} (at {curr_pos})"
                    i -= 1
                res.pop(i)
                i -= 1

    i: int = len(prevs) - 1
    while i >= 0:
        curr_pos = prevs[i]
        if curr_pos == orig:
            break

        if curr_pos in vertex_to_collect:
            j = len(vertex_to_collect[curr_pos]) - 1
            while j >= 0:
                if vertex_to_collect[curr_pos][j] not in storage:
                    supply_index = vertex_to_collect[curr_pos].pop(j)
                    storage.append(supply_index)
                    res.append(curr_pos)
                    res.append((-2, supply_weights[supply_index], supply_priorities[supply_index]))
                j -= 1

        i -= 1

    while i >= 0 and len(storage) > 0:
        curr_pos = prevs[i]
        if curr_pos not in supplies:
            supply_index = storage.pop()
            if curr_pos == entry:
                supplies[supply_index] = (0, -1, -1)
            else:
                supplies[supply_index] = curr_pos
            res.append(curr_pos)
            res.append((-1, supply_weights[supply_index], supply_priorities[supply_index]))
            if len(storage) == 0:
                break

        i -= 1

    if i == -1 and len(storage) != 0:
        curr_pos = prevs[0]
        res.append(curr_pos)
        while len(storage) > 0:
            supply_index = storage.pop()
            if curr_pos == entry:
                supplies[supply_index] = (0, -1, -1)
            else:
                supplies[supply_index] = curr_pos
            res.append((-1, supply_weights[supply_index], supply_priorities[supply_index]))

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


def get_supplies_to_collect(
    supplies: set[VertexT], vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID]
) -> set[VertexT]:
    return supplies.difference(
        (s for s in supplies if vertex_to_supply_id[s] in found_supply_ids)
    )


def ember_rescue(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, exits: set[VertexT],
    supplies: set[VertexT], supply_weights: dict[VertexT, int], supply_priorities: dict[VertexT, int],
    vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID], energy_amount: int
):
    supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids)

    flat_G = flatten_graph(G)
    entry_prevs = dijkstra(flat_G, entry)
    entry_paths = {v: reconstruct_path(entry_prevs, v) for v in supplies}

    exit_run = reconstruct_path(entry_prevs, list(exits)[0])
    exit_run_cost = get_path_length(flat_G, exit_run)
    for ex in exits:
        if ex == exit_run[-1]:
            continue
        curr = reconstruct_path(entry_prevs, ex)
        curr_cost = get_path_length(flat_G, curr)
        if curr_cost < exit_run_cost:
            exit_run = curr
            exit_run_cost = curr_cost

    """knapsack problem on the possible runs"""
    reduced_supplies = reduce_supplies(flat_G, supplies, supply_weights, supply_priorities, entry_paths, energy_amount - exit_run_cost)

    supply_wing_paths = get_supply_wing_paths(G, reduced_supplies, entry_paths)

    # print(f"supply candidates: {reduced_supplies}")
    # print(f"number of supplies: {len(reduced_supplies)}")
    super_path = clear_branch(G, entry, entry, list(flat_G.neighbors(entry))[0], get_which_wing(G, entry), [entry], supply_wing_paths, [supply_weights[s] for s in reduced_supplies], [supply_priorities[s] for s in reduced_supplies], reduced_supplies, tuple())
    res = []
    prev_pos = entry
    for i in range(len(super_path)):
        curr = super_path[i]
        if curr[0] < 0:
            res.append(curr)
        else:
            res += dijkstra_to(flat_G, prev_pos, curr)[1:]
            prev_pos = curr

    if prev_pos != entry:
        res += dijkstra_to(flat_G, prev_pos, entry)[1:]
    res += exit_run[1:]
    return res
