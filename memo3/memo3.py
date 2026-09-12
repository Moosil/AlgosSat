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
    import re

    return itertools, mcolors, mo, np, nx, plt, random, re


@app.cell
def global_vars():
    # Globals
    _figure_names = []

    def get_fig(figure_name: str) -> int:
        if figure_name in _figure_names:
            return _figure_names.index(figure_name) + 1
        else:
            _figure_names.append(figure_name)
            return len(_figure_names)

    return


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

        def get_collected_supplies_and_budget(self, plan):
            curr_supply_locations = self.supplies.copy()
            total_energy_cost = 0
            if plan and len(plan) > 0:
                i = 0
                curr_loc = self.entry
                curr_trip = []
                curr_supplies = []
                while i < len(plan):
                    curr = plan[i]
                    if isinstance(curr, str):
                        if curr == "pickup":
                            index = curr_supply_locations.index(curr_loc)
                            while index in curr_supplies:
                                index = curr_supply_locations.index(curr_loc, index + 1)
                            curr_supplies.append(index)
                        else:
                            curr_supply_locations[curr_supplies.pop()] = curr_loc
                    else:
                        mass_total = sum([self.masses[self.supplies[s]] for s in curr_supplies])
                        total_energy_cost += (1 + mass_total) * self.G.get_edge_data(curr_loc, curr)["weight"]
                        curr_loc = curr
                        curr_trip.append(curr)

                        if curr == self.entry or curr == self.exit_a or curr == self.exit_b:
                            # number the trip at its first collection point
    
                            curr_trip = [self.entry]

                    i += 1
        
            return [self.supplies[i] for i, s in enumerate(curr_supply_locations) if s == self.entry], total_energy_cost

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
            self, plan=None, abandoned=None, show_labels=True, title="Weighted Multi-Wing Facility"
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
            curr_supply_locations = self.supplies.copy()
            if plan and len(plan) > 0:
                i = 0
                curr_loc = self.entry
                curr_trip = []
                total_energy_cost = 0
                curr_supplies = []
                trip_first_supply = None
                col = TRIP_COLOURS[trip_count % len(TRIP_COLOURS)]
                while i < len(plan):
                    curr = plan[i]
                    trip_of[curr] = col
                    if isinstance(curr, str):
                        if curr == "pickup":
                            index = curr_supply_locations.index(curr_loc)
                            while index in curr_supplies:
                                index = curr_supply_locations.index(curr_loc, index + 1)
                            curr_supplies.append(index)
                            if trip_first_supply is None:
                                trip_first_supply = curr_loc
                        else:
                            curr_supply_locations[curr_supplies.pop()] = curr_loc
                    else:
                        mass_total = sum([self.masses[self.supplies[s]] for s in curr_supplies])
                        total_energy_cost += (1 + mass_total) * self.G.get_edge_data(curr_loc, curr)["weight"]
                        xs = [xoff(n[0]) + n[1] + 0.5 for n in [curr_loc, curr]]
                        ys = [n[2] + 0.5 for n in [curr_loc, curr]]
                        # white underlay keeps overlapping routes legible
                        ax.plot(
                            xs, ys, color='white', lw=6.4, alpha=0.85, zorder=6,
                            solid_capstyle='round'
                        )
                        ax.plot(
                            xs, ys, color=col, lw=3.6, alpha=0.95, zorder=7,
                            solid_capstyle='round'
                        )
                        curr_loc = curr
                        curr_trip.append(curr)

                    if curr == self.entry or curr == self.exit_a or curr == self.exit_b:
                        # number the trip at its first collection point

                        if trip_first_supply:
                            ax.text(
                                xoff(trip_first_supply[0]) + trip_first_supply[1] + 0.5, trip_first_supply[2] + 0.5, total_energy_cost,
                                ha='center', va='center', fontsize=6.5,
                                fontweight='bold', color='white', zorder=13,
                                bbox=dict(
                                    boxstyle='circle,pad=0.16', fc=col,
                                    ec='white', lw=0.7
                                )
                            )

                        trip_first_supply = None
                        trip_count += 1
                        curr_trip = [self.entry]
                        col = TRIP_COLOURS[trip_count % len(TRIP_COLOURS)]

                    i += 1

                col = TRIP_COLOURS[(trip_count - 1) % len(TRIP_COLOURS)]
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
            abandoned = set(abandoned or [])
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
    return (facility_drawer,)


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

        def get_lines_fancy(self, start: int, stop: int, font_size: int = 12, numbered: bool = False):
            return mo.md(
                rf"""
        <div style="font-family: monospace; font-size: {font_size}px; white-space: pre-wrap;">{self.get_lines(start, stop, numbered)}</div>
        """
            )

        def get_lines(self, start: int, stop: int, numbered: bool, *, start_number_offset: int = 0, first_not_numbered: bool = True):
            if numbered:
                splits = self.full_pseudocode.split('<br>')[start:stop]
                pad = int(np.ceil(np.log10(len(splits))))
                res = "" if first_not_numbered else f"<span class='pseudocode-bracket'>[{start_number_offset:0{pad}}]</span>"
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

            for command in ["AND", "OR", "NOT", "RAISE", "DO", "THEN", "IN", "TO", "RETURN"]:
                res = re.sub(fr"(?:(?<=\s)|(?<=&#9;)|(?<=\<br\>)){command}(?:(?=\s)|(?=&#9;)|(?=\<br\>))", f"<span class='pseudocode-command'>{command}</span>", res)

            for operator in [r"<-", "=", ">", "<", "<=", ">=", "+", "-"]:
                res = re.sub(fr"(?<= ){operator}(?= )", f"<span class='pseudocode-op'>{operator}</span>", res)

            res = re.sub(r"∅", "<span class='pseudocode-bracket'>∅</span>", res)
            for bracket in ["[", "]", "(", ")"]:
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

                end = p_str.find(f"END {find_str}", i + len(find_str))
                if end == -1:
                    return p_str
                substr = p_str[i:end]
                substr = syntax_highlight_name(substr, param_names, "pseudocode-param")
                return p_str[:i] + substr + p_str[end:]

            adt_operators = [
                "get_vertices", "get_edges", "add_vertex", "add_edge", "remove_vertex", "remove_edge", "get_neighbours", "has_edge", "get_vertices", "set_edge_weight", "get_edge_weight", "union", "intersection", "difference", 'symmetric_difference', "size", 'element_of', "strict_subset_of", "subset_of", "are_equal", "size", "has", "at", "remove", "set", "get_keys", "push", "pop", "get", "set", "get", "length",
                "enqueue", "update_priority"
            ]

            res = syntax_highlight_name(res, list(set(adt_operators)) + ["List", "Array", "Set", "Map", "Graph", "Tuple", "Priority Queue", "Positive Integer", "Integer", "Real"], "pseudocode-atomic")
            res = syntax_highlight_name(res, list(set(procedures)), "pseudocode-proc")
            res = syntax_highlight_name(res, ["SupplyID", "Vertex"], "pseudocode-type")

            res = find_all(res, "PROCEDURE</span>", syntax_highlight_proc)
            res = find_all(res, "FUNCTION</span>", syntax_highlight_proc)

            return res

    pseudocode_explorer = PseudocodeExplorer("memo2/raw_pseudocode.txt")

    pseudocode_explorer_old = PseudocodeExplorer("memo1a1/raw_pseudocode.txt")
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
def title(mo):
    mo.md(r"""
    # Memo 3
    """)
    return


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
    # Problem abstraction
    Let $G = (V_w, E_w, w)$ be a meta-graph, with $V_w=\{W_1, W_2, \dots, W_k\}$ being a set of undirected weighted graphs, $E_w \subseteq \{\{u, v\} \vert u \in V_n, v \in V_m, n \neq m\}$ being a set of edges between adjacent wings, $W_n, W_m$ of the facility, with $k$ being the number of wings in the facility, and $\forall n \leq k, W_n = (V_n, E_n)$.

    $V = V_1 \cup V_2 \cup \dots \cup V_k$ and $\forall n, m \leq k, V_n \cap V_m = \varnothing \iff n \neq m$ and $V_n = V_m \iff n = m$, with $V$ representing the salient sectors of the facility $E = E_1 \cup E_2 \cup \dots \cup E_k$ and $\forall n, m \leq k, E_n \cap E_m = \varnothing \iff n \neq m$ and $E_n = E_m \iff n = m$, with $E$ representing the paths between those adjacent salient sectors, and positive integer edge weight function $w: E \cup E_w \to \mathbb{N}$ representing the total cost of traversing the span of sectors  which are adjacent to just two other sectors and between two salient sectors. If $(u, v) \notin E$, define $w(u, v) = \infty$.

    We will designate source vertex $s \in V$, the set of sink vertices $X \subseteq V$, and the set of supply vertices $S \subseteq V$, each representing the entry, exit, and supply unit-containing sectors respectively.

    To abstract the supply weights and priorities, we will have $\delta: S \to \mathbb{N}$ and $p: S \to \mathbb{Z}$ represent functions mapping each supply to a weight and priority repectively.

    We will have $A$ be an list representing CRUDY-1's supply unit storage, which contains `SupplyID`s of each supply it is carrying, function $M: S \to \text{SupplyID}$ mapping each supply vertex to its `SupplyID`, and set $F$ be the set of found `SupplyID`s. When a supply is collected, it will be added to $A$, and $A_\text{new}$ will be returned.

    We will be designing an algorithm to traverse meta-graph $G$, from $s$ to an $x$, returning an ordered sequence of vertices representing which vertices CRUDY-1 will travel through, an ordered sequence of integers which tells CRUDY-1 to traverse normally (0), pick up a supply (1), or drop off a supply (2+) with a specific index, and a ordered sequence of `SupplyID`s representing each supply CRUDY-1 has brought to the entry.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.1 Signature specification:
    $\text{ember\_rescue}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \times \text{List}[\text{SupplyID}] \times \text{Map}[\text{Vertex}, \text{SupplyID}] \times \text{Set}[\text{SupplyID}] \to \text{List}[\text{Vertex}] \times \text{List}[\text{Boolean}] \times \text{List}[\text{SupplyID}]$
    """)
    return


@app.cell(hide_code=True)
def output_constraints(mo):
    mo.md(r"""
    ## 2.2 Output Constraints
    The algorithm's 3 outputs:
    - $W$, an ordered sequence of vertices (List)
    - $B$, an ordered sequence of booleans (List)
    - an ordered sequence of `SupplyID`s (List)


    Each index $B$ should only be 1 if a supply is at the sector CRUDY-1 is at that part of the walk and should only be greater than 1 if CRUDY-1 has a supply in that slot _and_ the sector CRUDY-1 is in is empty.

    $\forall v \in W, v \in V$, $v_1 = s$, and $v_n \in X$. It should aim to collect the greatest total supply priority possible under the energy constraints: $\displaystyle\sum_{i = 0}^{|W|} \begin{cases}
      p(W[i]) & B[i] \land (W[i] \in S) \\
      0 & \text{otherwise}
    \end{cases}$.

    The ordered sequence of `SupplyID`s should contain exact all $M(v)$ for each $v \in W$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.3 ADT & data model revisions
    No changes due the problem abstraction.

    Due to the dropping supplies feature of the revised problem, abstracting 2-degree vertices as weight between 3+ degree vertices loses data. This is because supplies must be dropped on these 2-degree sectors in optimal solutions.

    This change causes a redesign, as $|V|$ and $|E|$ are now larger.
    """)
    return


@app.cell(hide_code=True)
def _():
    return


@app.cell(hide_code=True)
def algorithm_explorer_header(mo):
    mo.md(r"""
    # 6 Algorithm
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6.1 Algorithm explorer
    """)
    return


@app.cell
def algorithm_resource(facility_drawer, mo):
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _storage = tuple([None] * 5)
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}

    _trials = 100

    def _get_runtime(trials: int = 1) -> float:
        if trials < 1:
            return 0

        """source: https://docs.python.org/3/library/profile.html"""

        import cProfile, pstats
        from pstats import SortKey
        pr = cProfile.Profile()
        pr.enable()
        for i in range(trials):
            """put algoithm here"""
            pass
        pr.disable()
        ps = pstats.Stats(pr).sort_stats(SortKey.CUMULATIVE)
        # return ps.stats[tuple(next(s for s in ps.stats if 'ember_rescue' in s))][3] / trials
        return 0

    def _get_mem() -> float:

        """source: https://docs.python.org/3/library/tracemalloc.html"""

        import tracemalloc

        tracemalloc.start()

        """put algoithm here"""
        pass

        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        top_stats = snapshot.statistics('filename')
        return sum(stat.size for stat in top_stats if "memo1a_algorithm.py" in stat.traceback._frames[0][0])

    _ave_mem = round(sum([_get_mem() for _ in range(_trials)]) / _trials)

    mo.hstack(
        [
            mo.stat(label="Runtime (Python):", value=f"{_get_runtime(_trials) * 1000:.2f}ms"),
            mo.stat(label="Memory (Python):", value=f"{_ave_mem} B")
        ], gap=1, wrap=True
    )
    return


@app.cell(hide_code=True)
def algorithm_resource_note(mo):
    mo.md(r"""
    These value **HIGHLY** depend on the marimo virtual machine, and can vary by orders of magnitude. On my machine, I get Runtime: 2.72ms, Memory: 336 B
    """)
    return


@app.cell
def algorithm_explorer_controls(facility_drawer, mo):
    import memo3_algorithm

    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _storage = tuple([None] * 5)
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}

    @mo.cache
    def ember_rescue_cached():
        return memo3_algorithm.ember_rescue(facility_drawer.get_abstracted_graph(), facility_drawer.entry, {facility_drawer.exit_a, facility_drawer.exit_b}, facility_drawer.supplies, facility_drawer.masses, facility_drawer.values, {}, set(), facility_drawer.budget)

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

    _collected_supplies, _used_budget = facility_drawer.get_collected_supplies_and_budget(_path[:path_len.value])

    mo.vstack(
        [
            mo.hstack(
                [
                    mo.stat(
                        label="Total instructions",
                        value=f"{len(_path) - 1} steps"
                    ),
                    mo.stat(
                        label="Supplies collected",
                        value=f"{len(_collected_supplies)}/{len(facility_drawer.supplies)}"
                    ),
                    mo.stat(
                        label="Supply priority collected",
                        value=f"{sum(facility_drawer.values[s] for s in _collected_supplies)}/{sum(facility_drawer.values[s] for s in facility_drawer.supplies)}"
                    ),
                    mo.stat(
                        label="Budget used",
                        value=f"{_used_budget}/{facility_drawer.budget}"
                    ),
                    mo.stat(
                        label="Ends at exit",
                        value="✅ Yes" if _path[-1] in _exits else "❌ No"
                    ),
                    mo.stat(
                        label="All moves valid",
                        value="✅ Yes" if all(_has_edge(_path[i], _path[i + 1]) for i in range(path_len.value - 1) if not isinstance(_path[i], str) and not isinstance(_path[i + 1], str)) else "❌ No"
                    )
                ], gap=1, wrap=True
            ),
            path_len
        ]
    )
    return


@app.cell
def algorithm_explorer(ember_rescue_cached, facility_drawer, path_len):
    _path = ember_rescue_cached()

    _collected_supplies, _ = facility_drawer.get_collected_supplies_and_budget(_path)

    facility_drawer.draw_multi_wing(plan=ember_rescue_cached()[:path_len.value + 1], abandoned={s for s in facility_drawer.supplies if s not in _collected_supplies})
    return


@app.cell(hide_code=True)
def appendix(mo):
    mo.md(r"""
    # 7 Appendix
    """)
    return


@app.cell
def references(mo):
    mo.md(f"""
    ## 7.1 References\n{open("memo2/references.txt", "r", encoding="utf-8").read()}
    """)
    return


if __name__ == "__main__":
    app.run()
