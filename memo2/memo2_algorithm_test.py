import cProfile
import csv
import pstats
import random
import tracemalloc
from itertools import chain
from pstats import SortKey

import networkx as nx
from tqdm.contrib.concurrent import thread_map

import average_tc
import memo2_algorithm


class GraphDrawer:
    def __init__(self, seed, wing_count, supply_count, exit_count) -> None:
        self.seed = seed
        self.WING_COLS, self.WING_ROWS = 10, 10

        self._setup_multi_wing_facility(self.seed, wing_count, supply_count, exit_count)

    @classmethod
    def _neighbours(cls, cols, rows, c, r):
        for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < cols and 0 <= nr < rows:
                yield nc, nr

    @classmethod
    def _build_wing(cls, cols, rows, rng):
        """Build a single-wing maze as a spanning tree of the grid."""
        visited = [[False] * rows for _ in range(cols)]
        g = nx.Graph()
        for c in range(cols):
            for r in range(rows):
                g.add_node((c, r))

        def carve(c, r):
            visited[c][r] = True
            dirs = list(cls._neighbours(cols, rows, c, r))
            rng.shuffle(dirs)
            for nc, nr in dirs:
                if not visited[nc][nr]:
                    g.add_edge((c, r), (nc, nr), weight=1)
                    carve(nc, nr)

        carve(0, 0)
        return g

    def get_abstracted_graph(self) -> tuple[set[nx.Graph], set[tuple]]:
        wings = set()
        AAAAAA_vertices = {*self.exits, self.entry, *list(chain(*self.junctions)), *self.supplies}
        for i in range(self.n_wings):
            wing: nx.Graph = self.wings[i].copy()
            for u, d in self.wings[i].degree:
                w_u = tuple([i] + list(u))
                if d == 2 and w_u not in AAAAAA_vertices:
                    n0 = list(wing.neighbors(u))[0]
                    n1 = list(wing.neighbors(u))[1]
                    w = wing.get_edge_data(u, n0)["weight"] + wing.get_edge_data(u, n1)["weight"]
                    wing.remove_node(u)
                    wing.add_edge(n0, n1, weight=w)
            wing = nx.relabel_nodes(wing, lambda x: tuple([i] + list(x)))
            wings.add(wing)

        return wings, set(self.junctions)

    def get_flat_graph(self, abs_graph: tuple[set[nx.Graph], set[tuple]] = None) -> nx.Graph:
        if abs_graph is None:
            abs_graph = self.get_abstracted_graph()
        res: nx.Graph = nx.compose_all(abs_graph[0])
        for u, v in abs_graph[1]:
            res.add_edge(u, v, weight=self.junction_costs[(u, v)])
        return res

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

    def _setup_cost_models(self):
        int_seed = self.seed

        for w, wg in enumerate(self.wings):
            if w == 0:
                pass
            elif w == 1:
                for (c1, r1), (c2, r2) in list(wg.edges()):
                    wg[c1, r1][c2, r2]['weight'] = 1 + max(c1, c2) // 3
            else:
                _crng = random.Random(int_seed * 41 + w * 3331)
                for (c1, r1), (c2, r2) in list(wg.edges()):
                    wg[c1, r1][c2, r2]['weight'] = _crng.randint(1, 5)

        # Junction costs = 1
        junction_costs = {(n1, n2): 1 for n1, n2 in self.junctions}

        self.junction_costs = junction_costs

    def _setup_multi_wing_facility(self, seed, wing_count, supply_count, exit_count):
        int_seed = int(seed)
        self.n_wings = wing_count

        # Build each wing from a deterministic derived seed
        self.wings = []
        for w in range(self.n_wings):
            wrng = random.Random(int_seed * 31 + w * 7919)
            self.wings.append(self._build_wing(self.WING_COLS, self.WING_ROWS, wrng))

        # Inter-wing junctions: 2 corridors per adjacent wing pair
        # Each junction connects (w, WING_COLS-1, r) to (w+1, 0, r)
        self.junctions = []
        for w in range(self.n_wings - 1):
            jrng = random.Random(int_seed * 17 + w * 5003)
            rows_avail = list(range(2, self.WING_ROWS - 2))
            jrng.shuffle(rows_avail)
            r1, r2 = sorted(rows_avail[:2])
            self.junctions.append(((w, self.WING_COLS - 1, r1), (w + 1, 0, r1)))
            self.junctions.append(((w, self.WING_COLS - 1, r2), (w + 1, 0, r2)))

        # Fixed entry and exits
        self.entry = (0, 0, 0)

        self.exits = []
        while len(self.exits) < exit_count:
            wing = random.randrange(0, self.n_wings, 1)
            lr = random.randrange(0, 2)
            tb = random.randrange(0, 2)
            candidate = (wing, (self.WING_COLS - 1) * lr, (self.WING_ROWS - 1) * tb)
            if candidate not in self.exits:
                self.exits.append(candidate)

        # Supply placement: spread across wings, prefer dead-end nodes
        srng = random.Random(int_seed * 13 + 42)
        reserved = {self.entry, *self.exits}
        for n1, n2 in self.junctions:
            reserved.add(n1)
            reserved.add(n2)

        # Collect dead-end candidates per wing
        per_wing_cands = []
        for w, wg in enumerate(self.wings):
            de = [
                (w, c, r) for (c, r) in wg.nodes()
                if wg.degree((c, r)) == 1 and (w, c, r) not in reserved
            ]
            srng.shuffle(de)
            per_wing_cands.append(de)

        # Amendment A2 (SAT.tex): "Some wings may contain zero supply units."
        # On 3- and 4-wing seeds, leave exactly one non-entry wing empty so the
        # student's own schematic shows the case Action 2 / Action 3 assess.
        # 2-wing seeds keep a 3-2 split: a 5-0 split would strand CRUDY-1's
        # whole objective in one wing and make the ordering question trivial.
        empty_wing = srng.choice(range(1, self.n_wings)) if self.n_wings >= 3 else None
        supply_wings = [w for w in range(self.n_wings) if w != empty_wing]

        # Deal supplies round-robin across the supplied wings until we have 5
        # (or the dead-end candidates run out). Looping rather than a fixed 2
        # passes matters on 2-wing seeds, which would otherwise yield only 4.
        self.supplies = []
        while len(self.supplies) < supply_count:
            added = False
            for w in supply_wings:
                if len(self.supplies) >= supply_count:
                    break
                for n in per_wing_cands[w]:
                    if n not in self.supplies:
                        self.supplies.append(n)
                        added = True
                        break
            if not added:
                break

        self._setup_cost_models()

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
    print(f"exits: {", ".join(str(x) for x in facility_drawer.exits)}")

    def has_edge(u, v) -> bool:
        if u[0] == v[0]:
            u = u[1:]
            v = v[1:]
            return any(wing.has_edge(u, v) for wing in facility_drawer.wings)
        else:
            return (u, v) in facility_drawer.junctions or (v, u) in facility_drawer.junctions

    is_correct = path[0] == facility_drawer.entry
    is_correct &= path[-1] in facility_drawer.exits
    is_correct &= all(has_edge(path[i], path[i + 1]) for i in range(len(path) - 1))
    print(f"is correct: {"yes" if is_correct else "no"}")


def test_memo2():
    facility_drawer = GraphDrawer(28122007, 2 + (28122007 % 3), 5, 2)
    abs_graph = facility_drawer.get_abstracted_graph()

    exits = set(facility_drawer.exits)
    supplies = set(facility_drawer.supplies)
    storage = tuple([None] * 5)
    supply_map = {i: hash(i) for i in facility_drawer.supplies}

    run_test(lambda: memo2_algorithm.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set())[0], facility_drawer)


def get_facility_data():
    file_name = "data_facility_ordered.csv"
    TRIALS = 100
    WING_TRIALS = 10

    tasks = [(i, j, k, l) for i in range(1, WING_TRIALS) for j in range(1, 2 * WING_TRIALS + 1) for k in range(1, min(WING_TRIALS, 2)) for l in range(1, j)]
    def process_task(task: tuple[int, int, int, int]):
        v_total = 0
        e_total = 0
        j_total = 0
        op_total = 0
        for i in range(TRIALS):
            facility_drawer = GraphDrawer(i + 10102000, task[0], task[1], task[2])
            abs_graph = facility_drawer.get_abstracted_graph()
            v_total += sum(w_j.number_of_nodes() for w_j in abs_graph[0])
            e_total += sum(w_j.number_of_edges() for w_j in abs_graph[0])
            j_total += len(abs_graph[1])
            exits = set(facility_drawer.exits)
            supplies = set(facility_drawer.supplies)
            storage = tuple([None] * task[3])
            supply_map = {i: hash(i) for i in facility_drawer.supplies}
            op_total += average_tc.ember_rescue(abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set())[2]
        return round(v_total / TRIALS), task[0], task[1], task[2], round(e_total / TRIALS), round(j_total / TRIALS), task[3], round(op_total / TRIALS)

    results = list(thread_map(process_task, tasks, desc="Analysing Facilities"))

    with open(file_name, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["v","w","p","q","e","j","s","op_count"])
        writer.writerows(results)


if __name__ == "__main__":
    while True:
        test_id = input(
            """Enter a number from 1-2 for a particular test:
            [1] test memo2's algorithm
            [2] get_facility_data
            """
        )
        match test_id:
            case "1":
                test_memo2()
                break
            case "2":
                get_facility_data()
                break
            case _:
                print(f"{test_id} is not a value between 1 and 2")
