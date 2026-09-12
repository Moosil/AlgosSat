import itertools
import random

import networkx as nx

from memo3_algorithm import ember_rescue


class GraphDrawer:
    def __init__(self, seed: int) -> None:
        self.budget_reserve = 0
        self.budget = 0
        self.seed = seed
        self.WING_COLS, self.WING_ROWS = 10, 10
        self.N_SUPPLIES = 30
        self.CAPACITY = 5

        self._setup_multi_wing_facility(self.seed)
        self.set_budget()

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

    def get_abstracted_graph(self):
        wings = []
        for i in range(self.n_wings):
            wings.append(self.wings[i].copy())
            wings[i] = nx.relabel_nodes(wings[i], lambda x: tuple([i] + list(x)))

        return wings, set(self.junctions)

    def _setup_multi_wing_facility(self, seed):
        int_seed = int(seed)
        self.n_wings = 2 + (int_seed % 3)  # 2, 3, or 4 wings from seed
        self.wing_names = ['Alpha', 'Beta', 'Gamma', 'Delta'][:self.n_wings]

        # Build each wing from a deterministic derived seed
        self.wings = [self._build_wing(self.WING_COLS, self.WING_ROWS, random.Random(int_seed * 31 + w * 7919)) for w in range(self.n_wings)]

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
        self.exit_a = (self.n_wings - 1, self.WING_COLS - 1, self.WING_ROWS - 1)
        self.exit_b = (self.n_wings - 1, self.WING_COLS - 1, 0)

        # Supply placement: spread across wings, prefer dead-end nodes
        srng = random.Random(int_seed * 13 + 42)
        reserved = {self.entry, self.exit_a, self.exit_b}
        for n1, n2 in self.junctions:
            reserved.add(n1)
            reserved.add(n2)

        # Collect dead-end candidates per wing
        tier1, tier2 = [], []
        for w, wg in enumerate(self.wings):
            t1 = [(w, c, r) for (c, r) in wg.nodes()
                  if wg.degree((c, r)) == 1 and (w, c, r) not in reserved]
            t2 = [(w, c, r) for (c, r) in wg.nodes()
                  if wg.degree((c, r)) == 2 and (w, c, r) not in reserved]
            srng.shuffle(t1)
            srng.shuffle(t2)
            tier1.append(t1)
            tier2.append(t2)

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
        for tier in (tier1, tier2):
            idx = {w: 0 for w in supply_wings}
            while len(self.supplies) < self.N_SUPPLIES:
                added = False
                for w in supply_wings:
                    if len(self.supplies) >= self.N_SUPPLIES:
                        break
                    while idx[w] < len(tier[w]):
                        n = tier[w][idx[w]]
                        idx[w] += 1
                        if n not in self.supplies:
                            self.supplies.append(n)
                            added = True
                            break
                if not added:
                    break
            if len(self.supplies) >= self.N_SUPPLIES:
                break
        self.supplies = self.supplies[:self.N_SUPPLIES]

        for w, wg in enumerate(self.wings):
            if w == 1:
                for (c1, r1), (c2, r2) in list(wg.edges()):
                    wg[c1, r1][c2, r2]['weight'] = 1 + max(c1, c2) // 3
            elif w >= 2:
                cr = random.Random(int_seed * 41 + w * 3331)
                for (c1, r1), (c2, r2) in list(wg.edges()):
                    wg[c1, r1][c2, r2]['weight'] = cr.randint(1, 5)

        self.G = nx.Graph()
        for w, wg in enumerate(self.wings):
            for (a, b, d) in wg.edges(data=True):
                self.G.add_edge((w,) + a, (w,) + b, weight=d['weight'])
        for a, b in self.junctions:
            self.G.add_edge(a, b, weight=1)

        prng = random.Random(int_seed * 977 + 13)
        self.masses = {s: prng.choice([1, 2, 3]) for s in self.supplies}
        self.values = {s: prng.choice([1, 2, 3, 4, 5]) for s in self.supplies}

        _key = [self.entry] + self.supplies + [self.exit_a, self.exit_b]
        self.dist = {n: nx.single_source_dijkstra_path_length(self.G, n, weight='weight')
                     for n in _key}
        self.path = {n: nx.single_source_dijkstra_path(self.G, n, weight='weight')
                     for n in _key}

    def trip_cost(self, trip):
        """Energy for one shuttle: shaft -> units in the given order -> shaft.

            Mass accumulates as units are picked up, so each leg is charged at the
            mass carried *along that leg*.
            """
        here, total, load = self.entry, 0.0, 0
        for u in trip:
            total += (1 + load) * self.dist[here][u]
            load += self.masses[u]
            here = u
        total += (1 + load) * self.dist[here][self.entry]
        return total

    def trip_mass(self, trip):
        return sum(self.masses[u] for u in trip)

    def trip_value(self, trip):
        return sum(self.values[u] for u in trip)

    def exit_leg(self):
        return min(self.dist[self.entry][self.exit_a], self.dist[self.entry][self.exit_b])

    def plan_cost(self, plan):
        """Total energy for a list of trips, including the final run to an exit."""
        return sum(self.trip_cost(t) for t in plan) + self.exit_leg()

    def plan_value(self, plan):
        return sum(self.trip_value(t) for t in plan)

    def validate_plan(self, plan, budget=None):
        """Return (ok, list_of_problems). Always run this before quoting a result."""
        problems = []
        seen = []
        for i, t in enumerate(plan, 1):
            if self.trip_mass(t) > self.CAPACITY:
                problems.append(
                    f"Trip {i} carries mass {self.trip_mass(t)}, over capacity {self.CAPACITY}."
                )
            for u in t:
                if u not in self.masses:
                    problems.append(f"Trip {i} contains {u}, which is not a supply unit.")
                if u in seen:
                    problems.append(f"Unit {u} appears in more than one trip.")
                seen.append(u)
        if budget is not None:
            c = self.plan_cost(plan)
            if c > budget:
                problems.append(f"Plan costs {c:.0f}, over budget {budget:.0f}.")
        return (len(problems) == 0), problems

    def best_order(self, units):
        """Cheapest collection order within a single trip (brute force; trips are small)."""
        if len(units) <= 1:
            return list(units)
        return list(min(itertools.permutations(units), key=self.trip_cost))

    def exemplar_a_nearest_fill(self, pool, budget):
        """A -- pack whatever is closest, ignore priority entirely."""
        remaining, plan, spent = list(pool), [], 0.0
        while remaining:
            trip, here, load = [], self.entry, 0
            while True:
                fits = [u for u in remaining
                        if u not in trip and load + self.masses[u] <= self.CAPACITY]
                if not fits:
                    break
                u = min(fits, key=lambda x: self.dist[here][x])
                trip.append(u)
                load += self.masses[u]
                here = u
            if not trip:
                break
            trip = self.best_order(trip)
            c = self.trip_cost(trip)
            if spent + c + self.exit_leg() > budget:
                break
            spent += c
            plan.append(trip)
            for u in trip:
                remaining.remove(u)
        return plan

    def set_budget(self):
        full_plan = self.exemplar_a_nearest_fill(self.supplies, budget=float('inf'))
        full_extraction_cost = self.plan_cost(full_plan)
        self.budget = round(full_extraction_cost * .60)
        self.budget_reserve = round(full_extraction_cost * .35)


if __name__ == "__main__":
    facility = GraphDrawer(28122007)

    print(
        '\n'.join(
            str(s) for s in
            ember_rescue(facility.get_abstracted_graph(), facility.entry, {facility.exit_a, facility.exit_b}, facility.supplies, facility.masses, facility.values, {}, set(), facility.budget)
            )
        )
