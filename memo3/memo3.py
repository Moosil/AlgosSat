import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium", app_title="Memo3", css_file="../custom.css")


@app.cell
def imports():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import itertools
    import numpy as np
    import pandas as pd
    import re
    import scipy
    import math

    plt.rcParams['figure.dpi'] = 300
    return itertools, math, mcolors, mo, np, nx, pd, plt, random, re, scipy


@app.cell
def global_vars(mo, pd):
    # Globals
    _figure_names = []

    def get_fig(figure_name: str) -> int:
        if figure_name in _figure_names:
            return _figure_names.index(figure_name) + 1
        else:
            _figure_names.append(figure_name)
            return len(_figure_names)

    @mo.cache
    def get_df(path, *args, **kwargs):
        return pd.read_csv(path, *args, **kwargs)

    return get_df, get_fig


@app.cell(hide_code=True)
def graph_drawer_impl(itertools, mcolors, nx, plt, random, seed_input):
    class GraphDrawer:
        def __init__(self) -> None:
            self.budget_reserve = 0
            self.budget = 0
            self.seed = seed_input.value
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

        def get_plan_info(self, plan):
            curr_supply_locations = self.supplies.copy()
            total_energy_cost = 0
            trip_supplies = []
            trip_costs = []
            trip_move_supplies = [{}]
            next_append = False
            if plan and len(plan) > 0:
                i = 0
                prev_loc = self.entry
                curr_supplies = []
                while i < len(plan):
                    curr = plan[i]
                    curr_loc, ins, curr_w, curr_v = curr
                    if ins == "pickup":
                        supply_index = list(filter(lambda x: self.masses[self.supplies[x]] == curr_w and self.values[self.supplies[x]] == curr_v and x not in curr_supplies and curr_supply_locations[x] == curr_loc, range(len(curr_supply_locations))))[-1]
                        curr_supplies.append(supply_index)
                    elif ins == "drop":
                        supply_index = list(filter(lambda x: self.masses[self.supplies[x]] == curr_w and self.values[self.supplies[x]] == curr_v, curr_supplies))[-1]
                        curr_supplies.remove(supply_index)
                        trip_move_supplies[-1][supply_index] = curr_loc
                        curr_supply_locations[supply_index] = curr_loc
                    if prev_loc != curr_loc:
                        if next_append:
                            trip_supplies.append(set(self.supplies[i] for i, s in enumerate(curr_supply_locations) if s == self.entry).difference(s for trip_s in trip_supplies for s in trip_s))
                            trip_move_supplies.append({})
                            trip_costs.append(total_energy_cost - sum(trip_costs))
                            next_append = False

                        mass_total = sum([self.masses[self.supplies[s]] for s in curr_supplies])
                        total_energy_cost += (1 + mass_total) * self.G.get_edge_data(prev_loc, curr_loc)["weight"]
                        prev_loc = curr_loc

                        if curr == self.entry or i == len(plan) - 1:
                            # number the trip at its first collection point
                            next_append = True

                    i += 1
            trip_costs.append(total_energy_cost - sum(trip_costs))
            return [self.supplies[i] for i, s in enumerate(curr_supply_locations) if s == self.entry], trip_costs, trip_supplies, trip_move_supplies

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

        def draw_multi_wing(
            self, plan=None, show_labels=True, highlight_trip=None, title="Weighted Multi-Wing Facility"
        ):
            COL_BG = '#F5F7FA'
            COL_GRID = '#C8D0DC'
            COL_WALL = '#44546A'
            COL_ENTRY = '#0B6E6B'
            COL_EXIT = '#7A1E2C'
            COL_SUPPLY = '#4AA8A0'
            COL_JUNCTION = '#7A1E2C'
            COL_DROPPED = '#AEB6C2'

            TRIP_COLOURS = [
                '#6D28D9', '#1E40AF', '#DB2777', '#059669', '#EA580C',
                '#0891B2', '#9333EA', '#65A30D', '#E11D48', '#2563EB',
                '#C026D3', '#0D9488', '#F59E0B', '#4F46E5', '#BE123C'
            ]

            GAP = 1  # grid-unit gap between wings in the visualisation

            # Weight colour scale: 1=lightest, 5=darkest
            WEIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
                'emberweight', ['#B8E0DE', '#F4C97A', '#7A1E2C'], N=256
            )

            def cost_color(weight, min_w=1, max_w=5):
                norm = (weight - min_w) / max(max_w - min_w, 1)
                return WEIGHT_CMAP(norm)

            def mass_size(m):
                """Star size encodes how expensive a unit is to carry."""
                return {1: 9, 2: 12, 3: 15}.get(m, 11)

            total_w = self.n_wings * self.WING_COLS + (self.n_wings - 1) * GAP
            showing_plan = bool(plan)
            # corridors recede when routes are on top of them
            corr_alpha = 0.30 if showing_plan else 1.0
            corr_lw = 3.0 if showing_plan else 4.5

            fig_w = max(12, total_w * 0.62)
            fig_h = max(6, self.WING_ROWS * 0.62 + 2.0)
            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.set_facecolor(COL_BG)
            fig.patch.set_facecolor(COL_BG)

            def xoff(w):
                return w * (self.WING_COLS + GAP)

            # Draw each wing
            for w, wing in enumerate(self.wings):
                ox = xoff(w)
                for c in range(self.WING_COLS + 1):
                    ax.plot([ox + c, ox + c], [0, self.WING_ROWS], color=COL_GRID, lw=0.3, zorder=1)
                for r in range(self.WING_ROWS + 1):
                    ax.plot([ox, ox + self.WING_COLS], [r, r], color=COL_GRID, lw=0.3, zorder=1)

                for (c1, r1), (c2, r2), data in wing.edges(data=True):
                    ax.plot(
                        [ox + c1 + 0.5, ox + c2 + 0.5], [r1 + 0.5, r2 + 0.5],
                        color=cost_color(data.get('weight', 1)), lw=corr_lw,
                        alpha=corr_alpha, solid_capstyle='round', zorder=2
                    )

                for c in range(self.WING_COLS):
                    for r in range(self.WING_ROWS):
                        if c + 1 < self.WING_COLS and not wing.has_edge((c, r), (c + 1, r)):
                            ax.plot(
                                [ox + c + 1, ox + c + 1], [r, r + 1],
                                color=COL_WALL, lw=1.4, zorder=3
                            )
                        if r + 1 < self.WING_ROWS and not wing.has_edge((c, r), (c, r + 1)):
                            ax.plot(
                                [ox + c, ox + c + 1], [r + 1, r + 1],
                                color=COL_WALL, lw=1.4, zorder=3
                            )

                ax.add_patch(
                    plt.Rectangle(
                        (ox, 0), self.WING_COLS, self.WING_ROWS, fill=False,
                        edgecolor=COL_WALL, lw=2.2, zorder=4
                    )
                )
                model_names = ['Uniform', 'Depth-based', 'Randomised', 'Randomised']
                model_lbl = model_names[w] if w < len(model_names) else 'Randomised'
                ax.text(
                    ox + self.WING_COLS / 2, self.WING_ROWS + 0.55, f"Wing {self.wing_names[w]}",
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    color='#0B1F3B', zorder=8
                )
                ax.text(
                    ox + self.WING_COLS / 2, self.WING_ROWS + 0.15, f"({model_lbl})", ha='center',
                    va='bottom', fontsize=7, color='#44546A', zorder=8
                )

            # ---- inter-wing junctions ----
            for (w1, c1, r1), (w2, c2, r2) in self.junctions:
                x1, y1 = xoff(w1) + c1 + 0.5, r1 + 0.5
                x2, y2 = xoff(w2) + c2 + 0.5, r2 + 0.5
                ax.plot(
                    [x1, x2], [y1, y2], color=COL_JUNCTION, lw=2.0,
                    linestyle='--', alpha=0.8, zorder=5
                )
                ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=6)
                ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=6)

            # ---- shuttle trips, drawn along the real corridor route ----
            trip_of = {}
            trip_count = 0
            supplies_collected = self.supplies
            trip_supply_end_locs = None
            if plan and len(plan) > 0:
                i = 0
                curr_supply_locations = self.supplies.copy()
                prev_loc = self.entry
                curr_trip = []
                total_energy_cost = 0
                curr_supplies = []
                trip_first_supply = None
                col = TRIP_COLOURS[trip_count % len(TRIP_COLOURS)]
                supplies_collected, _, _, _ = self.get_plan_info(plan)
                while i < len(plan):
                    curr = plan[i]
                    curr_loc, ins, curr_w, curr_v = curr
                    trip_of[curr] = col
                    if ins == "pickup":
                        supply_index = list(filter(lambda x: self.masses[self.supplies[x]] == curr_w and self.values[self.supplies[x]] == curr_v and x not in curr_supplies and curr_supply_locations[x] == curr_loc, range(len(curr_supply_locations))))[-1]
                        curr_supplies.append(supply_index)
                        if trip_first_supply is None:
                            trip_first_supply = curr_loc
                    elif ins == "drop":
                        supply_index = list(filter(lambda x: self.masses[self.supplies[x]] == curr_w and self.values[self.supplies[x]] == curr_v, curr_supplies))[-1]
                        curr_supplies.remove(supply_index)
                        curr_supply_locations[supply_index] = curr_loc
                    if prev_loc != curr_loc:
                        mass_total = sum([self.masses[self.supplies[s]] for s in curr_supplies])
                        total_energy_cost += (1 + mass_total) * self.G.get_edge_data(prev_loc, curr_loc)["weight"]
                        xs = [xoff(n[0]) + n[1] + 0.5 for n in [prev_loc, curr_loc]]
                        ys = [n[2] + 0.5 for n in [prev_loc, curr_loc]]
                        # white underlay keeps overlapping routes legible
                        if highlight_trip is None or highlight_trip == trip_count:
                            ax.plot(
                                xs, ys, color='white', lw=6.4, alpha=0.85, zorder=6,
                                solid_capstyle='round'
                            )
                            ax.plot(
                                xs, ys, color=col, lw=3.6, alpha=0.95, zorder=7,
                                solid_capstyle='round'
                            )
                        prev_loc = curr_loc
                        curr_trip.append(curr_loc)

                    if curr_loc == self.entry:
                        # number the trip at its first collection point

                        if trip_first_supply is not None and (highlight_trip is None or highlight_trip == trip_count):
                            ax.text(
                                xoff(trip_first_supply[0]) + trip_first_supply[1] + 0.5, trip_first_supply[2] + 0.5, total_energy_cost,
                                ha='center', va='center', fontsize=6.5,
                                fontweight='bold', color='white', zorder=13,
                                bbox=dict(
                                    boxstyle='circle,pad=0.16', fc=col,
                                    ec='white', lw=0.7
                                )
                            )

                        if highlight_trip == trip_count:
                            trip_supply_end_locs = curr_supply_locations.copy()

                        trip_first_supply = None
                        trip_count += 1
                        curr_trip = [self.entry]
                        col = TRIP_COLOURS[trip_count % len(TRIP_COLOURS)]

                    i += 1

                col = TRIP_COLOURS[trip_count % len(TRIP_COLOURS)]
                if highlight_trip is None:
                    ax.text(
                        xoff(curr_loc[0]) + curr_loc[1] + 0.5, curr_loc[2] + 0.5, total_energy_cost,
                        ha='center', va='center', fontsize=6.5,
                        fontweight='bold', color='white', zorder=13,
                        bbox=dict(
                            boxstyle='circle,pad=0.16', fc=col,
                            ec='white', lw=0.7
                        )
                    )

            # ---- supply units: star sized by mass ----
            abandoned = {s for s in facility_drawer.supplies if s not in supplies_collected}
            for i, u in enumerate(self.supplies):
                ws, cs, rs = u
                ox = xoff(ws)
                x, y = ox + cs + 0.5, rs + 0.5
                if u in abandoned:
                    ax.plot(
                        x, y, marker='x', ms=7, color=COL_DROPPED,
                        markeredgewidth=1.8, zorder=9
                    )
                else:
                    ax.plot(
                        x, y, marker='*', markersize=mass_size(self.masses[u]),
                        color=trip_of.get(u, COL_SUPPLY),
                        markeredgecolor='white' if u in trip_of else COL_ENTRY,
                        markeredgewidth=0.8, zorder=9
                    )
                if show_labels:
                    ax.text(
                        x + 0.30, y + 0.22,
                        f"S{i + 1}", fontsize=5.2, color=COL_WALL, zorder=10
                    )
                    ax.text(
                        x + 0.30, y - 0.42,
                        f"m{self.masses[u]}/p{self.values[u]}", fontsize=4.6,
                        color='#6B7480', zorder=10
                    )

            if trip_supply_end_locs is not None:
                for i, u in enumerate(trip_supply_end_locs):
                    ws, cs, rs = u
                    ox = xoff(ws)
                    x, y = ox + cs + 0.5, rs + 0.5
                    if self.supplies[i] != u:
                        ax.plot(
                            x, y, marker='*', markersize=mass_size(self.masses[self.supplies[i]]),
                            color=mcolors.to_rgba(trip_of.get(self.supplies[i], COL_SUPPLY), alpha=0.8),
                            markeredgecolor="#FFFFFF80" if self.supplies[i] in trip_of else COL_ENTRY,
                            markeredgewidth=0.8, zorder=9
                        )
                    if show_labels:
                        ax.text(
                            x + 0.30, y + 0.22,
                            f"S{i + 1}", fontsize=5.2, color=mcolors.to_rgba(COL_WALL, alpha=0.8), zorder=10
                        )
                        ax.text(
                            x + 0.30, y - 0.42,
                            f"m{self.masses[self.supplies[i]]}/p{self.values[self.supplies[i]]}", fontsize=4.6,
                            color='#6B748080', zorder=10
                        )


            # ---- shaft (the Memo 01 entry, now the extraction point) and exits ----
            we, ce, re = self.entry
            ax.add_patch(
                plt.Circle(
                    (xoff(we) + ce + 0.5, re + 0.5), 0.34,
                    color=COL_ENTRY, zorder=11
                )
            )
            ax.text(
                xoff(we) + ce + 0.5, re + 0.5, 'S', ha='center', va='center',
                fontsize=7, color='white', fontweight='bold', zorder=12
            )

            for lbl, (wx, cx, rx) in zip(['A', 'B'], [self.exit_a, self.exit_b]):
                ax.add_patch(
                    plt.Circle(
                        (xoff(wx) + cx + 0.5, rx + 0.5), 0.3,
                        color=COL_EXIT, zorder=11
                    )
                )
                ax.text(
                    xoff(wx) + cx + 0.5, rx + 0.5, lbl, ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=12
                )

            # ---- corridor-cost colourbar (unchanged from Memo 02) ----
            sm = plt.cm.ScalarMappable(
                cmap=WEIGHT_CMAP,
                norm=mcolors.Normalize(vmin=1, vmax=5)
            )
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, fraction=0.018, pad=0.02)
            cbar.set_label(
                'Corridor cost  w(e)' + ('  (muted)' if showing_plan else ''),
                fontsize=8, color='#0B1F3B'
            )
            cbar.set_ticks([1, 2, 3, 4, 5])
            cbar.ax.tick_params(labelsize=7)

            # ---- legend ----
            handles = [
                plt.Line2D(
                    [], [], marker='o', ls='', ms=7, color=COL_ENTRY,
                    label='S  extraction shaft (Memo 01 entry)'
                ),
                plt.Line2D(
                    [], [], marker='o', ls='', ms=6, color=COL_EXIT,
                    label='A / B  exits'
                ),
                plt.Line2D(
                    [], [], marker='*', ls='', ms=9, color=COL_SUPPLY,
                    markeredgecolor=COL_ENTRY, label='supply unit  (size = mass)'
                ),
                plt.Line2D(
                    [], [], marker='x', ls='', ms=7, color=COL_DROPPED,
                    label='abandoned'
                ),
                plt.Line2D(
                    [], [], ls='--', lw=2, color=COL_JUNCTION,
                    label='inter-wing junction'
                ),
            ]
            if plan:
                _lbl = f'shuttle trips ({trip_count}, numbered at first pickup)'
                handles.append(
                    plt.Line2D(
                        [], [], lw=4, color=TRIP_COLOURS[0],
                        label=_lbl
                    )
                )
            ax.legend(
                handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.02),
                ncol=3, fontsize=7, framealpha=0.9, borderpad=0.6
            )

            ax.set_xlim(-0.5, total_w + 0.5)
            ax.set_ylim(-1.0, self.WING_ROWS + 1.4)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title(
                title, fontsize=11, fontweight='bold',
                color='#0B1F3B', pad=10
            )
            plt.tight_layout()

            return fig

    facility_drawer = GraphDrawer()
    return GraphDrawer, facility_drawer


@app.cell(hide_code=True)
def _(mo, np, re):
    class PseudocodeExplorer:
        def __init__(self, fp: str):
            self.raw_pseudocode = open(fp, encoding="utf-8").read()
            self.full_pseudocode = self._parse_pseudocode(self.raw_pseudocode)

        def get_fn_fancy(self, name: str, font_size: int = 12, numbered: bool = False, *, start_offset: int = 0, start_offset_function_name_prefix: bool = True, end_offset: int = 0, start_elipsis=True, end_elipsis=True):
            start = self.raw_pseudocode.find(f"PROCEDURE {name}(")
            if start == -1:
                start = self.raw_pseudocode.find(f"FUNCTION {name}(")
                end = self.raw_pseudocode.find(f"END FUNCTION", start)
            else:
                end = self.raw_pseudocode.find(f"END PROCEDURE", start)
            if start == -1 or end == -1:
                print(start, end)
                return f"Oops, didn't find function or procedure called {name}."
            start_line = self.raw_pseudocode.count('\n', 0, start)
            end_line = self.raw_pseudocode.count('\n', start, end)
            res = self.get_lines(start_line + start_offset, start_line + end_line + 1 - end_offset, numbered, start_number_offset=start_offset, first_not_numbered=start_offset == 0)
            if start_offset != 0:
                res = "<br>" + res
                if start_elipsis:
                    res = "..." + res
                if start_offset_function_name_prefix:
                    res = self.get_lines(start_line, start_line + 1, False) + "<br>" + res
            if end_offset != 0:
                res += "<br>"
                if end_elipsis:
                    res += "..."
            return mo.md(
                rf"""
        <div style="font-family: monospace; font-size: {font_size}px; white-space: pre-wrap;">{res}</div>
        """
            )

        def get_lines_fancy(self, start: int = 0, stop: int = -1, font_size: int = 12, numbered: bool = True):
            return mo.md(
                rf"""
        <div style="font-family: monospace; font-size: {font_size}px; white-space: pre-wrap;">{self.get_lines(start, stop, numbered)}</div>
        """
            )

        def get_lines(self, start: int = 0, stop: int = -1, numbered: bool = True, *, start_number_offset: int = 0, first_not_numbered: bool = False):
            if numbered:
                splits = self.full_pseudocode.split('<br>')[start:stop]
                pad = int(np.ceil(np.log10(len(splits))))
                res = "" if first_not_numbered else f"<span class='pseudocode-bracket'>[{start_number_offset:0{pad}}] </span>"
                res += splits[0]
                for i in range(1, len(splits)):
                    res += f"<br><span class='pseudocode-bracket'>[{start_number_offset + i:0{pad}}]</span> {splits[i]}"
                return res
            else:
                return '<br>'.join(self.full_pseudocode.split('<br>')[start:stop])

        @classmethod
        def _parse_pseudocode(cls, code: str) -> str:
            procedures = []
            i: int = 0
            while True:
                i = code.find("PROCEDURE ", i)
                if i == -1:
                    break

                i += len("PROCEDURE ")
                end = code.find('(', i)
                procedures.append(code[i:end])

            i = 0
            while True:
                i = code.find("FUNCTION ", i)
                if i == -1:
                    break

                i += len("FUNCTION ")
                end = code.find('(', i)
                procedures.append(code[i:end])

            del i

            res = code.replace('\n', "<br>").replace("    ", "&#9;")
            res = re.sub("PROCEDURE(?= )", "<span class='pseudocode-command'>PROCEDURE</span>", res)
            res = re.sub("FUNCTION(?= )", "<span class='pseudocode-command'>FUNCTION</span>", res)
            res = re.sub("WHILE(?= )", "<span class='pseudocode-command'>WHILE</span>", res)
            res = re.sub("FOR EACH(?= )", "<span class='pseudocode-command'>FOR EACH</span>", res)
            res = re.sub(r"FOR(?= [^ ]+ <-)", "<span class='pseudocode-command'>FOR</span>", res)
            res = re.sub("IF(?= )", "<span class='pseudocode-command'>IF</span>", res)
            res = re.sub("ELSE", "<span class='pseudocode-command'>ELSE</span>", res)
            for command in ["PROCEDURE", "FUNCTION", "WHILE", "FOR", "IF"]:
                res = re.sub(f"END {command}", f"<span class='pseudocode-command'>END {command}</span>", res)

            for command in ["AND", "OR", "NOT", "RAISE", "DO", "THEN", "IN", "TO", "RETURN", "BREAK", "TRUE", "FALSE"]:
                res = re.sub(fr"(?:(?<=\s)|(?<=&#9;)|(?<=\<br\>)){command}(?:(?=\s)|(?=&#9;)|(?=\<br\>))", f"<span class='pseudocode-command'>{command}</span>", res)

            for operator in ["<-", "=", ">", "<", "<=", ">=", r"+", "-"]:
                res = re.sub(fr"(?<= )\{operator}(?= )", f"<span class='pseudocode-op'>{operator}</span>", res)

            res = re.sub(fr"(?<= )-(?=[0-9])", f"<span class='pseudocode-op'>-</span>", res)

            for item in ["∞"]:
                res = res.replace(str(item), f"<span class='pseudocode-bracket'>{item}</span>")

            for bracket in ["[", "]", "(", ")", "{", "}"]:
                res = re.sub(fr"\{bracket}", f"<span class='pseudocode-bracket'>{bracket}</span>", res)

            def find_all(p_str: str, find_str: str, func) -> str:
                i: int = 0
                while True:
                    i = p_str.find(find_str, i)
                    if i == -1:
                        break

                    p_str = func(p_str, i, find_str)
                    i += len(find_str)
                return p_str

            def syntax_highlight_name(p_str: str, names: list[str], class_name: str) -> str:
                surrounding = r"\s\.\:\,\(\)\[\]\{\}\<\>\;"
                for name in names:
                    p_str = re.sub(fr"(?<=[{surrounding}]){name}(?=[{surrounding}])", f"<span class='{class_name}'>{name}</span>", p_str)
                return p_str

            def syntax_highlight_proc(p_str: str, i: int, find_str: str) -> str:
                params_start = p_str.find('(', i) + len("</span>") + 1
                line_end = p_str.find('<br>', params_start)
                params_end = p_str.find(')', params_start)
                first_line = p_str[params_start:params_end]
                param_names = [s for s in first_line.split(':')]
                param_names = [param_names[0]] + [s.split(', ')[-1] for s in param_names[1:-1]]

                line_end = p_str.find(f"END {find_str}", i + len(find_str))
                if line_end == -1:
                    return p_str
                substr = p_str[i:line_end]
                substr = syntax_highlight_name(substr, param_names, "pseudocode-param")
                return p_str[:i] + substr + p_str[line_end:]

            adt_operators = [
                "get_vertices", "get_edges", "add_vertex", "add_edge", "remove_vertex", "remove_edge", "get_neighbours", "has_edge", "get_vertices", "set_edge_weight", "get_edge_weight", "union", "intersection", "difference", 'symmetric_difference', "size", 'element_of', "strict_subset_of", "subset_of", "are_equal", "size", "has", "at", "remove", "set", "get_keys", "insert", "pop_at", "get", "set", "get", "length", "push_back", "pop_back", "enqueue", "update_priority", "extract_min"
            ]

            res = syntax_highlight_name(res, list(set(adt_operators)) + ["List", "Array", "Set", "Map", "Graph", "Tuple", "Priority Queue", "Positive Integer", "Integer", "Real"], "pseudocode-atomic")
            res = syntax_highlight_name(res, list(set(procedures)), "pseudocode-proc")
            res = syntax_highlight_name(res, ["SupplyID", "Vertex"], "pseudocode-type")

            res = find_all(res, "PROCEDURE</span>", syntax_highlight_proc)
            res = find_all(res, "FUNCTION</span>", syntax_highlight_proc)
            res = res.replace("&#9;", "  ")
            res = re.sub(r"\,", r"<span class='pseudocode-bracket'>,</span>", res)

            return res

    pseudocode_explorer = PseudocodeExplorer("memo3/raw_pseudocode.txt")
    return (pseudocode_explorer,)


@app.cell(hide_code=True)
def title(mo):
    mo.md(r"""
    # Memo 3
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(rf"""
    {mo.outline(label="Table of Contents")}
    """)
    return


@app.cell(hide_code=True)
def settings(mo):
    mo.md(r"""
    # Settings
    """)
    return


@app.cell
def facility_seed_picker(mo):
    seed_input = mo.ui.number(
        value=28122007,
        start=0,
        stop=99999999,
        step=1,
        label="Facility seed",
    )
    seed_input
    return (seed_input,)


@app.cell(hide_code=True)
def introduction(mo):
    mo.md(r"""
    # 1 Introduction
    We have been tasked to design a **decision architecture** for a robot. To do this, we will create a abstraction for this problem, and subsequently an algorithm to solve it.

    The scope of the problem has changed. Now the algorithm must handle many more supplies than it could collect, a finite energy budget, non-uniform supply weights and priorities. To do this, an exact algorithm is not feasible, and employing closely approximate heuristics to arrive at a 'good enough' solution is the plan of the new proposed algorithm of this memo.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 2 Problem Abstraction
    Let $G = (V_w, E_w, w)$ be a meta-graph, with $V_w=\{W_1, W_2, \dots, W_k\}$ being a set of undirected weighted graphs, $E_w \subseteq \{\{u, v\} \vert u \in V_n, v \in V_m, n \neq m\}$ being a set of edges between adjacent wings, $W_n, W_m$ of the facility, with $k$ being the number of wings in the facility, and $\forall n \leq k, W_n = (V_n, E_n)$.

    $V = V_1 \cup V_2 \cup \dots \cup V_k$ and $\forall n, m \leq k, V_n \cap V_m = \varnothing \iff n \neq m$ and $V_n = V_m \iff n = m$, with $V$ representing the salient sectors of the facility $E = E_1 \cup E_2 \cup \dots \cup E_k$ and $\forall n, m \leq k, E_n \cap E_m = \varnothing \iff n \neq m$ and $E_n = E_m \iff n = m$, with $E$ representing the paths between those adjacent salient sectors, and positive integer edge weight function $w: E \cup E_w \to \mathbb{Z}^+$ representing the total cost of traversing the span of sectors  which are adjacent to just two other sectors and between two salient sectors. If $(u, v) \notin E$, define $w(u, v) = \infty$ and if $u = v$, defined $w(u, v) = 0$.

    We will designate source vertex $s \in V$, the set of sink vertices $X \subseteq V$, and the set of supply vertices $S \subseteq V$, each representing the entry, exit, and supply unit-containing sectors respectively.

    To abstract the supply weights and priorities, we will have $\delta: S \to \mathbb{N}$ and $p: S \to \mathbb{N}$ represent functions mapping each supply to a weight and priority repectively.

    Mapping $M: S \to \text{SupplyID}$ will mapp each supply vertex to its `SupplyID`, and set $F$ be the set of found `SupplyID`s.

    Finally, we will take the budget $B$ represent CRUDY-1's limited budget, and $C$ to be CRUDY-1's carry-weight capacity.

    We will be designing an algorithm to traverse meta-graph $G$, from $s$ to an $x \in X$, returning an ordered sequence of tuples, with the first element of each tuple being the next sector, the second element corresponding to the command: 1st being MOVE, 2nd being MOVE then DROP, 3 being MOVE then PICKUP, the 3rd being the supply weight for DROP and PICKUP commands, and the 4th being the supply priority for DROP and PICKUP commands. It will also update $F$ in-place.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.1 Signature Specification
    $\text{ember\_rescue}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \times \text{Map}[\text{Vertex}, \mathbb{N}] \times \text{Map}[\text{Vertex}, \mathbb{N}] \times \text{List}[\text{SupplyID}] \times \text{Map}[\text{Vertex}, \text{SupplyID}] \times \text{Set}[\text{SupplyID}] \times \mathbb{N} \to \text{List}[\text{Tuple}[\text{Vertex}, \mathbb{Z}^+, \mathbb{Z}^+, \mathbb{Z}^+]]$
    """
          )
    return


@app.cell(hide_code=True)
def output_constraints(mo):
    mo.md(r"""
    ## 2.2 Output Constraints
    To concisely present a set of constraints on the output, it is necessary to define the following functions:

    $\delta_{sum}(W, n) = \displaystyle\sum_{\mathclap{k=1}}^n \begin{cases}
    W[k][3] &, W[k][2] = 3\\
    -W[k][3] &, W[k][2] = 2\\
    0 &, \text{ otherwise}
    \end{cases}$

    which gives the total weight CRUDY-1 carries at the $n$th instruction of $W$, an solution to the problem, and

    $p_{sum}(W, n) = \displaystyle\sum_{\mathclap{k=1}}^{n} \begin{cases}
    W[k][4] &, W[k][2] = 2 \land W[k][1] = s\\
    0 &, \text{ otherwise}
    \end{cases}$

    which gives the total budget CRUDY-1 collects by the $n$th instruction of $W$.

    Output ordered sequence $W$ is valid iff:
    - $W[1][1] = s$
    - $W[|W|][1] \in X$
    - $\forall i \in W : i[2] \in [1, 3]$
    - $\forall n \in Z^+ : \delta_{sum}(n) \leq C$
    - $\forall i \in W : i[2] = 3 \implies i[1] \text{ contains a supply of weight } i[3] \text{ and priority } i[4]$
    - $\forall i \in W : i[2] = 2 \implies i[1] \text{ does not contain a supply} \lor i[1] = s$
    - $\displaystyle\sum_{\mathclap{k=1}}^{\mathclap{|W| - 1}} (1 + \delta_{sum}(W, n)) \times w(W[k], W[k + 1]) \leq B$.

    $W \text{ is optimal} \iff \forall w \in S_P : p_{sum}(w, |w|) \leq p_{sum}(W, |W|), \text{ where } S_P \text{ is the solution set of problem instance } P$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 2.3 Assumptions
            To create a coherant algorithm, assumptions must be made to restrict the input in ways that allow more efficient approaches to be taken. The following assumptions have held against all facilty blueprints, historical records and facilties seen in testing, and allow large optimisations of the algorithm.
            - The facility's wings do not contain intra-wing cycles (essential for depth-first search)
            - The facility is fully connected
            - The facility is finite, and therefore there is a finite number of supplies in the facility
            - Each supply has a positive integer weight and priority (essential for knapsack problem dynamic program procedure)
            - There is enough energy to get to an exit.
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 2.4 Main Problem Instance
            We have been tasked with creating an algorithm that works for a facility with the following values: $|V_w| \in [2, 4]$, $|E_w| = 2(|V_w| - 1)$, $|S| = 50$, $C = 5$, $\delta: S \to [1, 3]$, $p: S \to \mathbb{{N}}$. For other problem instances, the algorithm may solve them, but that has been a side-effort, and incorrectness can be found with lower budgets, supply capacities and supply counts in the facility.
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    _title = mo.md(fr"""
    ## 2.5 ADT Revisions
    ### 2.5.1 Justification
    - Making more functions inline, which reduces unnecessary copy instructions
    - adding indexed pop/push functions
    - adding set insertion/removal functions.

    ### 2.5.2 Semantic Changes
    - Algorithm and procedure parameters are now passed by reference instead of copies.
    <hr>
    ### 2.5.3 New Signatures
    """)

    _graphs_md = mo.md(r"""
    - $\text{get\_vertices}: \text{Graph} \to \text{Set}[\text{Vertex}]$
    - $\text{get\_edges}: \text{Graph} \to \text{Set}[\text{Edge}]$
    - $\text{add\_vertex}: \text{Graph} \times \text{Vertex} \to \text{None}$
    - $\text{add\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \times \mathbb{Z}^+ \cup \{0\} \to \text{None}$
    - $\text{remove\_vertex}: \text{Graph} \times \text{Vertex} \to \text{None}$
    - $\text{remove\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \to \text{None}$
    - $\text{get\_neighbours}: \text{Graph} \times \text{Vertex} \to \text{Set}[\text{Vertex}]$
    - $\text{has\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \to \text{Boolean}$
    - $\text{get\_vertices}: \text{Graph} \to \text{Set}[\text{Vertex}]$
    - $\text{set\_edge\_weight}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \times \mathbb{Z}^+ \cup \{0\} \to \text{None}$
    - $\text{get\_edge\_weight}: \text{Graph} \times \text{Vertex} \times \text{Vertex}) \to \mathbb{Z}^+ \cup \{0\}$

    `new Graph` is used to construct an empty graph.
    """)

    _set_md = mo.md(r"""
    - $\text{union}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{intersection}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{symmetric\_difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{size}: \text{Set} \to \mathbb{Z}^+ \cup \{0\}$
    - $\text{element\_of}: \text{Set} \times \text{Item} \to \text{boolean}$
    - $\text{strict\_subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{insert}: \text{Set} \times \text{Item} \to \text{None}$
    - $\text{remove}: \text{Set} \times \text{Item} \to \text{None}$

    `{x_1, x_2, ..., x_n}` is used to construct a set containing `x_1, x_2, ..., x_n`.
    """)

    _map_md = mo.md(r"""
    - $\text{size}: \text{Map} \to \mathbb{Z}^+ \cup \{0\}$
    - $\text{has}: \text{Map} \times \text{Key} \to \text{boolean}$
    - $\text{at}: \text{Map} \times \text{Key} \to \text{Value}$
    - $\text{remove}: \text{Map} \times \text{Key} \to \text{None}$
    - $\text{set}: \text{Map} \times \text{Key} \times \text{Value} \to \text{None}$
    - $\text{get\_keys}: \text{Map} \to \text{Set}[\text{Key}]$

    `new Map` is used to construct an empty map.
    `foo[x]` is used as a shorthand for `at(foo, x)`.
    `foo[x] <- y` is used as a shorthand for `set(foo, x, y)`.
    """)

    _list_md = mo.md(r"""
    - $\text{insert}: \text{List} \times \text{Item} \times \mathbb{N} \to \text{None}$
    - $\text{push\_back}: \text{List} \times \text{Item} \to \text{None}$
    - $\text{pop\_at}: \text{List} \times \mathbb{N} \to \text{None}$
    - $\text{pop\_back}: \text{List} \to \text{None}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+ \cup \{0\}$

    `[x_1, x_2, ..., x_n]` is used to construct a list containing, in order, `x_1, x_2, ..., x_n`.
    `foo[i]` is used as a shorthand for `get(foo, i)`.
    """)

    _tuple_md = mo.md(r"""
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    `(x_1, x_2, ..., x_n)` is used to construct a `n`-tuple containing, in order, `x_1, x_2, ..., x_n`.
    """)

    _pq_md = mo.md(r"""
    - $\text{extract\_min}: \text{Priority Queue} \to \text{Item}$
    - $\text{enqueue}: \text{Priority Queue} \times \text{Item} \times \mathbb{R} \to \text{None}$
    - $\text{update\_priority}: \text{Priority Queue} \times \text{Item} \times \mathbb{R} \to \text{None}$
    - $\text{length}:\text{Priority Queue} \to \mathbb{Z}^+$

    `new Priority Queue` is used to contruct an empty priority queue.
    """)

    mo.vstack([
        _title,
        mo.ui.tabs({
            "Graph": _graphs_md,
            "Set": _set_md,
            "Map": _map_md,
            "List": _list_md,
            "Tuple": _tuple_md,
            "Priority Queue": _pq_md
        })
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.6 Data Model Revisions
    Due to the dropping supplies feature of the revised problem, abstracting 2-degree vertices as weight between 3+ degree vertices loses data. This is because supplies must be dropped on these 2-degree sectors in optimal solutions.

    This change causes a redesign, as $|V|$ and $|E|$ are now larger.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.7 Revised Algorithm
    the TL;DR of this algorithm is "DFS on $G$, clearing between each non-3-degree vertex recursively, bring back supplies when total weight on backtrack $\geq 5$".

    The algorithm first, like the previous algorithm, determines which supplies have already been collected using $F$ and $M$, removing them from $S$. It will then flatten $G$ to a single graph and run Dijkstra's algorithm from $s$. It will find the shortest path to an exit vertex in $X$ and save that cost in a variable. After which it will run a knapsack problem on the supplies' weights and priorities with a budget equal to $B$ minus that exit run distance, with tuned supply costs based on empirical data. It will then, for each supply get which junctions it should go through to reach them.

    Then it reaches the main body of the algorithm, which clears all supplies from a branch of the tree by clearing supplies on a stretch between the current vertex, $u$, and a new vertex $v: \deg_+(v) \geq 3 \vee \deg_+(v) = 1$ and then recursively calling it on each neighbour of $v$.

    While going between $u$ and $v$, it will check if any of those vertices between are junctions, in which case it calls a procedure to clear the connecting wings, if any supplies could be on that junction path or further junctions paths.

    When it has cleared supplies between $u$ and $v$, it will check if the path to the last point of inter-wing transit or to the entry otherwise has total supply weight $\geq 5$, in which case it will run a knapsack dp algorithm on those supplies and take back those supplies to the entrance. After that, it will bring back and drop all supplies between $v$ and $u$ to $u$ and before $u$.

    Supply dropping is an integral part of this algorithm, and its advantages and the margin to which its better will be discussed later.

    Some further optimisations have been made, but they will be discussed later.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 3 Algorithm Quality
    ## 3.1 Efficiency
    The revised algorithm is much more efficient that memo 2's algorithm, running in $O(n^6)$, compared with memo 2's $O(n^2 2^n)$ complexity, where $n$ is the byte-length of the input. This latter complexity is intractable and would not work on the larger supply count in the updated situation, as it grows faster than polynomial time. The former complexity is tractable, being polynomial with degree 6.

    When applied to real-world scenarios, even though a version of memo 2's algorithm adapted to the new problem would give an optimal supply collection, it would likely take years or may never complete in the time left in the universe on a super-computer, let alone a drone. The space complete $O(n^3 2^n)$ would also become a problem, with it being unrunnable after 35 supplies even if that cost has coefficient 1 (which is has at least).

    Alternatively, the solution proposed in this memo runs in $O(n^6)$ time and $O(n^3)$ space, making it useable on larger facilities without changes. This makes it useful on lower-end mobile CPUs like those embedded in lower-end drones.

    ## 3.2 Coherence
    Both problem abstractions were concise and coherant, without redundant elements. They also aim to be as unopinionated as is useful: allowing a variety of algorithms to be used without being so general as to become useless.

    This memo's algorithm has an edge against the more general algorithm of the previous memo: memoised dp exhaustive search doesn't fit any specific problem, while the depth-first search utilised assumptions of the facility to reduce the complexity of the algorithm to being tractable.

    ## 3.3 Fitness for Purpose
    Due to the heuristic nature of memo 3's algorithm, a memo 2-like algorithm &mdash; which is exact and searches all possible best solutions &mdash; will arrive at a better solution than this memo's algorithm. This of course comes at the cost of efficiency, and difficulty to encapsulate all features of the problem: multiple-trips, trip-dependent supply collection costs and dropping supplies, into an exact algorithm, which is why a heuristic algorithm is more fit for purpose than an exact algorithm like memo 2's.

    ## 3.4 Counter-example
    """)
    return


@app.cell(hide_code=True)
def _(GraphDrawer, plt, random):
    def draw_sub_facility(title, ax, cols, rows, drone=(0, 0), supplies=[], path=[], path_len=0):
        COL_BG = '#F5F7FA'
        COL_GRID = '#C8D0DC'
        COL_WALL = '#44546A'
        COL_ENTRY = '#0B6E6B'
        COL_EXIT = '#7A1E2C'
        COL_SUPPLY = '#4AA8A0'
        COL_DRONE = "#eb4034"
        COL_ROUTE = list(
            reversed(
                [
                    '#83f6b7',
                    '#00e1ce',
                    '#00bedc',
                    '#009aeb',
                    '#3867f7',
                    '#6d28d9'
                ]
            )
        )

        g = GraphDrawer._build_wing(cols, rows, random.Random(0))

        ax.set_facecolor(COL_BG)

        for c in range(cols + 1):
            ax.plot(
                [c, c], [0, rows],
                color=COL_GRID, lw=0.3, zorder=1
            )
        for r in range(rows + 1):
            ax.plot(
                [0, cols], [r, r],
                color=COL_GRID, lw=0.3, zorder=1
            )

        ax.add_patch(
            plt.Rectangle(
                (0, 0), cols, rows, fill=False,
                edgecolor=COL_WALL, lw=2.2, zorder=4
            )
        )

        for c in range(cols):
            for r in range(rows):
                if c + 1 < cols and not g.has_edge((c, r), (c + 1, r)):
                    ax.plot(
                        [c + 1, c + 1], [r, r + 1],
                        color=COL_WALL, lw=1.4, zorder=3
                    )
                if r + 1 < rows and not g.has_edge((c, r), (c, r + 1)):
                    ax.plot(
                        [c, c + 1], [r + 1, r + 1],
                        color=COL_WALL, lw=1.4, zorder=3
                    )

        total_cost = 0
        storage = []
        if path:
            path = path[:path_len]
            trip_c = 0
            for i in range(len(path) - 1):
                x1, y1, i1 = path[i]
                x2, y2, i2 = path[i + 1]
                if (x1, y1) == (0, 0):
                    trip_c += 1
                ax.plot(
                    [x1 + 0.5, x2 + 0.5],
                    [y1 + 0.5, y2 + 0.5], color=COL_ROUTE[trip_c], lw=5.0,
                    linestyle='-', alpha=1.0, zorder=8, solid_capstyle='round'
                )

                total_cost += sum(supplies[s_idx][2] for s_idx in storage) + 1

                if i1 == 2:
                    s_idx = storage.pop()
                    supplies[s_idx] = (x1, y1, supplies[s_idx][2])
                elif i1 == 1:
                    added = False
                    for s_idx in range(len(supplies)):
                        if supplies[s_idx][0] == x1 and supplies[s_idx][1] == y1:
                            storage.append(s_idx)
                            added = True
                            break
                elif i1 == 3:
                    while len(storage) > 0:
                        s_idx = storage.pop()
                        supplies[s_idx] = (x1, y1, supplies[s_idx][2])

            x1, y1, i1 = path[-1]
            if i1 == 2:
                s_idx = storage.pop()
                supplies[s_idx] = (x1, y1, supplies[s_idx][2])
            elif i1 == 1:
                added = False
                for j in range(len(supplies)):
                    if supplies[j][0] == x1 and supplies[j][1] == y1:
                        storage.append(j)
                        added = True
                        break
            elif i1 == 3:
                while len(storage) > 0:
                    s_idx = storage.pop()
                    supplies[s_idx] = (x1, y1, supplies[s_idx][2])

            drone = path[-1][0], path[-1][1]

        storage_i = 0
        for i, (x, y, w) in enumerate(supplies):
            if x == 0 and y == 0:
                continue

            if i in storage:
                ax.plot(
                    drone[0] + 0.8 + storage_i * .25, drone[1] + 0.2, marker='*', markersize=20,
                    color=COL_SUPPLY, markeredgecolor=COL_ENTRY,
                    markeredgewidth=3, zorder=9
                )
                ax.text(drone[0] + 0.8 + storage_i * .25, drone[1] + 0.2 - .01, w, fontsize=16, color="#ffffff", zorder=10, ha="center", va="center")
                storage_i += 1
            else:
                ax.plot(
                    x + 0.5, y + 0.5, marker='*', markersize=40,
                    color=COL_SUPPLY, markeredgecolor=COL_ENTRY,
                    markeredgewidth=3, zorder=9
                )
                ax.text(x + .5, y + .5 - .01, w, fontsize=16, color="#ffffff", zorder=10, ha="center", va="center")

        ax.plot(
            drone[0] + 0.5, drone[1] + 0.5, marker="o", markersize=40,
            color=COL_DRONE, markeredgecolor="#94283c",
            markeredgewidth=3, zorder=11
        )
        ax.text(drone[0] + 0.515, drone[1] + 0.495, r"$\mathbf{C}_1$", fontsize=20, color="#ffffff", zorder=12, ha="center", va="center")

        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(
            title, fontsize=14, fontweight='bold',
            color='#0B1F3B', pad=10
        )
        return ax, total_cost

    return (draw_sub_facility,)


@app.cell
def _(mo):
    counter_example_slider = mo.ui.slider(0, 17, 1, show_value=True, label="Path length")
    return (counter_example_slider,)


@app.cell
def _(counter_example_slider, draw_sub_facility, mo, plt):
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(16, 8))
    _fig.patch.set_facecolor('#F5F7FA')
    _, _nearest_first_budget = draw_sub_facility(
        "Greedy (nearest-first)", _ax1, 4, 4, (0, 0), [(1, 1, 3), (2, 2, 1)],
        [(0, 0, 0), (1, 0, 0), (1, 1, 1), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 3, 0), (2, 3, 0), (2, 2, 1), (2, 3, 0), (3, 3, 0), (3, 2, 0), (3, 1, 0), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3)], counter_example_slider.value + 1
    )
    _, _algorithm_budget = draw_sub_facility(
        "My algorithm", _ax2, 4, 4, (0, 0), [(1, 1, 3), (2, 2, 1)],
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 3, 0), (2, 3, 0), (2, 2, 1), (2, 3, 0), (3, 3, 0), (3, 2, 0), (3, 1, 0), (2, 1, 0), (1, 1, 1), (1, 0, 0), (0, 0, 3)], counter_example_slider.value + 1
    )

    mo.vstack([mo.lazy(_fig, show_loading_indicator=True), mo.hstack([counter_example_slider, mo.md(fr"""total budget used: {_nearest_first_budget} (greedy) / {_algorithm_budget} (my algorithm)""")])])
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Greedy counter-example")}</span>

    Figure {get_fig("Greedy counter-example")} shows the large difference between nearest-first greedy and my algorithm, which is closer to further-first greedy. Nearest-first fails to account for the cost of moving the supply it is carrying the distance to supplies later in the trip, which is accounted for in my algorithm. This is never better than the furthest-first approach with supply dropping and is most often better unless budget restrictions get tight.
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 4 Time & Space Complexity and Optimisations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4.1 Worst-case
    """)
    return


@app.cell
def _(mo, pseudocode_explorer, re):
    class ProcedureTCExplorer:
        @classmethod
        def get_custom_explanation(cls, name):
            match name:
                case "reconstruct_path_to":
                    return """The while loop (7) runs exactly $|V|$ times, where the lengths of the left and right paths increment by 0 or 1 each run of the loop. The for loops (18) (32) runs at most the length of the left and right paths, giving a triangular amount of runs. The inside of the ifs inside the for loops (19) (33) run exactly once, as it returns after that."""
                case "get_path_length":
                    return r"""The for loop (2) runs exactly $n - 1$ times."""
                case "reverse":
                    return r"""The for loop (2) runs exactly $n$ times."""
                case "reconstruct_path":
                    return r"""The while loop (2) can run at most $|V|$ times, as valid first inputs represent a directed tree graph with $|V|$ verticies. The call to reverse is done with $n = |V|$"""
                case "dijkstra":
                    return r"""The for loops (2) (6) run exactly $|V|$ times. Since the while loop removes 1 item from the priority queue each loop, it runs at most $|V|$ times"""
                case "ember_rescue":
                    return r"""The for loop (12) runs exactly $|X|$ times, calling reconstruct path on $n = |V|$ vertices. Then clear branch is called (41), which has much larger costs in all variables than other parts of ember_rescue."""
                case "knapsack_capacity":
                    return r"""There are 2 nested loops (10) (13) which run $n$ and $C$ times respectively, where $C$ is the capacity parameter."""
                case "knapsack_value":
                    return r"""There are 2 nested loops (15) (18) which run $n$ and $C$ times respectively, where $P$ is the sum of values in the value parameter."""
                case "get_which_wing":
                    return r"""The for loop (1) runs exactly |V_W| times."""
                case "find":
                    return r"""linear search at worst searches through the entire list with the for loop (1)."""
                case "flatten_graph":
                    return r"""The nest for loops (2) (3) (6) are amortised to each vertex and edge on the graph, giving $|V|$ and $|E|$ iterations respecitvely. The for loops are started $|V_w|$ times. The final for loop (10) runs $|E_w|$ times."""
                case "get_weight_cost":
                    return r"""no loops or anything"""
                case "get_reduced_supplies":
                    return r"""The main cost is in the call to `knapsack_value`. The maximum value is in $O(n C)$ where $C$ is the drone weight capacity, giving $O(n \times n C)$."""
                case "get_other_junction":
                    return r"""Checks each junction in for loop (1), totaling $|E_w|$ times."""
                case "get_supplies_to_collect":
                    return r"""Checks each supply in for loop (2), totaling $|S|$ times."""
                case "get_supply_wing_paths":
                    return r"""Adds each junction to set in for loop (2). Then it does, for each supply, looks through the path between it and the entrance. This path has a maximal length of $|V|$, giving $|V| \times |S|$ iterations."""
                case "knapsack_supplies":
                    return r"""The outer while loop (6) runs at most $C$ times, as it will remove 1 supply from the facility each time. It then calls `knapsack_capacity` (11) which runs in $O(|S| C)$. The backtracking while loop (27) can run for each vertex in the facility if that is the full backtrack. The for loop (31) can run up to $C$ times, as the knapsack can hold at most $C$ items, given their weight is in $\mathbb{Z}^+$. The while loop inside (34) can run at most $C$ times for the same reason: it removes at least 1 weight from a value that can be at most $C$ each loop till it's at lowest 0. The while loop (38) can run up to $|V| - 1$ times for a full backtrack."""
                case "clear_junction_path":
                    return r"""since `clear_junction_path` and `clear_branch` both call each other recursively, their complexity classes are the same. The $|E|$ cost can be attributed to the for loop (34) running at most $|E|$ times if each edge connects two junctions. The inner for loops amortise to costs smaller than other terms, as the length of the return value is bound in $2|V| (|S| + 2)$ in the worst case where it brings back each supply to the entrances then goes to get that supply and repeats."""
                case "clear_branch":
                    return r"""<div>Since `clear_junction_path` and `clear_branch` both call each other recursively, their complexity classes are the same. From the `clear_branch` procedure, two of the main 3 terms can be found:
                    <ul>
                    <li>$|S| C (|S| C + C^2 |V|^2)$ can be attributed to calling knapsack_supplies and it sucessfully running past the if conditional at most $|S|$ times as it can happen at most once for each supply.</li>
                    <li>$|V| |V_E| (|S|^2 + |V| + |C|)$ can  be attributed to amortisation of the recursive calls. Since the facility's wings are trees, vertex in the facility has 1 path of junctions which it is optimally traversed through. This optimal path can traverse through at most $|E_w|$ junctions, each searching at most $|V|$ vertices.
                      <ul><li>Each run of the procedure will backtrack at most $|V|$ vertices. The check inside for supplies amortises to $|S|$ checks.</li>
                      <li>The double nested while loop (74) (80) backtracking through `res`. The inner loop amortises to $|S|$, as it can only be called $|S|$ times because it's checking for supplies in the current vertex.</li>
                      <li>he double nested while loop below (92) (101) has the outer running $C$ times at most for dropping at most $C$ 1-weight supplies (given supply weights $\in \mathbb{N}$), while the inner loop amortises to $|S|$ runnings for the same reason as the previous part.</li></ul></li></ul></div>"""
                case "ember_rescue":
                    return r"""The $|X| |V|$ cost can be attributed to finding length of paths to each exit (12 - 19). The $|V|^3$ cost is from reconstructing the paths between at most $|V| |S|$ vertices (44, 54), in the worst case where CRUDY-1 collects each supply one at a time. The rest of the cost is from the `clear_branch` call (41) which is amortised on each vertex (hence it's not $|V| \times$ that cost).
        
    In terms of the byte-length of the input $n$, this gives $O(n^6)$ time complexity."""

        @classmethod
        def get_function(cls, name: str):
            var_explanation_dict = {
                "V": "set of vertices",
                "E": "set of edges",
                "V_W": "set of input wing graphs",
                "E_W": "set of inter-wing junctions",
                "A": "array representing CRUDY-1's supply storage",
                "X": "set of exit vertices",
                "S": "set of supply vertices"
            }

            big_os = open("memo3/big_os.txt", encoding="utf-8").read()
            t_n_big_o_latex = list(filter(lambda x: name in x, big_os.split('\n')))[0].replace(f"{name}: ", "")

            pseudocode = pseudocode_explorer.get_fn_fancy(name, numbered=True)

            return mo.md(
                fr"""
                ### {"Procedure" if name != "ember_rescue" else "Algorithm"} `{name}`
                {pseudocode}

                $${t_n_big_o_latex}$$

                {cls.get_custom_explanation(name)}
            """
                )

    proc_tc_explorer = ProcedureTCExplorer()

    _tabs_dict = {}

    for _match in re.finditer("FUNCTION ([^\()]+)", pseudocode_explorer.raw_pseudocode):
        _tabs_dict[_match.group(1)] = proc_tc_explorer.get_function(_match.group(1))

    for _match in re.finditer("PROCEDURE ([^\()]+)", pseudocode_explorer.raw_pseudocode):
        _tabs_dict[_match.group(1)] = proc_tc_explorer.get_function(_match.group(1))

    mo.ui.tabs(_tabs_dict)
    return


@app.cell
def _(mo):
    class VariableSetter(mo.ui.dictionary):
        _pretty_name = {
            "vertex count": "Vertex count",
            "wing count": "Wing count",
            "supply count": "Supply count",
            "exit count": "Exit count",
            "edge count": "Edge count",
            "junction count": "Inter-wing junction count",
            "supply cap": "Supply capacity",
            "op_count": "Operation count"
        }

        def __init__(self, label, range_max: dict[str, int]=None, initial_values=None, range_min: dict[str, int]=None, *, df=None, variables: list[str]=None):
            if variables is None:
                variables = ["vertex count", "edge count", "wing count", "junction count", "exit count", "supply count", "supply cap"]

            self.variables = list(variables)

            for v in self.variables:
                if v not in initial_values:
                    initial_values[v] = None

            if df is None:
                if range_max is None:
                    range_max = "oops. range_max or df must be filled"
                super().__init__({self._pretty_name[name]: mo.ui.slider(1 if range_min is None else range_min[name], range_max[name], 1, label=self._pretty_name[name], show_value=True, value=None if initial_values is None else initial_values[name]) for name in variables}, label=label)
            else:
                super().__init__({self._pretty_name[name]: mo.ui.slider(steps=[int(n) for n in sorted(df[name].unique())], label=self._pretty_name[name], show_value=True, value=None if initial_values is None else initial_values[name]) for name in variables}, label=label)

        def __getitem__(self, name):
            if name in self._pretty_name:
                name = self._pretty_name[name]
            return super().__getitem__(name)

    operation_cost_explorer = VariableSetter(
        "Variables",
        {"vertex count": 144*3, "wing count": 150, "supply count": 50, "exit count": 50, "edge count": 144*3-4, "junction count": 150, "supply cap": 50},
        {"vertex count": 70,  "wing count": 150, "supply count": 11, "exit count": 4,  "edge count": 150, "junction count": 150, "supply cap": 50},
        None
    )
    return (VariableSetter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4.2 Average-case
    """)
    return


@app.cell
def _(VariableSetter, get_df, mo):
    _df = get_df("memo3/data/data_facility.csv")

    _pretty_name = {
        "vertex count": "Vertex count",
        "wing count": "Wing count",
        "supply count": "Supply count",
        "exit count": "Exit count",
        "edge count": "Edge count",
        "junction count": "Inter-wing junction count",
        "supply cap": "Supply capacity",
        "op_count": "Operation count"
    }

    _variables = ["vertex count", "edge count", "wing count", "exit count", "supply count", "supply cap"]

    _all_vars = ["vertex count", "edge count", "wing count", "junction count", "exit count", "supply count", "supply cap"]

    average_case_partial_growth_rate_explorer = VariableSetter("Fixed Variables",
        df=_df, variables=_variables, initial_values={"supply count": 50, "supply cap": 5, "exit count": 2}
    )

    _default_enabled = {
        "vertex count": False,
        "wing count": False,
        "supply count": True,
        "exit count": True,
        "edge count": False,
        "junction count": False,
        "supply cap": True,
    }

    average_case_partial_growth_rate_explorer_cbs = mo.ui.dictionary({_pretty_name[name]: mo.ui.checkbox(value=_default_enabled[name], on_change=lambda v: on_change_cb(name, v)) for name in _variables}, label="Enabled")

    average_case_partial_growth_rate_colour_picker = mo.ui.dropdown([_pretty_name[n] for n in _all_vars], allow_select_none=True, value=None, searchable=False, label="Coloured variable (except in supply/supply storage figures)")

    def on_change_cb(name: str, value: bool):
        average_case_partial_growth_rate_explorer[name].disabled = value

    mo.vstack([
        mo.hstack([
            average_case_partial_growth_rate_explorer,
            average_case_partial_growth_rate_explorer_cbs
        ], widths=[1.5, 1]),
        average_case_partial_growth_rate_colour_picker
    ])
    return (
        average_case_partial_growth_rate_colour_picker,
        average_case_partial_growth_rate_explorer,
        average_case_partial_growth_rate_explorer_cbs,
    )


@app.cell
def _(
    average_case_partial_growth_rate_colour_picker,
    average_case_partial_growth_rate_explorer,
    average_case_partial_growth_rate_explorer_cbs,
    get_df,
    mo,
    np,
    plt,
):
    _pretty_name = {
        "vertex count": "Vertex count",
        "wing count": "Wing count",
        "supply count": "Supply count",
        "exit count": "Exit count",
        "edge count": "Edge count",
        "junction count": "Inter-wing junction count",
        "supply cap": "Supply capacity",
        "op_count": "Operation count"
    }

    _variables = ["vertex count", "edge count", "wing count", "junction count", "exit count", "supply count", "supply cap"]

    def _get_df(names=[]):
        df = get_df("memo3/data/data_facility.csv")

        for n in _variables:
            if n in ["junction count"]:
                continue

            if not average_case_partial_growth_rate_explorer_cbs[_pretty_name[n]].value:
                continue

            if n in names:
                continue

            df = df[df[n] == average_case_partial_growth_rate_explorer[n].value]
            if len(df) == 0:
                print("Empty df")
                break

        return df.sample(n=min(300, len(df)))

    @mo.cache
    def _plot(name):
        _fig, _ax = plt.subplots(1, 1, figsize=(12, 6))
        df = _get_df([name])
        if len(df) == 0:
            return _fig

        if average_case_partial_growth_rate_colour_picker.value is None:
            _ax.scatter(df[name], df["op count"], color="#74c7ec", label=_pretty_name[name], alpha=.7)
        else:
            colour_name = [k for k, v in _pretty_name.items() if v == average_case_partial_growth_rate_colour_picker.value][0]

            colors = plt.cm.viridis(np.linspace(0, 1, max(df[colour_name])))
            for m in sorted(df[colour_name].unique()):
                c_df = df[df[colour_name] == m]
                if len(c_df) > 0:
                    _ax.scatter(c_df[name], c_df["op count"], color=colors[m - 1], label=_pretty_name[name], alpha=.7)

            sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(vmin=0, vmax=max(df[colour_name])))
            axcb = _fig.colorbar(sm, ax=_ax)
            axcb.set_label(f"{_pretty_name[colour_name]}", fontsize=14)

        _ax.set_xlabel(_pretty_name[name], fontsize=14)
        _ax.set_title(f"{_pretty_name[name]} vs Operation count", fontsize=16)
        _ax.set_xlim(0, max(df[name]) * 1.1)
        _ax.set_ylim(1, max(df["op count"]) * 1.1)
        _ax.tick_params(axis='x', which='major', labelsize=14)
        _ax.set_ylabel("Operation count", fontsize=14)

        _fig.tight_layout()
        return _fig

    average_case_partial_growth_tabs = mo.ui.tabs({_pretty_name[name]: mo.lazy(_plot(name), show_loading_indicator=True) for name in _variables})
    average_case_partial_growth_tabs
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The new algorithm has a much better, non-exponential average time. It displays low-order polynomial-time with all variables, and the runtime of the algorithm is dominated instead by constant costs.

    For the main problem instance it has low coefficient polynomial time growth with vertices, edges, wings, inter-wing junctions, exits, supply capacity and higher coefficient polynomial time growth with supplies.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 4.2.1 Average Case Operations
            """
        )
    return


@app.cell
def _(mo, np, pd, plt):
    def _get_flame_graph(df, samples):
        fig, ax = plt.subplots(figsize=(10, 4))

        for name in df:
            df[name] /= samples

        max_splits = 0
        for stack in df:
            max_splits = max(max_splits, len(stack.split("->")))

        for i in range(max_splits - 1, 1, -1):
            curr_df = list(filter(lambda x: len(x.split("->")) == i, df))
            for name in curr_df:
                parent_name = "->".join(name.split("->")[:-1])
                df[parent_name] += df[name]

        data_width = df["ember_rescue"].tolist()[0]

        splits = {"ember_rescue": 0}

        def get_bar(ax, name, depth, left, value):
            bar = ax.barh(depth, value, left=left, ec="#000000", color=cmap(float(depth) / max_splits / 2 + .5), height=1)
            label = ax.text(data_width * .003 + left, depth, f"{name}: {np.round(value / data_width * 100, 2)}%", ha="left", va="center", clip_on=True)
            label.set_clip_path(bar[0])

        cmap = plt.get_cmap("inferno")
        get_bar(ax, "ember_rescue", 1, 0, data_width)
        for depth in range(2, max_splits):
            curr_df = list(sorted(filter(lambda x: len(x.split("->")) == depth, df), key=lambda x: df[x].tolist()[0], reverse=True))
            for name in curr_df:
                parent_name = "->".join(name.split("->")[:-1])
                parent_curr_start = splits[parent_name]
                value = df[name].tolist()[0]
                splits[name] = parent_curr_start
                splits[parent_name] += value
                get_bar(ax, name.split("->")[-1], depth, parent_curr_start, value)

        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.set_visible(False)
        ax.set_xlim(0, data_width, auto=True)
        ax.set_title("Main problem instance flame graph")
        ax.set_xlabel("Operation (count)")
        plt.tight_layout()
        return fig

    _df = pd.read_csv("memo3/data/flame_facility_small.csv")
    mo.lazy(_get_flame_graph(_df, sum(1 for _ in open("memo3/data/data_facility_small.csv", encoding="utf-8").read())), show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    # TODO move error stuff to error section except first one...
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Main problem instance flame graph")}</span>

    Figure {get_fig("Main problem instance flame graph")} shows the call stack of an average run of the algorithm on the main problem instance. 

    The majority of time is spent in `get_reduced_supplies` which reduces the supply set to those the algorithm will definitely be able to collect. This is where most of the error by introducing heuristics can be found: we cannot guess the exact budget cost to pickup a supply is, so we approximate it. To reduce this error, we spend a large amount of time here.

    The `reconstruct_path` call is used to reconstruct entry to supply paths and entry paths, which are used in `get_reduced_supplies` to calculate approximate supply costs, and to reduce the budget to allow for an exit trip, respectively. 

    `get_supply_wing_paths`, the third largest cost in the algorithm, is responsible for deciding which supplies should be collected by paths through which junctions. It allows depth first search to be used when traversing the facility by not allowing CRUDY-1 to pick up supplies if the backtrack path isn't the shortest way to get that supply. This does introduce an error, as the shortest path to a supply may not be the optimal way to collect it.

    `dijkstra_to`, the fourth largest cost connects together the salient instructions returned by `clear_branch`. It uses the tree structure to reconstruct paths in $O(n)$ time, faster than running dijkstra's algorithm repeatedly.

    `flatten_graph`, the fifth largest cost, creates a flat graph for finding least-cost entry to supply and exit paths.

    `clear_branch`, the sixth largest cost, is where the majority of the code lies, and recursively clear branches, acting similar to depth first search. It introduces error in a simplification I decided to make due to the time restriction: if the sum of supply weight on the backtrack path to the previous junction or entry is greater than or equal to CRUDY-1's storage size, it will bring some of those supplies back. In many cases, it may be better to 'juggle' 2 high weight supplies to avoid wasting energy bring a 3 weight supply back by itself.
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4.3 Space Complexity
    One of the major improvements to the algorithm comes from the semantic change of *default copy* to *default in-place*. This small change reduces the main space costs of the recursive call to the only 1 variable not passed by reference: the backtrack list.

    The salient factors contributing to the space complexity are as follows:
    - The backtrack lists in `clear_junction_path`: Since CRUDY-1 will never need to go through the same junction more than once, it can only recurse at a depth $\propto |W_E|$. Each call of `clear_junction_path` can create a backtrack list of length at most $|V|$
    - The return value length is amortised to $O(|V| |S|)$ as discussed in the time complexity of `clear_junction_path`
    - The knapsack step in `get_reduced_supplies` creates a results list of at most length $C |S|$ which contains lists of length at most $|S|$
    - The knapsack step in `knapsack_supplies` creates a results list of length $B + 1$ which contains lists of length at most $|S|$.


    This gives a worst-case space complexity of $O(|V| |S| + |V| |W_E| + C|S|^2 + B|S|)$.

    In terms of the byte-length of the input $n$, this gives $O(n^3)$ space complexity.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5.1 Intractability of Exact Approaches
    The following discussions on intractability will be split into two cases: the case where CRUDY-1's ability to drop supplies is present and the case where it is not.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 5.1.1 No Supply Dropping
    Without supply dropping, the problem is equivalent to the **knapsack problem on dependent costs**, with capacity $C$ and costs dependent on other items in the knapsack. Since the knapsack problem is a reduction of this problem, the resulting problem is $\text{NP-Hard}$, unless $\text{P} = \text{NP}$.

    While $\text{NP-Hard}$ problems can be solved exactly, the algorithms to solve them will grow exponentially with $n$. For the **dependent-cost 0/1 knapsack problem**, it can be solved by a linear problem:
    $$
    \begin{darray}{rrll}
        \text{max} &\sum_{\mathclap{k \in \mathcal{P}(K)}} v_k x_k & & & \\
        \text{s.t.} &\sum_{\mathclap{k \in \mathcal{P}(K) \vert i \in k}} x_k &= 1 &\forall i \in K; \\
        &\sum_{\mathclap{k \in \mathcal{P}(K)}} c_k x_k &\leq C; \\
    \end{darray}
    $$
    where
    $$
    \begin{aligned}
    x_k &= \begin{dcases}
    1 & \text{all } i \in k \text{ are collected in one trip}\\
    0 & \text{otherwise}
    \end{dcases}\\
    v_k &= \displaystyle\sum\limits_{i \in k} \text{value of } k\\
    c_k &= \text{minimum cost of collection all } i \in k\\
    C &= \text{budget given to CRUDY-1}
    \end{aligned}
    $$
    Integer linear programs are NP-Complete, and this one has $3 \times |K|!$ constaints, meaning it would in theory be solved by a branch-and-bound algorithm.

    Furthermore, since the number of constrains, $m$, is fixed, and the coefficients of $x$ in a tabular (matrix) form the linear program are independent of other variables and bound within $[0, w_{max}]$, we know an algorithm exists that solves this in $O(n^{2m + 2} (m a)^{(m + 1) (2m + 1)}) = O(n^{6|K|! + 2} (3|K|! + w_{max})^{(3|K|! + 1)(6|K|! + 1)})$, but since the number of coefficients is dependent on $n$ non-polynomialy (notice $|K|!$ means $O(n!)$ bytes), there is no known pseudopolynomial time equation to solve this problem.
    """
          )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.1.2 With Supply Dropping
            With supply dropping, we can notice that we should never travel away from the entrance while holding a supply. This variation of the problem can be solved with the same dependent-cost 0/1 knapsack problem linear program, with different $v_k$.
        
            However, with supply order becoming non-salient with this change, near-optimal paths collecting a certain subset of the supplies can be found in polynomial time.
        
            Supply costs can also be better estimated independent of other supplies as will be shown below. These properties, as well as the potential to collect greater supplies from the facility guided the choice to focus on this sub-problem.
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 5.2 Local Optimal
            The algorithm presented finds a local optimal guided by the initial guess of supply costs in the knapsack step. While earlier other inaccuracies were disucssed in the `clear branches` procedure, these can only create marginal optimisations which add optimisation-like properties to the algorithm, which would make this algorithm run in exponential time.
        
            The knapsack supply cost estimation is the main loss of precision, as the algorithm will never collect more than the initial guess in value.
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.2.1 Supply Juggling Optimisation
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    juggling_slider = mo.ui.slider(0, 34, 1, value=0, show_value=True, label="Path length")
    return (juggling_slider,)


@app.cell(hide_code=True)
def _(draw_sub_facility, juggling_slider, mo, plt):
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(16, 8))
    _fig.patch.set_facecolor('#F5F7FA')
    _, _juggle_budget = draw_sub_facility(
        "With Juggling", _ax1, 4, 4, (2, 2), [(3, 3, 3), (2, 3, 3), (2, 0, 2), (3, 0, 2)],
        [(2, 2, 0), (2, 3, 1), (3, 3, 0), (3, 2, 0), (3, 1, 2), (3, 2, 0), (3, 3, 1), (3, 2, 0), (3, 1, 0), (2, 1, 2), (3, 1, 0), (3, 0, 1), (3, 1, 1), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 0, 0), (2, 0, 1), (3, 0, 0), (3, 1, 0), (2, 1, 1), (1, 1, 0), (1, 0, 0), (0, 0, 3)], juggling_slider.value + 1
    )
    _, _non_juggle_budget = draw_sub_facility(
        "Without Juggling", _ax2, 4, 4, (2, 2), [(3, 3, 3), (2, 3, 3), (2, 0, 2), (3, 0, 2)],
        [(2, 2, 0), (2, 3, 1), (3, 3, 0), (3, 2, 0), (3, 1, 0), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 3, 1), (3, 2, 0), (3, 1, 2), (3, 0, 1), (3, 1, 1), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 0, 0), (2, 0, 1), (3, 0, 0), (3, 1, 0), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3)], juggling_slider.value + 1
    )

    mo.vstack([mo.lazy(_fig, show_loading_indicator=True), mo.hstack([juggling_slider, mo.md(fr"""total budget used: {_juggle_budget} (juggle) / {_non_juggle_budget} (non-juggle)""")])])
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Juggle vs no juggle")}</span>

    Figure {get_fig("Juggle vs no juggle")} shows a marginal difference between worst-case situations when collecting supplies: CRUDY-1 discovers two 3-weight supplies, which it takes back to the entrance, whereas with juggling, it will take them back until it is able to take exactly 5 weight back. The juggling procedure was not implemented to reduce the complexity of the algorithm and due to time restrictions.

    This second approach is also sub-optimal, as it should check whether it will be able to take them back and find a 2-weight supply to pair with each 3-weight supply, if not it doesn't need to spend extra energy juggling the supplies.

    In the algorithm, it is randomised which branch it chooses: if it picks the one with the two 2-weight supplies, it will be better than the juggling algorithm. This choice, if made smartly by the algorithm reduces the number of situations juggling is preffered, but was not implemented due to time restrictions.
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    supply_dropping_slider = mo.ui.slider(0, 38, 1, value=0, show_value=True, label="Path length")
    return (supply_dropping_slider,)


@app.cell
def _(draw_sub_facility, mo, plt, supply_dropping_slider):
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(16, 8))
    _fig.patch.set_facecolor('#F5F7FA')
    _, _dropping_budget = draw_sub_facility(
        "With supply dropping", _ax1, 4, 4, (0, 0), [(3, 3, 3), (2, 3, 3), (2, 0, 2), (3, 0, 2)],
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 0, 0), (2, 0, 1), (3, 0, 1), (3, 1, 2), (2, 1, 2), (3, 1, 0), (3, 2, 0), (3, 3, 0), (2, 3, 1), (3, 3, 0), (3, 2, 0), (3, 1, 1), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 3, 1), (3, 2, 0), (3, 1, 0), (2, 1, 1), (1, 1, 0), (1, 0, 0), (0, 0, 3)], supply_dropping_slider.value + 1
    )
    _, _non_dropping_budget = draw_sub_facility(
        "Without supply dropping", _ax2, 4, 4, (0, 0), [(3, 3, 3), (2, 3, 3), (2, 0, 2), (3, 0, 2)],
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 0, 0), (2, 0, 1), (3, 0, 1), (3, 1, 0), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 3, 0), (2, 3, 1), (3, 3, 0), (3, 2, 0), (3, 1, 0), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3), (1, 0, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 3, 1), (3, 2, 0), (3, 1, 0), (2, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 3)], supply_dropping_slider.value + 1
    )

    mo.vstack([mo.lazy(_fig, show_loading_indicator=True), mo.hstack([supply_dropping_slider, mo.md(fr"""total budget used: {_dropping_budget} (supply drop) / {_non_dropping_budget} (no supply drop)""")])])
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Supply drop vs no supply drop")}</span>

    Figure {get_fig("Supply drop vs no supply drop")} shows a marginal difference between supply dropping and non-supply dropping walks. Without supply dropping, CRUDY-1 cannot collect the supply in the bottom right in the 2nd trip without incurring a cost of traversing with a large weight. With supply dropping it can do this
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 5.2.3 Supply Cost Bounds
            """
        )
    return


@app.cell
def _(mo):
    supply_cost_bound_slider = mo.ui.slider(1, 10, 1, value=5, show_value=True, label="Supply capacity")
    return (supply_cost_bound_slider,)


@app.cell
def _(mo, np, plt, supply_cost_bound_slider):
    _fig, _ax = plt.subplots(figsize=(10, 6))

    _x = np.linspace(0, supply_cost_bound_slider.value, 1000)

    _ub = _x + 2

    _lb = (supply_cost_bound_slider.value + 2) * _x / supply_cost_bound_slider.value

    _function = (1 - (_x / supply_cost_bound_slider.value) ** 0.4) * _lb + ((_x / supply_cost_bound_slider.value) ** 0.4) * _ub

    _ax.plot(_x, _ub, color="red", label=r"Upper bound: $f_{ub}(w, C) = w + 2$")

    _ax.plot(_x, _lb, color="blue", label=r"Lower bound: $f_{lb}(w, C) = (C + 2) \frac{w}{C}$")

    _ax.plot(_x, _function, color="green", label=r"Cost function: $f(w, C) = (1 - \left(\frac{w}{C})^{0.45}\right)f_{lb}(w, C) + \left(\frac{w}{C}\right)^{0.45} f_{ub}(w, C)$")

    _ax.legend()
    _ax.set_title("Upper and lower bounds of supply cost")
    _ax.set_xlim(0, supply_cost_bound_slider.value)
    _ax.set_ylim(0, supply_cost_bound_slider.value + 2)

    _ax.set_xlabel("Supply weight")
    _ax.set_ylabel("Supply cost")

    _fig.tight_layout()
    mo.vstack(
        [
            mo.lazy(_fig, show_loading_indicator=True),
            supply_cost_bound_slider,
        ], align="center"
    )
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Supply cost bounds")}</span>

    Figure {get_fig("Supply cost bounds")} shows the upper bound and lower bound costs of collecting a supply, where $w$ is the weight of the supply and $C$ is CRUDY-1's supply capacity:
    - Upper bound: the trip being going to the supply, picking it up and bringing it back to the entrance and dropping it off, which has function $f_{{ub}}(w, C) = w + 2$
    - Lower bound: the trip being going to the supply, picking it, and more supplies to add up to $C$ total weight, then bringing them back to the entrance and dropping them off, where each supply has cost given by $f_{{lb}}(w, C) = (C + 2) \frac{{w}}{{C}} = w + \frac{{2w}}{{C}}$
    - The proposed function is a linear interpolation between the two functions, $f(w, C) = \operatorname{{lerp}}(f_{{lb}}(w, C), f_{{ub}}(w, C), t)$, with $t = \left(\frac{{w}}{{C}}\right) ^ d$, with $d = 0.45$ being a value found that gives low-variance results on budget use for 60% and 35% full and reserve budgets.

    Possible weight-cost functions would be of form $w + \Delta\left(\frac{{w}}{{C}}\right) \vert \Delta: [0, 1] \to \mathbb{{R}}, \ \operatorname{{range}}(\Delta) \subseteq [\frac{{2w}}{{C}}, 2]$, where the function I chose can be expressed with $\Delta(x) = 2x^{{1.45}} + 2x + 2x^{{0.45}}$.

    Of course, no function could, independent of other supply positions, predict exact costs for collecting a supply. We can calculate the error by getting the maximum of the difference between $f$ and $f_{{lb}}$ as a proportion of $f_{{lb}}$ by solving DE

    $$\begin{{align*}}
    \frac{{d}}{{dw}} \left( \frac{{f(w, 5) - f_{{lb}}(w, 5)}}{{f_{{lb}}(w, 5)}} \right) &= 0\\
    \frac{{d}}{{dw}} \left( \frac{{w + 2\left(\frac{{w}}{{5}}\right)^{{1.45}} + \frac{{2w}}{{5}} + 2\left(\frac{{w}}{{5}}\right)^{{0.45}} - w - \frac{{2w}}{{5}}}}{{w + \frac{{2w}}{{5}}}}\right) &= 0\\
    \frac{{d}}{{dw}} \left( \frac{{\left(\frac{{w}}{{5}}\right)^{{0.45}} \left(1 + \frac{{w}}{{5}}\right)}}{{\frac{{7w}}{{5}}}} \right) &= 0\\
    \frac{{d}}{{dw}} \left( \frac{{w^{{0.45}} \left(5 + w\right)}}{{w}} \right) &= 0\\
    \frac{{d}}{{dw}} \left( w^{{-0.55}} \left(5 + w\right) \right) &= 0\\
    \displaystyle\int_0^w 5w^{{-0.55}} + w^{{0.45}} \, dw &= 0 \text{{ (using }} f(0, 5) = f_{{lv}}(0, 5) = 0\text{{)}}\\
    \biggl[\frac{{100}}{{9}} w^\frac{{9}}{{20}} + \frac{{20}}{{29}} w^{{1.45}}\biggr]_0^w &= 0\\
    \frac{{100}}{{9}} w^\frac{{9}}{{20}} + \frac{{20}}{{29}} w^{{1.45}} &= 0\\
    w &= 0
    \end{{align*}}$$

    Which means the proportion between them is constantly decreasing, so the maximum proportion will be for 1-weight supplies, which is $\epsilon = \frac{{f(1, 5) - f_{{lb}}(1, 5)}}{{f_{{lb}}(1, 5)}} \approx 0.5539$. 

    While this in theory could have a error on value $(1 - \epsilon)$, this problem is unsolved as far as I can tell, with only sensitivity analysis on the knapsack problem being done on 1-item perturbations: [Sensitivity analysis of the optimum to perturbation of the profit of a subset of items in the binary knapsack problem](https://doi.org/10.1016/j.disopt.2008.05.001).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5.3 Error Bounding
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            While it is difficult to bound the error by a value $\epsilon$, it is possible to determine probabilities of using a certain percentage of the budget or collecting a percentage of the total value of the supplies. After presenting these, I will present a hard, likely unachievable upper bound on value collected, graphed against the output's collected value to find the average maximal difference between the value collected by the algorithm and the optimal value collected, which will then be compared against a naive, greedy approach.
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.3.1 Budget Proportion
            """
        )
    return


@app.cell(hide_code=True)
def _(math, mo, np, pd, plt, scipy):
    _df = pd.read_csv("memo3/data/data_facility_small.csv")
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 6))

    def _graph(df, ax, budget_percent):
        df = df[df["budget"] != 0]

        df = df[df["budget percent"] == budget_percent]

        data = df["budget used"] / df["budget"]

        kde = scipy.stats.gaussian_kde(data)
        xx = np.linspace(data.min(), data.max(), 1000)

        ax.hist(data, density=True, bins=[float(i) / 100 for i in range(math.floor(data.min() * 100), math.ceil(data.max() * 100), 1)], color="#74c7ec")

        ax.set_title(f"Proportion of budget used with {budget_percent}% budget")

        return ax.plot(xx, kde(xx), color="#ff4d00")

    _graph(_df, _ax1, 60)
    _graph(_df, _ax2, 35)

    _fig.supxlabel("Proportion of budget used")
    _fig.supylabel("Percent")
    _fig.tight_layout()

    mo.lazy(_fig, show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def _(get_fig, mo, np, pd, scipy):
    def _scientific_latex(n):
        if n != 0:
            splits = np.format_float_scientific(n, precision=4).split('e')
            return splits[0] + r"\mathrm{e}{" + splits[1] + '}'
        return r"0\ \text{(to 300 decimal places)}"

    def _get_paragraph(df, budget_percent):
        df = df[df["budget"] != 0]
        df = df[df["budget percent"] == budget_percent]
        data = df["budget used"] / df["budget"]
        p_val = scipy.stats.norm.pdf(1, loc=data.mean(), scale=data.std())
        return fr"""With $B_{{{budget_percent}}} \sim N(\mu \approx {data.mean().round(4)}, \sigma^2 \approx {data.std().round(4)} ^ 2)$, we can calculate there is a $p = \Pr(B_{{{budget_percent}}} \gt 1) = {_scientific_latex(p_val)}$ chance of going over budget, equivalent to a **1 in {str(int(np.floor(np.reciprocal(p_val))) if not p_val == 0.0 else np.inf).replace("inf", r"$\infty$")}** chance."""

    _df = pd.read_csv("memo3/data/data_facility_small.csv")

    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Budget bound main")}</span>

    Figure {get_fig("Budget bound main")} shows the used budget as a proportion of budget use in trips found by the algorithm on the main problem instance.

    {_get_paragraph(_df, 60)}

    {_get_paragraph(_df, 35)}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.3.2 Value Proportion
            """
        )
    return


@app.cell
def _(math, mo, np, pd, plt, scipy):
    _df = pd.read_csv("memo3/data/data_facility_small.csv")
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 6))

    def _graph(df, ax, budget_percent):
        df = df[df["value total"] != 0]

        df = df[df["budget percent"] == budget_percent]

        data = df["value collected"] / df["value total"]

        kde = scipy.stats.gaussian_kde(data)
        xx = np.linspace(data.min(), data.max(), 1000)

        ax.hist(data, density=True, bins=[float(i) / 100 for i in range(math.floor(data.min() * 100), math.ceil(data.max() * 100), 1)], color="#74c7ec")

        ax.set_title(f"Proportion of value collected with {budget_percent}% budget")

        return ax.plot(xx, kde(xx), color="#ff4d00")

    _graph(_df, _ax1, 60)
    _graph(_df, _ax2, 35)

    _fig.supxlabel("Proportion of value collected")
    _fig.supylabel("Percent")
    _fig.tight_layout()

    mo.lazy(_fig, show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def _(get_fig, mo, np, pd, scipy):
    _df = pd.read_csv("memo3/data/data_facility_small.csv")

    def _scientific_latex(n):
        if n != 0:
            splits = np.format_float_scientific(n, precision=4).split('e')
            return splits[0] + r"\mathrm{e}{" + splits[1] + '}'
        return r"0\ \text{(to 300 decimal places)}"

    def _get_paragraph(df, budget_percent):
        df = df[df["value total"] != 0]
        df = df[df["budget percent"] == budget_percent]
        data = df["value collected"] / df["value total"]
        p_val = scipy.stats.norm.pdf(budget_percent, loc=data.mean(), scale=data.std())
        return fr"""With $V_{{{budget_percent}}} \sim N(\mu \approx {data.mean().round(4)}, \sigma^2 \approx {data.std().round(4)} ^ 2)$, we can calculate there is a $p = \Pr(V_{{{budget_percent}}} \lt {budget_percent / 100}) \approx {_scientific_latex(p_val)}$ chance of collecting less than the amount of value that the budget was calculated to collect, equivalent to a **1 in {str(int(np.floor(np.reciprocal(p_val))) if not p_val == 0.0 else np.inf).replace("inf", r"$\infty$")}** chance."""

    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Value bound main")}</span>

    Figure {get_fig("Value bound main")} shows the collected value as a proportion of possible-to-collect value in the facility by trips found by the algorithm on the main problem instance. 

    {_get_paragraph(_df, 60)}

    {_get_paragraph(_df, 35)}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.3.3 Over Budget
            """
        )
    return


@app.cell
def _(mo, np, pd, plt):
    _df = pd.read_csv("memo3/data/data_facility_small.csv")
    _fig, _ax = plt.subplots(figsize=(14, 6))

    _max_budget = _df["budget"].max()
    _max_budget_used = _df["budget used"].max()

    _x = np.linspace(0, max(_max_budget, _max_budget_used), 1000)
    for _c, _percent in [("blue", 35), ("red", 60)]:
        _c_df = _df[_df["budget percent"] == _percent]
        _ax.scatter(_c_df["budget"], _c_df["budget used"], c=_c, alpha=1, label=f"{_percent}% budget")
    _ax.plot(_x, _x, c="green", label="Over/Under budget seperator")

    _ax.set_xlim(0, _max_budget)
    _ax.set_ylim(0, _max_budget_used)

    _ax.set_xlabel("Budget")
    _ax.set_ylabel("Budget used")

    _ax.legend()
    _ax.set_title("Over/Under Budget of Outputs")

    _fig.tight_layout()

    mo.lazy(_fig, show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Budget vs Budget Used")}</span>

    Figure {get_fig("Budget vs Budget Used")} shows the budget vs budget used, along with a line with gradient = 1. This shows the 4 outliers that go over budget: all between 2000 and 6000 budget. It also shows the gap between the budget and budget used widens as the budget gets larger. This likely means the cost function should take the budget amount as an input.

    This cost function optimisation could also be done by a neural network and the `get_weight_cost` function could become a neural network instead of a multi-variable mathematical function. In future, this network could also take as input the rest of the supplies' distances from the current or various other variables to more closely approximate the real cost which is dependent on all these factors
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.3.4 Optimality Bounding
            """
        )
    return


@app.cell
def _(math, mo, np, pd, plt, scipy):
    _df = pd.read_csv("memo3/data/data_facility_small.csv")
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 6))

    def _graph(df, ax, budget_percent):
        df = df[df["value total"] != 0]

        df = df[df["budget percent"] == budget_percent]

        data = 1 - df["value collected"] / df["value upper"]

        kde = scipy.stats.gaussian_kde(data)
        xx = np.linspace(data.min(), data.max(), 1000)

        ax.hist(data, density=True, bins=[float(i) / 100 for i in range(math.floor(data.min() * 100), math.ceil(data.max() * 100), 1)], color="#74c7ec")

        ax.set_title(f"Maximal optimality gap with {budget_percent}% budget")
        ax.set_xlabel("Maximal optimality gap")
        ax.set_ylabel("Percentage")

        return ax.plot(xx, kde(xx), color="#ff4d00")

    _graph(_df, _ax1, 60)
    _graph(_df, _ax2, 35)

    _fig.tight_layout()

    mo.lazy(_fig, show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Optimality gap")}</span>

    Figure {get_fig("Optimality gap")} shows the maximal gap between a optimal output and the output given by the algorithm. This shows the algorithm, in the 60% budget case, is on average within 25% of this optimal &mdash; which is likely not achieveable. T

    his helps explain the 40% gap seen in the 35% budget case: it is very likely the optimal will be much lower and be closer to the gap seen in the 60% case as more trips will be not full capacity ones in the 35% budget case. 

    Additionally, there is **always** a section of the collection of a supply: the part until it reaches a sector of the facility that lies in the least-cost path to the entrance of another supply which is always evaluated with the upper-bound cost
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ### 5.3.5 Naive Lower Bounding
            """
        )
    return


@app.cell
def _(math, mo, np, pd, plt, scipy):
    _df = pd.read_csv("memo3/data/data_facility_small.csv")
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 6))

    def _graph(df, ax, budget_percent):
        df = df[df["value total"] != 0]

        df = df[df["budget percent"] == budget_percent]

        data = 1 - df["value collected"] / df["value lower"]

        kde = scipy.stats.gaussian_kde(data)
        xx = np.linspace(data.min(), data.max(), 1000)

        ax.hist(data, density=True, bins=[float(i) / 100 for i in range(math.floor(data.min() * 100), math.ceil(data.max() * 100), 1)], color="#74c7ec")

        ax.set_title(f"Maximal naive lower-bound gap with {budget_percent}% budget")
        ax.set_xlabel("Maximal naive lower-bound gap")
        ax.set_ylabel("Percentage")

        return ax.plot(xx, kde(xx), color="#ff4d00")

    _graph(_df, _ax1, 60)
    _graph(_df, _ax2, 35)

    _fig.tight_layout()

    mo.lazy(_fig, show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("lower-bound gap")}</span>

    Figure {get_fig("lower-bound gap")} shows the gap between the algorithmic output and a naive lower-bound, calculated with each supply being collected individually. These graphs show what I have previously mentioned: this algorithm will always return a walk that is at least as good as these lower bounds, and that this 'naive' lower-bound is actually pretty good.

    This might mean local-search methods like 2-opt and Lin-Kernighan, which were tested on the first memo, may have fared well on both the non-supply dropping and supply dropping sub-problems, as this almost instantly calculatable lower-bound value collection is within 8-10% of a much more complex algorithm's output.
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 6 Real-world application
    """)
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(
        rf"""
    ## 6.1 Real Hardware
    {mo.image("memo3/media/c++impl_flame.png")}
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("C++ flame graph")}</span>

    Figure {get_fig("C++ flame graph")} shows a flame graph of the run-time costs of the algorithm implemented in C++. 

    The algorithm has greater costs in clear_branch, likely due to me treating copying of lists into other lists to be constant time, which it isn't in practise. There are likely also other costs like function call, vector resizing and non-constant costs for each ADT operation which contribute to the predicted operation count being different from the one in the implementation.

    For this algorithm to be suitable for real-world problems &mdash; where time and effort of computation directly reduces battery and can be the difference between a successful extraction and a failed one &mdash; this algorithm sacrifices optimality for its speed: 1.5 MOP can be calculated in 10ms on a 120MOP/s CPU. Due to the main DFS structure of `clear_branch` it is easily parallelisable with few changes, which would also aids its computational efficiency.

    With the previous dynamic programming approach, 50 supplies would not be completable both due to the time to complete and the storage to hold the memo-table. 5 supplies was around the limit for that algorithm, as it was close to going over the one second arbitrary budget I decided on. Each running of the algorithm on 50 supplies would take 1MOP and this would have to be done $\approx 10 \binom{{50}}{{5}} = 21,187,600$ times. This would be computable by computer networks and super computers but out of the range of embedded systems, and this doesn't even account for the added complexity of non-uniform supply weights, priorities and the budget not being enough to pick up all the supplies.
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 6.2 Real Guarantees
            As discussed previously, the algorithm has very low probability of going over budget. This can be increased by changing the cost function's $\Delta(w, C)$ function to be closer to $f_{ub}(w, C)$ if more precision is required.
        
            If a guarantee is required, though, the algorithm is not very efficient, as a trip as good as the upper bound function is trivial to create by collecting each supply individually. Additionally, a optimisation of this trip is also trivial: for each supply, it can check if collecting that supply in the same trip as the current one is cheaper than collecting the supplies individually.
        
            In this case &mdash; a hard guarantee required as opposed to a probablistic one &mdash; this algorithm would *not* be as suitable as the previously suggested one. Even in the 40000 trials used in testing the algorithm, an outlier which went over budget was found. This result will on average (median) appear every 250 million trials.
            """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 6.3 Real Implementation
            Due to time restrictions, the coherance of the algorithm was compromised for it's safety guarantees. Some optimisations, such as not checking for supplies in the same sectors in *all* supply collecting loops even when the algorithm guarantees they cannot be there, were not made which has effects on theoretical worst-case time complexity of the algorithm.
        
            Other optimisations not made include not checking for supplies in the branch-origin sector, which *does* have real effects on the algorithm's run-time. This reduces the conciseness of the algorithm, but overall it doesn't reduce the many edge-case checking which leads to bloated procedures.
        
            These all reduce coherance, but the actual control flow of the algorithm: being depth-first search helps aid it's coherance.
            """
        )
    return


@app.cell(hide_code=True)
def algorithm_explorer_header(mo):
    mo.md(r"""
    # 7 Algorithm
    """
          )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
            ## 7.1 Pseudocode
            """
        )
    return


@app.cell(hide_code=True)
def _(mo, pseudocode_explorer, re):
    _dict = {"Full": mo.md(fr"""{pseudocode_explorer.get_lines_fancy(numbered=True)}""")}

    for _match in re.finditer("FUNCTION ([^\()]+)", pseudocode_explorer.raw_pseudocode):
        _dict[_match.group(1)] = mo.md(fr"""{pseudocode_explorer.get_fn_fancy(_match.group(1), numbered=True)}""")

    for _match in re.finditer("PROCEDURE ([^\()]+)", pseudocode_explorer.raw_pseudocode):
        _dict[_match.group(1)] = mo.md(fr"""{pseudocode_explorer.get_fn_fancy(_match.group(1), numbered=True)}""")


    mo.ui.tabs(_dict, value="ember_rescue")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6.1 Algorithm explorer
    """)
    return


@app.cell
def algorithm_resource(facility_drawer, mo):
    import memo3_algorithm

    _abs_graph = facility_drawer.get_abstracted_graph()
    _entry = facility_drawer.entry
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _masses = facility_drawer.masses
    _values = facility_drawer.values
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}
    _budget = facility_drawer.budget

    _trials = 1

    def _get_runtime(trials: int = 1) -> float:
        if trials < 1:
            return 0

        """source: https://docs.python.org/3/library/profile.html"""

        import cProfile, pstats
        from pstats import SortKey
        pr = cProfile.Profile()
        pr.enable()
        for i in range(trials):
            memo3_algorithm.ember_rescue(_abs_graph, _entry, _exits, _supplies, _masses, _values, _supply_map, set(), _budget, 5)
        pr.disable()
        ps = pstats.Stats(pr).sort_stats(SortKey.CUMULATIVE)
        return ps.stats[tuple(next(s for s in ps.stats if 'ember_rescue' in s))][3] / trials

    def _get_mem() -> float:

        """source: https://docs.python.org/3/library/tracemalloc.html"""

        import tracemalloc

        tracemalloc.start()

        memo3_algorithm.ember_rescue(_abs_graph, _entry, _exits, _supplies, _masses, _values, _supply_map, set(), _budget, 5)

        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        top_stats = snapshot.statistics('filename')
        return sum(stat.size for stat in top_stats if "memo3_algorithm.py" in stat.traceback._frames[0][0])

    _ave_mem = round(sum([_get_mem() for _ in range(_trials)]) / _trials)


    mo.hstack(
        [
            mo.lazy(mo.stat(label="Runtime (Python):", value=f"{_get_runtime(_trials) * 1000:.2f}ms"), show_loading_indicator=True),
            mo.lazy(mo.stat(label="Memory (Python):", value=f"{round(sum([_get_mem() for _ in range(_trials)]) / _trials)} B"), show_loading_indicator=True)
        ], justify="center", gap="2rem"
    )
    return (memo3_algorithm,)


@app.cell(hide_code=True)
def algorithm_resource_note(mo):
    mo.md(r"""
    These value **HIGHLY** depend on the marimo virtual machine, and can vary by orders of magnitude. On my machine, I get Runtime: 8.19ms, Memory: 8547 B
    """)
    return


@app.cell
def algorithm_explorer_controls(facility_drawer, memo3_algorithm, mo):
    _abs_graph = facility_drawer.get_abstracted_graph()
    _entry = facility_drawer.entry
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _masses = facility_drawer.masses
    _values = facility_drawer.values
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}
    _budget = facility_drawer.budget

    # @mo.cache
    def ember_rescue_cached():
        return memo3_algorithm.ember_rescue(_abs_graph, _entry, _exits, _supplies, _masses, _values, _supply_map, set(), _budget, 5)

    _path = ember_rescue_cached()

    path_len = mo.ui.slider(
        value=len(_path),
        start=0,
        stop=len(_path),
        step=1,
        label="Step (drag to walk through the facility)",
        full_width=True,
        include_input=True
    )
    return ember_rescue_cached, path_len


@app.cell
def algorithm_explorer_controls_and_info(
    ember_rescue_cached,
    facility_drawer,
    mo,
    path_len,
):
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _storage = tuple([None] * 5)
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}

    _path = ember_rescue_cached()

    def _has_edge(u, v) -> bool:
        if u[0] == v[0]:
            u = u[1:]
            v = v[1:]
            return any(wing.has_edge(u, v) for wing in facility_drawer.wings)
        else:
            return (u, v) in facility_drawer.junctions or (v, u) in facility_drawer.junctions

    _collected_supplies, _used_budget, _trip_supplies, _ = facility_drawer.get_plan_info(_path[:path_len.value])
    _used_budget = sum(_used_budget)
    # _collected_supplies, _used_budget, _trip_supplies = [], 1e9, []

    highlight_trip = mo.ui.slider(
        value=len(_trip_supplies) + 1,
        start=1,
        stop=len(_trip_supplies) + 1,
        step=1,
        label="Trip (drag to highlight a trip or to end for no highlight)",
        full_width=True,
        include_input=True
    )

    mo.vstack(
        [
            mo.hstack(
                [
                    mo.lazy(mo.stat(
                        label="Total instructions",
                        value=f"{len(_path) - 1} steps"
                    ), show_loading_indicator=True),
                    mo.lazy(mo.stat(
                        label="Supplies collected",
                        value=f"{len(_collected_supplies)}/{len(facility_drawer.supplies)}"
                    ), show_loading_indicator=True),
                    mo.lazy(mo.stat(
                        label="Supply priority collected",
                        value=f"{sum(facility_drawer.values[s] for s in _collected_supplies)}/{sum(facility_drawer.values[s] for s in facility_drawer.supplies)}"
                    ), show_loading_indicator=True),
                    mo.lazy(mo.stat(
                        label="Budget used",
                        value=f"{_used_budget}/{facility_drawer.budget}"
                    ), show_loading_indicator=True),
                    mo.lazy(mo.stat(
                        label="Ends at exit",
                        value="✅ Yes" if _path[-1][0] in _exits else "❌ No"
                    ), show_loading_indicator=True),
                    mo.lazy(mo.stat(
                        label="All moves valid",
                        value="✅ Yes" if all(_has_edge(_path[i][0], _path[i + 1][0]) for i in range(path_len.value - 1) if _path[i][0] != _path[i + 1][0]) else "❌ No"
                    ), show_loading_indicator=True)
                ], gap=1, wrap=True
            ),
            path_len,
            highlight_trip
        ]
    )
    return (highlight_trip,)


@app.cell
def _(ember_rescue_cached, facility_drawer, highlight_trip, mo):
    _path = ember_rescue_cached()
    _, _trip_costs, _trip_supplies, _trip_move_supplies = facility_drawer.get_plan_info(_path)
    # _trip_supplies, _trip_move_supplies = [], [{}]

    _ordered = []
    if highlight_trip.value != highlight_trip.stop:
        _ordered = list(i for i, n in _trip_move_supplies[highlight_trip.value - 1].items() if n != facility_drawer.entry)

    def join_and(l: list):
        if not isinstance(l, list):
            l = list(l)
        if len(l) == 0:
            return ""
        if len(l) == 1:
            return str(l[0])
        return f"{", ".join(str(s) for s in l[:-1])} and {l[-1]}"

    mo.lazy(mo.md(fr"""
    {f"Collecting supplies at {join_and(_trip_supplies[highlight_trip.value - 1])}" if highlight_trip.value != highlight_trip.stop - 1 else ""}
    {f"\nWeights: {join_and([facility_drawer.masses[s] for s in _trip_supplies[highlight_trip.value - 1]])}" if highlight_trip.value != highlight_trip.stop - 1 else ""}

    {f"Moving suppl{"ies" if len(_ordered) > 1 else "y"} at {join_and([facility_drawer.supplies[i] for i in _ordered])} to {join_and([_trip_move_supplies[highlight_trip.value - 1][i] for i in _ordered])}" if len(_ordered) > 0 else ""}

    Trip cost: {_trip_costs[highlight_trip.value - 1]}
    """)) if highlight_trip.value != highlight_trip.stop else None
    return


@app.cell
def algorithm_explorer(
    ember_rescue_cached,
    facility_drawer,
    highlight_trip,
    mo,
    path_len,
):
    _path = ember_rescue_cached()

    mo.lazy(facility_drawer.draw_multi_wing(plan=_path[:path_len.value + 1], highlight_trip=highlight_trip.value - 1 if highlight_trip.value != highlight_trip.stop else None), show_loading_indicator=True)
    return


@app.cell(hide_code=True)
def appendix(mo):
    mo.md(r"""
    # 8 Appendix
    """)
    return


@app.cell(hide_code=True)
def references(mo):
    mo.md(f"""
    ## 8.1 References\n{open("memo3/references.txt", "r", encoding="utf-8").read()}
    """)
    return


if __name__ == "__main__":
    app.run()
