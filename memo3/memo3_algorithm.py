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
    supplies_ordered: list[VertexT], supply_weights: list[int], supply_priorities: list[int],
    entry_to_supply_distances: dict[VertexT, int], energy_cap: int
) -> list[int]:

    ks, tot = knapsack(
        energy_cap, [supply_priorities[i] for i in range(len(supplies_ordered))],
        [(supply_weights[i] + 2) * entry_to_supply_distances[supplies_ordered[i]] for i in range(len(supplies_ordered))]
    )

    return ks


def knapsack_supplies(supplies: list[VertexT], supply_weights: list[int], supply_priorities: list[int], supplies_in_junction: list[int], entry: VertexT, prevs: list[VertexT], res: list[tuple | VertexT]) -> bool:
    total_weight = sum(supply_weights[s] for s in supplies_in_junction)
    if total_weight < 5:
        return False
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
        for i in range(len(prevs) - 1, -1, -1):
            curr_pos = prevs[i]
            if curr_pos in sack_items:
                for supply_index in sack_items[curr_pos]:
                    curr_w = supply_weights[supply_index]
                    drop_count = 1
                    while curr_sack_weight + curr_w > 5:
                        del_supply_index = curr_extra_supplies.pop()
                        del_pos = prevs[i - drop_count]
                        res.append(del_pos)
                        res.append((-1, supply_weights[del_supply_index], supply_priorities[del_supply_index]))
                        curr_sack_weight -= supply_weights[del_supply_index]
                        supplies[del_supply_index] = del_pos
                        drop_count += 1

                    curr_sack_weight += curr_w
                    res.append(curr_pos)
                    res.append((-2, supply_weights[supply_index], supply_priorities[supply_index]))
            elif curr_pos in supplies:
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

    return True


def get_curr_pos(res, orig):
    for r in reversed(res):
        if r[0] >= 0:
            return r
    return orig


def clear_junction_path(G, supplies, supply_weights, supply_priorities, entry, prevs, inter_wing_path, supply_paths, curr, res) -> bool:
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
                branch_res, trip_done = clear_branch(G, entry, junction_other, n, n_wing, new_branch_prevs, supply_paths, supply_weights, supply_priorities, supplies, new_inter_wing_path)
                if trip_done:
                    return True
                if len(branch_res) > 0:
                    res.append(junction_other)
                    res += branch_res

                    supplies_in_junction = [s for s in supply_paths[new_inter_wing_path] if
                                            supplies[s] is not None and supplies[s] == junction_other]

                    if knapsack_supplies(supplies, supply_weights, supply_priorities, supplies_in_junction, entry, prevs + [junction_other], res):
                        return True

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

            if knapsack_supplies(supplies, supply_weights, supply_priorities, surviving_supplies, entry, prevs, res):
                return True

            if new_inter_wing_path in supply_paths:
                supply_paths[inter_wing_path] |= supply_paths.pop(new_inter_wing_path)

    return False


def clear_branch(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, orig: VertexT, branch: VertexT,
    orig_wing: WingT, prevs: list[VertexT], supply_paths: dict[tuple[VertexT, ...], set[int]],
    supply_weights: list[int], supply_priorities: list[int], supplies: list[VertexT], inter_wing_path: tuple[VertexT, ...]
) -> tuple[list[tuple | VertexT], bool]:
    res = []

    end_branch_pos = branch
    prev = orig
    prevs.append(end_branch_pos)

    if clear_junction_path(G, supplies, supply_weights, supply_priorities, entry, prevs, inter_wing_path, supply_paths, end_branch_pos, res):
        return res, True
    while orig_wing.degree[end_branch_pos] == 2:
        n = list(orig_wing.neighbors(end_branch_pos))
        if n[0] == prev:
            prev = end_branch_pos
            end_branch_pos = n[1]
        else:
            prev = end_branch_pos
            end_branch_pos = n[0]
        prevs.append(end_branch_pos)

        if clear_junction_path(G, supplies, supply_weights, supply_priorities, entry, prevs, inter_wing_path, supply_paths, end_branch_pos, res):
            return res, True

    end_branch_degree = orig_wing.degree[end_branch_pos]
    if end_branch_degree == 3:
        for n in orig_wing.neighbors(end_branch_pos):
            if n == prev:
                continue
            branch_res, trip_done = clear_branch(G, entry, end_branch_pos, n, orig_wing, prevs.copy(), supply_paths, supply_weights, supply_priorities, supplies, inter_wing_path)
            if len(branch_res) > 0:
                res += branch_res
            if trip_done:
                return res, True

    supply_to_collect = list(
        i for i in range(len(supplies)) if supplies[i] in prevs and i in supply_paths[inter_wing_path]
    )

    if knapsack_supplies(supplies, supply_weights, supply_priorities, supply_to_collect, entry, prevs, res):
        return res, True

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

        return res, True

    return res, False


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
        for i in range(len(curr_path) - 1):
            if curr_path[i] in junctions and curr_path[i + 1] == get_other_junction(G, curr_path[i]):
                junction_path.append(curr_path[i])
                junction_path.append(curr_path[i + 1])

        res[tuple(junction_path)].add(s)

    return res


def ember_rescue(
    G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], entry: VertexT, exits: set[VertexT],
    supplies: set[VertexT], supply_weights: dict[VertexT, int], supply_priorities: dict[VertexT, int],
    vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID], budget: int
):
    flat_G = flatten_graph(G)

    entry_prevs = dijkstra(flat_G, entry)
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

    # print(f"supply candidates: {reduced_supplies}")
    # print(f"number of supplies: {len(reduced_supplies)}")
    budget_left = budget
    res = []

    supplies_ordered = list(supplies)
    supply_weights_idx = [supply_weights[s] for s in supplies_ordered]
    supply_priorities_idx = [supply_priorities[s] for s in supplies_ordered]
    entry_supply_paths = {v: reconstruct_path(dijkstra(flat_G, entry), v) for v in supplies_ordered}
    entry_supply_distances = {v: get_path_length(flat_G, entry_supply_paths[v]) for v in supplies_ordered}

    while budget_left > exit_run_cost:
        reduced_supplies_index = reduce_supplies(supplies_ordered, supply_weights_idx, supply_priorities_idx, entry_supply_distances, budget_left - exit_run_cost)
        if len(reduced_supplies_index) == 0:
            break

        reduced_supplies = [supplies_ordered[i] for i in reduced_supplies_index]
        supply_wing_paths = get_supply_wing_paths(G, reduced_supplies, entry_supply_paths)
        super_path = clear_branch(G, entry, entry, list(flat_G.neighbors(entry))[0], get_which_wing(G, entry), [entry], supply_wing_paths, [supply_weights_idx[i] for i in reduced_supplies_index], [supply_priorities_idx[i] for i in reduced_supplies_index], reduced_supplies, tuple())[0]

        curr_supply_locations = supplies_ordered.copy()
        prev_pos = entry
        prev_wing = get_which_wing(G, prev_pos)
        storage = []
        for i in range(len(super_path)):
            curr = super_path[i]
            if curr[0] == -2:
                supply_index = list(filter(lambda x: supply_weights_idx[x] == curr[1] and supply_priorities_idx[x] == curr[2] and x not in storage and curr_supply_locations[x] == prev_pos, range(len(curr_supply_locations))))[-1]
                storage.append(supply_index)
                res.append(curr)
            elif curr[0] == -1:
                supply_index = list(filter(lambda x: supply_weights_idx[x] == curr[1] and supply_priorities_idx[x] == curr[2], storage))[-1]
                storage.remove(supply_index)
                curr_supply_locations[supply_index] = prev_pos
                res.append(curr)
            else:
                curr_wing = get_which_wing(G, curr)
                if curr_wing == prev_wing:
                    append_res = dijkstra_to(curr_wing, prev_pos, curr)[1:]
                else:
                    append_res = dijkstra_to(flat_G, prev_pos, curr)[1:]
                    prev_wing = get_which_wing(G, curr)

                if len(append_res) > 0:
                    budget_left -= flat_G.get_edge_data(prev_pos, append_res[0])["weight"]
                    for j in range(len(append_res) - 1):
                        budget_left -= flat_G.get_edge_data(append_res[j], append_res[j + 1])["weight"]
                    res += append_res

                prev_pos = curr

        if prev_pos != entry:
            e_wing = get_which_wing(G, entry)
            if e_wing == prev_wing:
                append_res = dijkstra_to(e_wing, prev_pos, entry)[1:]
            else:
                append_res = dijkstra_to(flat_G, prev_pos, entry)[1:]

            if len(append_res) > 0:
                budget_left -= flat_G.get_edge_data(prev_pos, append_res[0])["weight"]
                for j in range(len(append_res) - 1):
                    budget_left -= flat_G.get_edge_data(append_res[j], append_res[j + 1])["weight"]
                res += append_res

        for i in range(len(reduced_supplies_index)):
            if reduced_supplies[i] == (0, -1, -1):
                supplies_ordered.pop(reduced_supplies_index[i])
                supply_weights_idx.pop(reduced_supplies_index[i])
                supply_priorities_idx.pop(reduced_supplies_index[i])
            else:
                supplies_ordered[reduced_supplies_index[i]] = reduced_supplies[i]

        entry_supply_paths = {v: reconstruct_path(dijkstra(flat_G, entry), v) for v in supplies_ordered}
        entry_supply_distances = {v: get_path_length(flat_G, entry_supply_paths[v]) for v in supplies_ordered}

    res += exit_run[1:]
    return res
