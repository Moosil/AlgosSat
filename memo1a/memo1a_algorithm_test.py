import cProfile
import copy
import csv
import math
import pstats
import random
import tracemalloc
from itertools import chain
from pstats import SortKey

import networkx as nx
from tqdm import trange

import memo1.memo1_algorithm as memo1_algorithm
import memo1a_algorithm


class GraphDrawer:
    def __init__(self, seed, supply_count: int = 5) -> None:
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

    def _get_multi_wing_facility(self, seed, supply_count):
        int_seed = int(seed)
        n_wings = math.ceil(supply_count / 2)  # 2, 3, or 4 wings from seed

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
        storage = tuple([None] * 5)
        supply_map = [{i: hash(i) for i in facility_drawer[i].supplies} for i in range(trials)]

        stage_1_res = [memo1a_algorithm.stage_1(abs_graph[i], facility_drawer[i].entry, exits[i], supplies[i], storage, supply_map[i], set()) for i in range(trials)]
        return facility_drawer, [f.entry for f in facility_drawer], supplies, exits, stage_1_res

    def get_runtime_trials_with_n(pregens_data, trials, technique=memo1a_algorithm.brute_force, min_n=2, max_n=20) -> list[tuple[float, float]]:
        def get_runtime_trials(p_technique, pregen_data, p_trials: int = 1) -> tuple[float, float]:
            if p_trials < 1:
                return 0, 0

            facility_drawer, abs_graph, entry, supplies, exits, stage_1_res = pregen_data
            """source: https://docs.python.org/3/library/profile.html"""

            pathlen = []

            import cProfile, pstats
            from pstats import SortKey
            pr = cProfile.Profile()
            pr.enable()
            for j in range(p_trials):
                pathlen.append(p_technique(entry[j], supplies[j], exits[j], stage_1_res[j][1], stage_1_res[j][2]))
            pr.disable()
            ps = pstats.Stats(pr).sort_stats(SortKey.CUMULATIVE)

            pathlen = [len(facility_drawer[j].get_path_from_super_path(memo1a_algorithm.get_path_from_super_path(pathlen[j], stage_1_res[j][0]))) for j in range(p_trials)]
            pathlen = sum(pathlen) / len(pathlen)

            return [v for k, v in ps.stats.items() if p_technique.__name__ in k[2]][0][3] / p_trials, pathlen

        res: list[tuple[float, float]] = []
        for i in trange(min_n, max_n, desc=f"running {technique.__name__}"):
            res.append(get_runtime_trials(technique, pregens_data[i], trials))
        return res

    TRIALS = 10
    pregens = [None] * 2 + [pregen(n, TRIALS) for n in trange(2, 8, desc="pregenerating")] + \
              [pregen(n, TRIALS) for n in trange(8, 20, desc="pregenerating more")] + [pregen(n, 1) for n in trange(20, 100, desc="pregenerating more more")]

    brute_force_res = get_runtime_trials_with_n(pregens, TRIALS, memo1a_algorithm.brute_force, 2, 11) + \
                      get_runtime_trials_with_n(pregens, 1, memo1a_algorithm.brute_force, 11, 12)
    brute_force_res_ub = get_runtime_trials_with_n(pregens, TRIALS, memo1a_algorithm.brute_force_ub, 2, 11) + \
                         get_runtime_trials_with_n(pregens, 1, memo1a_algorithm.brute_force_ub, 11, 12)
    nearest_neighbour_res = get_runtime_trials_with_n(pregens, TRIALS, lambda x, y, z, w, q: memo1a_algorithm.nearest_neighbour(x, y, z, w, q)[0], 2, 8) + \
                            get_runtime_trials_with_n(pregens, TRIALS, lambda x, y, z, w, q: memo1a_algorithm.nearest_neighbour(x, y, z, w, q)[0], 8, 20) + \
                            get_runtime_trials_with_n(pregens, 1, lambda x, y, z, w, q: memo1a_algorithm.nearest_neighbour(x, y, z, w, q)[0], 20, 100)
    lin_kernighan_res = get_runtime_trials_with_n(pregens, TRIALS, memo1a_algorithm.lin_kernighan, 2, 8) + \
                        get_runtime_trials_with_n(pregens, TRIALS, memo1a_algorithm.lin_kernighan, 8, 20) + \
                        get_runtime_trials_with_n(pregens, 1, memo1a_algorithm.lin_kernighan, 20, 100)
    # brute_force_res_ub_lotsa_trials = get_runtime_trials_with_n(pregens, TRIALS, memo1a_algorithm.brute_force_ub, 2, 8)
    # nearest_neighbour_gap = [nearest_neighbour_res[i][1] / brute_force_res_ub_lotsa_trials[i][1] for i in range(min(len(nearest_neighbour_res), len(brute_force_res_ub_lotsa_trials)))]
    # lin_kernighan_gap = [lin_kernighan_res[i][1] / brute_force_res_ub_lotsa_trials[i][1] for i in range(min(len(lin_kernighan_res), len(brute_force_res_ub_lotsa_trials)))]
    print(f"Brute force time: {','.join(str(i[0]) for i in brute_force_res)}")
    print(f"Brute force UB time: {','.join(str(i[0]) for i in brute_force_res_ub)}")
    print(f"Nearest Neighbour time: {','.join(str(i[0]) for i in nearest_neighbour_res)}")
    print(f"Lin-Kernighan time: {','.join(str(i[0]) for i in lin_kernighan_res)}")
    print(f"Brute force length: {','.join(str(i[1]) for i in brute_force_res)}")
    print(f"Brute force UB length: {','.join(str(i[1]) for i in brute_force_res_ub)}")
    print(f"Nearest Neighbour length: {','.join(str(i[1]) for i in nearest_neighbour_res)}")
    print(f"Lin-Kernighan length: {','.join(str(i[1]) for i in lin_kernighan_res)}")  # print(f"Nearest Neighbour gap: {','.join(str(i) for i in nearest_neighbour_gap)}")  # print(f"Lin-Kernighan gap: {','.join(str(i) for i in lin_kernighan_gap)}")


def test_memo1a():
    facility_drawer = GraphDrawer(28122007)
    abs_graph = facility_drawer.get_abstracted_graph()

    exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    supplies = set(facility_drawer.supplies)
    storage = tuple([None] * 5)
    supply_map = {i: hash(i) for i in facility_drawer.supplies}

    run_test(lambda: memo1a_algorithm.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set())[0], facility_drawer)


def test_memo1():
    def get_flat_graph(
        abs_graph: tuple[set[nx.Graph], set[tuple]]
    ) -> nx.Graph:
        res: nx.Graph = nx.compose_all(abs_graph[0])
        for u, v in abs_graph[1]:
            res.add_edge(u, v, weight=1)
        return res

    facility_drawer = GraphDrawer(28122007)
    flat_graph = get_flat_graph(facility_drawer.get_abstracted_graph())

    exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    supplies = set(facility_drawer.supplies)
    storage = tuple([None] * 5)
    supply_map = {i: hash(i) for i in facility_drawer.supplies}

    run_test(lambda: memo1_algorithm.ember_rescue(flat_graph, facility_drawer.entry, exits, supplies, supply_map, storage, set()), facility_drawer)


def get_data():
    data: list[dict] = []

    for i in trange(30_000, desc="gathering data on different facilities"):
        i += 10102000
        facility_drawer = GraphDrawer(i)
        abs_graph = facility_drawer.get_abstracted_graph()

        exits = {facility_drawer.exit_a, facility_drawer.exit_b}
        supplies = set(facility_drawer.supplies)
        storage = tuple([None] * 5)
        supply_map = {i: hash(i) for i in facility_drawer.supplies}

        runtime, res = get_runtime(lambda: memo1a_algorithm.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set()))

        path = facility_drawer.get_path_from_super_path(res[0])

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

        abstraction_vertices = len(abs_graph)
        n_wings = facility_drawer.n_wings
        salient_vertices = len(list(chain(*facility_drawer.junctions))) + len(exits) + len(supplies) + 1
        solution_len = len(path) - 1
        data.append({"abstraction_vertices_count": abstraction_vertices,
                    "n_wings": n_wings,
                     "salient_vertices": salient_vertices,
                     "solution_len": solution_len,
                     "runtime": runtime
                    })

    if len(data) > 0:
        with open("data.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data[0].keys())
            writer.writerows([d.values() for d in data])

if __name__ == "__main__":
    test_memo1()
    test_memo1a()
    get_data()
