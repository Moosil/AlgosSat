import marimo
from matplotlib.colors import LinearSegmentedColormap

__generated_with = "0.23.14"
app = marimo.App(width="medium", app_title="Memo1A2", css_file="../custom.css")


@app.cell
def imports():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.colors as mcolors
    import pandas as pd
    import numpy as np
    from itertools import chain
    import re
    import inspect
    import sys

    return (
        chain,
        inspect,
        mcolors,
        mo,
        mpatches,
        np,
        nx,
        pd,
        plt,
        random,
        re,
        sys,
    )


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

    return (get_fig,)


@app.cell(hide_code=True)
def graph_drawer_impl(chain, mcolors, mpatches, nx, plt, random, seed_input):
    class GraphDrawer:
        def __init__(self) -> None:
            self.seed = seed_input.value
            self.WING_COLS, self.WING_ROWS = 10, 10

            self._setup_multi_wing_facility(self.seed)

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
            for i in range(self.n_wings):
                wing: nx.Graph = self.weighted_wings[i].copy() if weighted else self.wings[i].copy()
                for u, d in self.wings[i].degree:
                    w_u = tuple([i] + list(u))
                    if d == 2 and w_u not in self.supplies and w_u not in {self.exit_a, self.exit_b, self.entry} and w_u not in set(chain(*self.junctions)):
                        n0 = list(wing.neighbors(u))[0]
                        n1 = list(wing.neighbors(u))[1]
                        w = wing.get_edge_data(u, n0)["weight"] + wing.get_edge_data(u, n1)["weight"]
                        wing.remove_node(u)
                        wing.add_edge(n0, n1, weight=w)
                wing = nx.relabel_nodes(wing, lambda x: tuple([i] + list(x)))
                wings.add(wing)

            return wings, set(self.junctions)

        def get_flat_graph(self, abs_graph: tuple[set[nx.Graph], set[tuple]]=None) -> nx.Graph:
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

        def _setup_multi_wing_facility(self, seed):
            int_seed = int(seed)
            self.n_wings = 2 + (int_seed % 3)  # 2, 3, or 4 wings from seed
            self.wing_names = ['Alpha', 'Beta', 'Gamma', 'Delta'][:self.n_wings]

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
            self.exit_a = (self.n_wings - 1, self.WING_COLS - 1, self.WING_ROWS - 1)
            self.exit_b = (self.n_wings - 1, self.WING_COLS - 1, 0)

            # Supply placement: spread across wings, prefer dead-end nodes
            srng = random.Random(int_seed * 13 + 42)
            reserved = {self.entry, self.exit_a, self.exit_b}
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
            while len(self.supplies) < 5:
                added = False
                for w in supply_wings:
                    if len(self.supplies) >= 5:
                        break
                    for n in per_wing_cands[w]:
                        if n not in self.supplies:
                            self.supplies.append(n)
                            added = True
                            break
                if not added:
                    break

            self._setup_cost_models()

        def draw_multi_wing(self, weighted=True, highlight_path=None, node_colors=None,
                            supply_collected=None, title="Multi-Wing Facility"):
            COL_BG = '#F5F7FA'
            COL_GRID = '#C8D0DC'
            COL_WALL = '#44546A'
            COL_ENTRY = '#0B6E6B'
            COL_EXIT = '#7A1E2C'
            COL_SUPPLY = '#4AA8A0'
            COL_JUNCTION = '#7A1E2C'
            COL_ROUTE = '#6D28D9'  # bold purple

            _GAP = 1  # grid-unit gap between wings in the visualisation

            # Weight colour scale: 1=lightest, 5=darkest
            WEIGHT_CMAP = LinearSegmentedColormap.from_list(
                'emberweight', ['#B8E0DE', '#F4C97A', '#7A1E2C'], N=256
            )

            def cost_color(weight, min_w=1, max_w=5):
                norm = (weight - min_w) / max(max_w - min_w, 1)
                return WEIGHT_CMAP(norm)

            total_w = self.n_wings * self.WING_COLS + (self.n_wings - 1) * _GAP

            fig_w = max(12, total_w * 0.62)
            fig_h = max(6, self.WING_ROWS * 0.62 + 2.0)
            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.set_facecolor(COL_BG)
            fig.patch.set_facecolor(COL_BG)

            def xoff(w):
                return w * (self.WING_COLS + _GAP)

            # Draw each wing
            for w, wing in enumerate(self.weighted_wings if weighted else self.wings):
                ox = xoff(w)

                # Grid lines
                for c in range(self.WING_COLS + 1):
                    ax.plot([ox + c, ox + c], [0,self.WING_ROWS],
                            color=COL_GRID, lw=0.3, zorder=1)
                for r in range(self.WING_ROWS + 1):
                    ax.plot([ox, ox + self.WING_COLS], [r, r],
                            color=COL_GRID, lw=0.3, zorder=1)

                ax.add_patch(plt.Rectangle((ox, 0), self.WING_COLS, self.WING_ROWS, fill=False,
                                           edgecolor=COL_WALL, lw=2.2, zorder=4))
                model_names = ['Uniform', 'Depth-based', 'Randomised', 'Randomised']
                model_lbl = model_names[w] if w < len(model_names) else 'Randomised'
                ax.text(ox + self.WING_COLS / 2, self.WING_ROWS + 0.55, f"Wing {self.wing_names[w]}",
                        ha='center', va='bottom', fontsize=9, fontweight='bold',
                        color='#0B1F3B', zorder=8)
                ax.text(ox + self.WING_COLS / 2, self.WING_ROWS + 0.15, f"({model_lbl})", ha='center',
                        va='bottom', fontsize=7, color='#44546A', zorder=8)

                # Draw each corridor coloured by weight
                for (c1, r1), (c2, r2), data in wing.edges(data=True):
                    col = cost_color(data.get('weight', 1))
                    ax.plot([ox + c1 + 0.5, ox + c2 + 0.5], [r1 + 0.5, r2 + 0.5],
                            color=col, lw=4.5, solid_capstyle='round', zorder=2)

                # Internal walls (draw where no edge exists)
                for c in range(self.WING_COLS):
                    for r in range(self.WING_ROWS):
                        if c + 1 < self.WING_COLS and not wing.has_edge((c, r), (c + 1, r)):
                            ax.plot([ox + c + 1, ox + c + 1], [r, r + 1],
                                    color=COL_WALL, lw=1.4, zorder=3)
                        if r + 1 <self.WING_ROWS and not wing.has_edge((c, r), (c, r + 1)):
                            ax.plot([ox + c, ox + c + 1], [r + 1, r + 1],
                                    color=COL_WALL, lw=1.4, zorder=3)

                # Node highlights
                if node_colors:
                    for (ww, c, r), color in node_colors.items():
                        if ww == w:
                            ax.add_patch(plt.Rectangle(
                                (ox + c, r), 1, 1,
                                color=color, alpha=0.5, zorder=2))

            # Inter-wing corridors and junction nodes
            for (w1, c1, r1), (w2, c2, r2) in self.junctions:
                x1, y1 = xoff(w1) + c1 + 0.5, r1 + 0.5
                x2, y2 = xoff(w2) + c2 + 0.5, r2 + 0.5
                ax.plot([x1, x2], [y1, y2], color=COL_JUNCTION, lw=2.0,
                        linestyle='--', alpha=0.8, zorder=5)
                ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=6)
                ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=6)

            # Supply markers
            for i, (ws, cs, rs) in enumerate(self.supplies):
                ox = xoff(ws)
                ax.plot(ox + cs + 0.5, rs + 0.5, marker='*', markersize=13,
                        color=COL_SUPPLY, markeredgecolor=COL_ENTRY,
                        markeredgewidth=0.7, zorder=7)
                ax.text(ox + cs + 0.62, rs + 0.58, f'S{i + 1}', fontsize=6,
                        color=COL_WALL, zorder=8)

            # Entry marker
            we, ce, re = self.entry
            ox = xoff(we)
            ax.add_patch(plt.Circle((ox + ce + 0.5, re + 0.5), 0.3,
                                    color=COL_ENTRY, zorder=9))
            ax.text(ox + ce + 0.5, re + 0.5, 'E', ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=10)

            # Exit markers
            for lbl, (wx, cx, rx) in [('A', self.exit_a), ('B', self.exit_b)]:
                ox = xoff(wx)
                ax.add_patch(plt.Circle((ox + cx + 0.5, rx + 0.5), 0.3,
                                        color=COL_EXIT, zorder=9))
                ax.text(ox + cx + 0.5, rx + 0.5, lbl, ha='center', va='center',
                        fontsize=6, color='white', fontweight='bold', zorder=10)

            # Highlight path
            if highlight_path and len(highlight_path) > 1:
                cost_total = 0
                plt.rc('text', usetex=True)
                plt.rc('text.latex', preamble=r'\usepackage{amsmath}')
                for i in range(len(highlight_path) - 1):
                    w1, c1, r1 = highlight_path[i]
                    w2, c2, r2 = highlight_path[i + 1]

                    ax.plot([xoff(w1) + c1 + 0.5, xoff(w2) + c2 + 0.5],
                            [r1 + 0.5, r2 + 0.5], color=COL_ROUTE, lw=5.0,
                            linestyle='-', alpha=1.0, zorder=8, solid_capstyle='round')

                    if w1 != w2:
                        cost_total += 1
                        mid_c = (xoff(w1) + c1 + xoff(w2) + c2) // 2
                        row = r1 + .5 if w1 < w2 else r1 - .5

                        ax.text(mid_c + .53, row + .4, fr"$\underrightarrow{{{str(cost_total)}}}$" if w1 < w2 else fr"$\underleftarrow{{{str(cost_total)}}}$", fontsize=12, color=COL_WALL, zorder=6, horizontalalignment="center")
                    else:
                        cost_total += self.weighted_wings[w1].get_edge_data((c1, r1), (c2, r2))["weight"]

                plt.rc('text', usetex=False)

            # Legend
            legend_items = [
                mpatches.Patch(color=COL_ENTRY, label='Entry'),
                mpatches.Patch(color=COL_EXIT, label='Exit A / B'),
                mpatches.Patch(color=COL_SUPPLY, label='Supply unit'),
                mpatches.Patch(color=COL_JUNCTION, label='Inter-wing junction'),
            ]
            sm = plt.cm.ScalarMappable(cmap=WEIGHT_CMAP,
                                       norm=mcolors.Normalize(vmin=1, vmax=5))
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, fraction=0.018, pad=0.02)
            cbar.set_label('Corridor cost', fontsize=8, color='#0B1F3B')
            cbar.set_ticks([1, 2, 3, 4, 5])
            cbar.ax.tick_params(labelsize=7)

            ax.set_xlim(-0.5, total_w + 0.5)
            ax.set_ylim(-1.0, self.WING_ROWS + 1.4)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title(title, fontsize=11, fontweight='bold',
                         color='#0B1F3B', pad=10)
            plt.tight_layout()
            return fig

    facility_drawer = GraphDrawer()
    return (facility_drawer,)


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
    # Memo 1 Amendment 1
    """)
    return


@app.cell(hide_code=True)
def introduction(mo):
    mo.md(r"""
    # 1 Introduction
    We have been tasked to design a **decision architecture** for a robot. To do this, we will create a abstraction for this problem, and subsequently an algorithm to solve it.

    We will first abstract this problem, discuss and evaluate multiple approaches, before outlining the final chosen approach.

    After which, the algorithm will be implemented in python and run on multiple facilities, we will rigorously prove its correctness and completeness and visualise the running of the algorithm on a representation of the facility.
    """)
    return


@app.cell(hide_code=True)
def algorithm_explorer_header(mo):
    mo.md(r"""
    ### 3.3.4 Algorithm Explorer
    """)
    return


@app.cell
def algorithm_resource(facility_drawer, memo1a_algorithm, mo):
    _abs_graph = facility_drawer.get_abstracted_graph()
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
            memo1a_algorithm.ember_rescue(_abs_graph, facility_drawer.entry, _exits, _supplies, _storage, _supply_map, set())
        pr.disable()
        ps = pstats.Stats(pr).sort_stats(SortKey.CUMULATIVE)
        return ps.stats[tuple(next(s for s in ps.stats if 'ember_rescue' in s))][3] / trials

    def _get_mem() -> float:

        """source: https://docs.python.org/3/library/tracemalloc.html"""

        import tracemalloc

        tracemalloc.start()

        memo1a_algorithm.ember_rescue(
            _abs_graph, facility_drawer.entry, _exits, _supplies, _storage, _supply_map, set()
        )

        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        top_stats = snapshot.statistics('filename')
        return sum(stat.size for stat in top_stats if "memo1a_algorithm.py" in stat.traceback._frames[0][0])

    _ave_mem = round(sum([_get_mem() for _ in range(_trials)]) / _trials)

    mo.hstack([
        mo.stat(label="Runtime (Python):",    value=f"{_get_runtime(_trials) * 1000:.2f}ms"),
        mo.stat(label="Memory (Python):", value=f"{_ave_mem} B")
    ], gap=1, wrap=True)
    return


@app.cell(hide_code=True)
def algorithm_resource_note(mo):
    mo.md(r"""
    These value **HIGHLY** depend on the marimo virtual machine, and can vary by orders of magnitude. On my machine, I get Runtime: 2.72ms, Memory: 336 B
    """)
    return


@app.cell
def algorithm_explorer_controls(facility_drawer, mo, sys):
    sys.path.append('../AlgosSat')
    from memo1a1 import memo1a_algorithm

    _abs_graph = facility_drawer.get_abstracted_graph()
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _storage = tuple([None] * 5)
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}

    @mo.cache
    def ember_rescue_cached():
        return memo1a_algorithm.ember_rescue(_abs_graph, facility_drawer.entry, _exits, _supplies, _storage, _supply_map, set())

    _res = ember_rescue_cached()

    _path = facility_drawer.get_path_from_super_path(_res[0])

    path_len = mo.ui.slider(
        value=0,
        start=0,
        stop=len(_path) - 1,
        step=1,
        label="Step (drag to walk through the facility)",
        full_width=True,
        include_input=True
    )
    return ember_rescue_cached, memo1a_algorithm, path_len


@app.cell
def algorithm_explorer_controls_and_info(
    ember_rescue_cached,
    facility_drawer,
    mo,
    path_len,
):
    _abs_graph = facility_drawer.get_abstracted_graph()
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _storage = tuple([None] * 5)
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}

    _res = ember_rescue_cached()

    def _has_edge(u, v) -> bool:
        if u[0] == v[0]:
            u = u[1:]
            v = v[1:]
            return any(wing.has_edge(u, v) for wing in facility_drawer.wings)
        else:
            return (u, v) in facility_drawer.junctions or (v, u) in facility_drawer.junctions

    _path = facility_drawer.get_path_from_super_path(_res[0])
    _flat_graph = facility_drawer.get_flat_graph(_abs_graph)
    _path_cost = sum(_flat_graph.get_edge_data(_res[0][i], _res[0][i + 1])["weight"] for i in range(len(_res[0]) - 1))
    mo.vstack([
        mo.hstack([
                mo.stat(label="Complete Path length",
                        value=f"{len(_path) - 1} steps"),
                mo.stat(label="Supplies collected",
                        value=f"{len([None for u in _path[:path_len.value] if u in _supplies])}/{len(_supplies)}"),
                mo.stat(label="Ends at exit",
                        value="✅ Yes" if _path[-1] in _exits else "❌ No"),
                mo.stat(label="All moves valid",
                        value="✅ Yes" if all(_has_edge(_path[i], _path[i + 1]) for i in range(path_len.value)) else "❌ No")
            ], gap=1, wrap=True),
        path_len
    ])
    return


@app.cell
def algorithm_explorer(ember_rescue_cached, facility_drawer, mo, path_len):
    @mo.cache
    def _get_path():
        _res = ember_rescue_cached()

        return facility_drawer.get_path_from_super_path(_res[0])

    facility_drawer.draw_multi_wing(highlight_path=_get_path()[:path_len.value + 1])
    return


@app.cell(hide_code=True)
def appendix(mo):
    mo.md(r"""
    # 6 Appendix
    """)
    return


@app.cell
def references(mo):
    mo.md(f"""
    ## 6.1 References\n{open("references.txt", "r", encoding="utf-8").read()}
    """)
    return


@app.cell(hide_code=True)
def other_algorithm_impl_header(mo):
    mo.md(r"""
    # 6.2 Python Implementations
    """)
    return


@app.cell
def get_impl_index_cell(inspect, mo):
    _impl_names = []

    def get_impl_idx(impl_name: str) -> int:
        if impl_name in _impl_names:
            return _impl_names.index(impl_name) + 1
        else:
            _impl_names.append(impl_name)
            return len(_impl_names)

    def get_impl_appendix(name: str, functions):
        if not isinstance(functions, list):
            functions = [functions]
        # Source - https://stackoverflow.com/a/427533
        # Posted by Rafał Dowgird, modified by community. See post 'Timeline' for change history
        # Retrieved 2026-07-09, License - CC BY-SA 3.0
        return mo.vstack([
            mo.md(f"### 6.2.{get_impl_idx(name)} {name}"),
            mo.ui.code_editor('\n\n'.join(inspect.getsource(f) for f in functions), disabled=True)
        ])

    return (get_impl_appendix,)


@app.cell
def other_algorithm_impls(get_impl_appendix, memo1a_algorithm, mo):
    _impl_names = []
    mo.vstack([
        get_impl_appendix("Nearest Neighbour", memo1a_algorithm.nearest_neighbour),
        get_impl_appendix("Lin-Kernighan", [memo1a_algorithm.lin_kernighan, memo1a_algorithm._lin_kernighan]),
        get_impl_appendix("Branch and Bound", memo1a_algorithm.branch_and_bound),
        get_impl_appendix("Simplex (not working)", [memo1a_algorithm.simplex, memo1a_algorithm._simplex, memo1a_algorithm.solve_relaxed_lp])
    ])
    return


if __name__ == "__main__":
    app.run()
