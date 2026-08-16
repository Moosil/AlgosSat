import csv
import random
from math import ceil

import numba

import networkx as nx
from itertools import chain

import sympy as sym
import numpy as np
from tqdm import trange
from tqdm.contrib.concurrent import thread_map

from complexity import Complexity


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

    def get_abstracted_graph(self, weighted=True) -> tuple[set[nx.Graph], set[tuple]]:
        wings = set()
        AAAAAA_vertices = {*self.exits, self.entry, chain(*self.junctions), *self.supplies}
        for i in range(self.n_wings):
            wing: nx.Graph = self.weighted_wings[i].copy() if weighted else self.wings[i].copy()
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

        self.weighted_wings = [g.copy() for g in self.wings]

        for w, wg in enumerate(self.weighted_wings):
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


def get_facility_data():
    res: list[dict] = []

    v, e, n, w, j, p, q = sym.symbols("V,E,n,W,J,P,Q", positive=True, integer=True)
    formula = Complexity.ember_rescue(v, e, w, j, p, q, 5, True).simplify()
    formula_callable = sym.lambdify((v, e, w, j, p, q), formula, "numpy", cse=True)
    formula_callable = numba.jit(formula_callable)
    file_name = "data_facility_ordered.csv"
    TRIALS = 100
    WING_TRIALS = 100

    tasks = list(range(1, WING_TRIALS))
    def process_task(task):
        v_total = 0
        e_total = 0
        j_total = 0
        for _ in range(TRIALS):
            facility_drawer = GraphDrawer(task + 10102000, task, 1, 1)
            abs_graph = facility_drawer.get_abstracted_graph()
            v_total += sum(w_j.number_of_nodes() for w_j in abs_graph[0])
            e_total += sum(w_j.number_of_edges() for w_j in abs_graph[0])
            j_total += len(abs_graph[1])
        return round(v_total / TRIALS), round(e_total / TRIALS), round(j_total / TRIALS)

    results = list(thread_map(process_task, tasks, desc="Analysing Facilities"))
    average_v = {tasks[i]: results[i][0] for i in range(len(results))}
    average_e = {tasks[i]: results[i][1] for i in range(len(results))}
    average_j = {tasks[i]: results[i][2] for i in range(len(results))}

    for w_i in trange(1, WING_TRIALS, desc="Getting Operation Count"):
        for p_i in range(1, 2 * w_i + 1):
            for q_i in range(1, min(w_i, 3)):
                v_i = average_v[w_i]
                e_i = average_e[w_i]
                j_i = average_j[w_i]
                res.append({
                    "v": v_i,
                    "w": w_i,
                    "p": p_i,
                    "q": q_i,
                    "e": e_i,
                    "j": j_i,
                    "s": 5,
                    "op_count": ceil(formula_callable(v_i, e_i, w_i, j_i, p_i, q_i))
                })

    with open(file_name, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["v","w","p","q","e","j","s","op_count"])
        writer.writerows([d.values() for d in res])


if __name__ == "__main__":
    get_facility_data()
