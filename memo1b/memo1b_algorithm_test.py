import cProfile
import copy
import csv
import math
import pstats
import random
import sys
import tracemalloc
from itertools import chain
from pstats import SortKey

import networkx as nx
from tqdm import trange

sys.path.append('../AlgosSat')
from memo1 import memo1_algorithm
import memo1b_algorithm


class GraphDrawer:
    def __init__(self, seed, supply_count: int | None = None) -> None:
        self.WING_COLS, self.WING_ROWS = 10, 10

        self.n_wings, self.wings, self.entry, self.exit_a, self.exit_b, self.supplies, self.junctions = self._get_multi_wing_facility(
            seed, supply_count
        )

    @staticmethod
    def _neighbours(cols, rows, c, r):
        for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < cols and 0 <= nr < rows:
                yield nc, nr

    @staticmethod
    def _build_wing(cols, rows, rng):
        """Build a single-wing maze as a spanning tree of the grid."""
        visited = [[False] * rows for _ in range(cols)]
        g = nx.Graph()
        for c in range(cols):
            for r in range(rows):
                g.add_node((c, r))

        def carve(c, r):
            visited[c][r] = True
            dirs = list(GraphDrawer._neighbours(cols, rows, c, r))
            rng.shuffle(dirs)
            for nc, nr in dirs:
                if not visited[nc][nr]:
                    g.add_edge((c, r), (nc, nr), weight=1)
                    carve(nc, nr)

        carve(0, 0)
        return g

    def get_abstracted_graph(self) -> tuple[set[nx.Graph], set[tuple]]:
        wings = set()
        for i in range(self.n_wings):
            wing: nx.Graph = copy.deepcopy(self.wings[i])
            for u, d in self.wings[i].degree:
                w_u = tuple([i] + list(u))
                if d == 2 and w_u not in self.supplies and w_u not in {
                    self.exit_a, self.exit_b,
                    self.entry
                } and w_u not in set(
                    chain(*self.junctions)
                ):
                    n0 = list(wing.neighbors(u))[0]
                    n1 = list(wing.neighbors(u))[1]
                    w = wing.get_edge_data(u, n0)["weight"] + wing.get_edge_data(u, n1)["weight"]
                    wing.remove_node(u)
                    wing.add_edge(n0, n1, weight=w)
            wing = nx.relabel_nodes(wing, lambda x: tuple([i] + list(x)))
            wings.add(wing)

        return wings, set(self.junctions)

    def get_path_from_super_path(self, path: list) -> list:
        res = []
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            if u[0] == v[0]:
                res += [tuple([u[0]] + list(w)) for w in
                        nx.shortest_path(self.wings[u[0]], source=u[1:], target=v[1:], weight="weight")]
                res.pop()
            else:
                res.append(u)
        res.append(path[-1])
        return res

    def _get_multi_wing_facility(self, seed, supply_count=None):
        int_seed = int(seed)
        if supply_count is None:
            n_wings = 2 + (int_seed % 3)  # 2, 3, or 4 wings from seed
            supply_count = 5
        else:
            n_wings = math.ceil(supply_count / 2)

        # Build each wing from a deterministic derived seed
        wings = []
        for w in range(n_wings):
            wrng = random.Random(int_seed * 31 + w * 7919)
            wings.append(self._build_wing(self.WING_COLS, self.WING_ROWS, wrng))

        # Inter-wing junctions: 2 corridors per adjacent wing pair
        # Each junction connects (w, WING_COLS-1, r) to (w+1, 0, r)
        junctions = []
        for w in range(n_wings - 1):
            jrng = random.Random(int_seed * 17 + w * 5003)
            rows_avail = list(range(2, self.WING_ROWS - 2))
            jrng.shuffle(rows_avail)
            r1, r2 = sorted(rows_avail[:2])
            junctions.append(((w, self.WING_COLS - 1, r1), (w + 1, 0, r1)))
            junctions.append(((w, self.WING_COLS - 1, r2), (w + 1, 0, r2)))

        # Fixed entry and exits
        entry = (0, 0, 0)
        exit_a = (n_wings - 1, self.WING_COLS - 1, self.WING_ROWS - 1)
        exit_b = (n_wings - 1, self.WING_COLS - 1, 0)

        # Supply placement: spread across wings, prefer dead-end nodes
        srng = random.Random(int_seed * 13 + 42)
        reserved = {entry, exit_a, exit_b}
        for n1, n2 in junctions:
            reserved.add(n1)
            reserved.add(n2)

        # Collect dead-end candidates per wing
        per_wing_cands = []
        for w, wg in enumerate(wings):
            de = [
                (w, c, r) for (c, r) in wg.nodes()
                if wg.degree((c, r)) == 1 and (w, c, r) not in reserved
            ]
            srng.shuffle(de)
            per_wing_cands.append(de)

        # Round-robin: up to 2 supplies per wing, 5 total
        supplies = []
        for _ in range(2):
            for wl in per_wing_cands:
                if len(supplies) >= supply_count:
                    break
                for n in wl:
                    if n not in supplies:
                        supplies.append(n)
                        break
            if len(supplies) >= supply_count:
                break

        return n_wings, wings, entry, exit_a, exit_b, supplies[:supply_count], junctions


def get_runtime(test_func):
    pr = cProfile.Profile()
    pr.enable()

    res = test_func()

    pr.disable()
    sortby = SortKey.CUMULATIVE
    ps = pstats.Stats(pr).sort_stats(sortby)
    return ps.stats[tuple(next(s for s in ps.stats if 'ember_rescue' in s))][3], res


def get_mem(test_func):
    tracemalloc.start()

    res = test_func()

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('filename')
    return sum(stat.size for stat in top_stats if "memo1a_algorithm.py" in stat.traceback._frames[0][0]), res


def run_test(test_func, facility_drawer):
    run_time, res = get_runtime(test_func)
    print(f"Runtime: {run_time * 1000:.3f}ms")

    print(f"Total allocated size: {get_mem(test_func)[0] / 1024:.3f} KiB")

    path = facility_drawer.get_path_from_super_path(res)

    print(f"super path: {res}")
    print(f"len of super path: {len(res)}")
    # print(f"path: {path}")
    print(f"len of path: {len(path)}")

    print(f"entry: {facility_drawer.entry}")
    print(f"exit_a: {facility_drawer.exit_a}")
    print(f"exit_b: {facility_drawer.exit_b}")

    def has_edge(u, v) -> bool:
        if u[0] == v[0]:
            u = u[1:]
            v = v[1:]
            return any(wing.has_edge(u, v) for wing in facility_drawer.wings)
        else:
            return (u, v) in facility_drawer.junctions or (v, u) in facility_drawer.junctions

    is_correct = path[0] == facility_drawer.entry
    is_correct &= (path[-1] == facility_drawer.exit_a or path[-1] == facility_drawer.exit_b)
    is_correct &= all(has_edge(path[i], path[i + 1]) for i in range(len(path) - 1))
    print(f"is correct: {"yes" if is_correct else "no"}")


def test_stage_2():
    def pregen(n, trials):
        facility_drawer = [GraphDrawer(i + 10101010, n) for i in range(trials)]
        abs_graph = [facility_drawer[i].get_abstracted_graph() for i in range(trials)]

        exits = [{facility_drawer[i].exit_a, facility_drawer[i].exit_b} for i in range(trials)]
        supplies = [set(facility_drawer[i].supplies) for i in range(trials)]
        storage = tuple([None] * len(supplies))
        supply_map = [{i: hash(i) for i in facility_drawer[i].supplies} for i in range(trials)]

        stage_1_res = [memo1a_algorithm.stage_1(abs_graph[i], facility_drawer[i].entry, supplies[i], exits[i], storage, supply_map[i], set()) for i in range(trials)]
        return abs_graph, facility_drawer, [f.entry for f in facility_drawer], supplies, exits, stage_1_res

    def get_runtime_trials_with_n(p_data, trials, technique) -> tuple[float, float]:
        if trials < 1:
            return 0, 0

        abs_graph, facility_drawer, entry, supplies, exits, stage_1_res = p_data
        """source: https://docs.python.org/3/library/profile.html"""

        pathlen = []

        import cProfile, pstats
        from pstats import SortKey
        pr = cProfile.Profile()
        pr.enable()
        for i in range(trials):
            pathlen.append(technique(entry[i], supplies[i], exits[i], stage_1_res[i][1], stage_1_res[i][4]))
        pr.disable()
        ps = pstats.Stats(pr).sort_stats(SortKey.CUMULATIVE)

        pathlen = [len(facility_drawer[i].get_path_from_super_path(memo1a_algorithm.get_path_from_super_path_bfs(abs_graph[i], memo1a_algorithm.get_path_from_super_path(pathlen[i], stage_1_res[i][0]), stage_1_res[i][2]))) for i in range(trials)]
        pathlen = sum(pathlen) / len(pathlen)

        return [v for k, v in ps.stats.items() if technique.__name__ in k[2]][0][3] / trials * 1000, pathlen

    res: list[dict] = []

    TRIALS = 10
    for n in trange(2, 100, desc="Heuristic Algorithms"):
        data = pregen(n, TRIALS)
        nn_time, nn_len = get_runtime_trials_with_n(data, TRIALS, lambda x, y, z, w, q: memo1a_algorithm.nearest_neighbour(x, y, z, w, q)[0])
        lk_time, lk_len = get_runtime_trials_with_n(data, TRIALS, memo1a_algorithm.lin_kernighan)
        res.append(
            {
                "nearest neighbour time": nn_time,
                "nearest neighbour length": nn_len,
                "lin-kernighan time": lk_time,
                "lin-kernighan length": lk_len
            }
        )

    for n in trange(2, 11, desc="Brute force"):
        data = pregen(n, TRIALS)
        bf_time, bf_len = get_runtime_trials_with_n(data, TRIALS, memo1a_algorithm.brute_force)
        res[n - 2]["brute force time"] = bf_time
        res[n - 2]["brute force length"] = bf_len

    for n in trange(2, 15, desc="Branch & bound"):
        data = pregen(n, TRIALS)
        bb_time, bb_len = get_runtime_trials_with_n(data, TRIALS, memo1a_algorithm.branch_and_bound)
        res[n - 2]["branch & bound time"] = bb_time
        res[n - 2]["branch & bound length"] = bb_len

    if len(res) > 0:
        with open("data_stage_2.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(res[0].keys())
            writer.writerows([[res[i][k] if k in res[i] else "" for k in res[0]] for i in range(len(res))])


def test_memo1a():
    facility_drawer = GraphDrawer(28122007)
    abs_graph = facility_drawer.get_abstracted_graph()

    exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    supplies = set(facility_drawer.supplies)
    storage = tuple([None] * 5)
    supply_map = {i: hash(i) for i in facility_drawer.supplies}

    run_test(lambda: memo1a_algorithm.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set())[0], facility_drawer)

def get_flat_graph(
    abs_graph: tuple[set[nx.Graph], set[tuple]]
) -> nx.Graph:
    res: nx.Graph = nx.compose_all(abs_graph[0])
    for u, v in abs_graph[1]:
        res.add_edge(u, v, weight=1)
    return res

def test_memo1():
    facility_drawer = GraphDrawer(28122007)
    flat_graph = get_flat_graph(facility_drawer.get_abstracted_graph())

    exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    supplies = set(facility_drawer.supplies)
    storage = tuple([None] * 5)
    supply_map = {i: hash(i) for i in facility_drawer.supplies}

    run_test(lambda: memo1_algorithm.ember_rescue(flat_graph, facility_drawer.entry, exits, supplies, supply_map, storage, set()), facility_drawer)


def get_data():
    res: list[dict] = []

    for i in trange(100_000, desc="gathering data on different facilities"):
        i += 10102000
        facility_drawer = GraphDrawer(i)
        abs_graph = facility_drawer.get_abstracted_graph()

        exits = {facility_drawer.exit_a, facility_drawer.exit_b}
        supplies = set(facility_drawer.supplies)
        storage = tuple([None] * 5)
        supply_map = {i: hash(i) for i in facility_drawer.supplies}

        runtime, super_path = get_runtime(lambda: memo1a_algorithm.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set()))

        path = facility_drawer.get_path_from_super_path(super_path[0])

        def has_edge(u, v) -> bool:
            if u[0] == v[0]:
                u = u[1:]
                v = v[1:]
                return any(wing.has_edge(u, v) for wing in facility_drawer.wings)
            else:
                return (u, v) in facility_drawer.junctions or (v, u) in facility_drawer.junctions

        is_correct = path[0] == facility_drawer.entry
        is_correct &= (path[-1] == facility_drawer.exit_a or path[-1] == facility_drawer.exit_b)
        is_correct &= all(has_edge(path[i], path[i + 1]) for i in range(len(path) - 1))

        abstraction_vertices = sum(len(g) for g in abs_graph[0])
        n_wings = facility_drawer.n_wings
        n_supplies = len(supplies)
        salient_vertices = len(list(chain(*facility_drawer.junctions))) + len(exits) + len(supplies) + 1
        solution_len = len(path) - 1
        res.append(
            {
                "seed": i,
                "abstraction_vertices_count": abstraction_vertices,
                "n_wings": n_wings,
                "n_supplies": n_supplies,
                "salient_vertices": salient_vertices,
                "solution_len": solution_len,
                "runtime": runtime * 1000
            }
            )

    if len(res) > 0:
        with open("data_algorithm.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(res[0].keys())
            writer.writerows([d.values() for d in res])

def get_memo_difference():
    res: list[dict] = []

    TRIALS = 10000
    for i in trange(TRIALS, desc="Testing Memo1 vs Memo1A1"):
        facility_drawer = GraphDrawer(10102000 + i)
        abs_graph = facility_drawer.get_abstracted_graph()
        flat_graph = get_flat_graph(abs_graph)

        exits = {facility_drawer.exit_a, facility_drawer.exit_b}
        supplies = set(facility_drawer.supplies)
        storage = tuple([None] * 5)
        supply_map = {i: hash(i) for i in facility_drawer.supplies}

        m1a1_time = get_runtime(lambda: memo1a_algorithm.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set()))[0]
        m1_time = get_runtime(lambda: memo1_algorithm.ember_rescue(flat_graph, facility_drawer.entry, exits, supplies, supply_map, storage, set()))[0]
        res.append(
            {
                "Memo1 time": m1_time * 1000,
                "Memo1A1 time": m1a1_time * 1000,
            }
        )

    if len(res) > 0:
        with open("data_memos.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(res[0].keys())
            writer.writerows([[res[i][k] if k in res[i] else "" for k in res[0]] for i in range(len(res))])


if __name__ == "__main__":
    # test_memo1()
    # test_memo1a()
    # get_data()
    test_stage_2()
    # get_memo_difference()
    pass
