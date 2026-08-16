import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium", app_title="Memo2", css_file="../custom.css")


@app.cell
def imports():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.colors as mcolors
    from itertools import chain
    import sympy as sym
    import numpy as np
    import sys
    import re
    import pandas as pd
    from complexity import Complexity

    return (
        Complexity,
        chain,
        mcolors,
        mo,
        mpatches,
        np,
        nx,
        plt,
        random,
        re,
        sym,
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

        def draw_multi_wing(
            self, weighted=True, highlight_path=None,
            supply_collected=None, title="Multi-Wing Facility"
            ):
            COL_BG = '#F5F7FA'
            COL_GRID = '#C8D0DC'
            COL_WALL = '#44546A'
            COL_ENTRY = '#0B6E6B'
            COL_EXIT = '#7A1E2C'
            COL_SUPPLY = '#4AA8A0'
            COL_JUNCTION = '#7A1E2C'
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

            _GAP = 1  # grid-unit gap between wings in the visualisation

            # Weight colour scale: 1=lightest, 5=darkest
            WEIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
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
                    ax.plot(
                        [ox + c, ox + c], [0, self.WING_ROWS],
                        color=COL_GRID, lw=0.3, zorder=1
                        )
                for r in range(self.WING_ROWS + 1):
                    ax.plot(
                        [ox, ox + self.WING_COLS], [r, r],
                        color=COL_GRID, lw=0.3, zorder=1
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
                    ha='center', va='bottom', fontsize=14, fontweight='bold',
                    color='#0B1F3B', zorder=8
                    )
                ax.text(
                    ox + self.WING_COLS / 2, self.WING_ROWS + 0.15, f"({model_lbl})", ha='center',
                    va='bottom', fontsize=10, color='#44546A', zorder=8
                    )

                # Draw each corridor coloured by weight
                for (c1, r1), (c2, r2), data in wing.edges(data=True):
                    col = cost_color(data.get('weight', 1))
                    ax.plot(
                        [ox + c1 + 0.5, ox + c2 + 0.5], [r1 + 0.5, r2 + 0.5],
                        color=col, lw=4.5, solid_capstyle='round', zorder=2
                        )

                # Internal walls (draw where no edge exists)
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

            # Inter-wing corridors and junction nodes
            for (w1, c1, r1), (w2, c2, r2) in self.junctions:
                x1, y1 = xoff(w1) + c1 + 0.5, r1 + 0.5
                x2, y2 = xoff(w2) + c2 + 0.5, r2 + 0.5
                ax.plot(
                    [x1, x2], [y1, y2], color=COL_JUNCTION, lw=2.0,
                    linestyle='--', alpha=0.8, zorder=5
                    )
                ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=6)
                ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=6)

            # Supply markers
            for i, (ws, cs, rs) in enumerate(self.supplies):
                ox = xoff(ws)
                ax.plot(
                    ox + cs + 0.5, rs + 0.5, marker='*', markersize=13,
                    color=COL_SUPPLY, markeredgecolor=COL_ENTRY,
                    markeredgewidth=0.7, zorder=7
                    )
                ax.text(
                    ox + cs + 0.62, rs + 0.58, f'S{i + 1}', fontsize=9,
                    color=COL_WALL, zorder=8
                    )

            # Entry marker
            we, ce, re = self.entry
            ox = xoff(we)
            ax.add_patch(
                plt.Circle(
                    (ox + ce + 0.5, re + 0.5), 0.3,
                    color=COL_ENTRY, zorder=9
                    )
                )
            ax.text(
                ox + ce + 0.5, re + 0.5, 'E', ha='center', va='center',
                fontsize=9, color='white', fontweight='bold', zorder=10
                )

            # Exit markers
            for lbl, (wx, cx, rx) in [('A', self.exit_a), ('B', self.exit_b)]:
                ox = xoff(wx)
                ax.add_patch(
                    plt.Circle(
                        (ox + cx + 0.5, rx + 0.5), 0.3,
                        color=COL_EXIT, zorder=9
                        )
                    )
                ax.text(
                    ox + cx + 0.5, rx + 0.5, lbl, ha='center', va='center',
                    fontsize=9, color='white', fontweight='bold', zorder=10
                    )

            # Highlight path
            if highlight_path and len(highlight_path) > 1:
                cost_total = 0
                plt.rc('text', usetex=True)
                plt.rc('text.latex', preamble=r'\usepackage{amsmath}')
                supplies_collected = set()
                for i in range(len(highlight_path) - 1):
                    w1, c1, r1 = highlight_path[i]
                    w2, c2, r2 = highlight_path[i + 1]

                    ax.plot(
                        [xoff(w1) + c1 + 0.5, xoff(w2) + c2 + 0.5],
                        [r1 + 0.5, r2 + 0.5], color=COL_ROUTE[len(supplies_collected)], lw=5.0,
                        linestyle='-', alpha=1.0, zorder=8, solid_capstyle='round'
                        )

                    if w1 != w2:
                        cost_total += 1
                        mid_c = (xoff(w1) + c1 + xoff(w2) + c2) // 2
                        row = r1 + .5 if w1 < w2 else r1 - .5

                        ax.text(mid_c + .53, row + .4, fr"$\underrightarrow{{{str(cost_total)}}}$" if w1 < w2 else fr"$\underleftarrow{{{str(cost_total)}}}$", fontsize=12, color=COL_WALL, zorder=6, horizontalalignment="center")
                    else:
                        cost_total += self.weighted_wings[w1].get_edge_data((c1, r1), (c2, r2))["weight"]
                    if (w2, c2, r2) in self.supplies:
                        supplies_collected.add((w2, c2, r2))

                plt.rc('text', usetex=False)

            # Legend
            legend_items = [
                mpatches.Patch(color=COL_ENTRY, label='Entry'),
                mpatches.Patch(color=COL_EXIT, label='Exit A / B'),
                mpatches.Patch(color=COL_SUPPLY, label='Supply unit'),
                mpatches.Patch(color=COL_JUNCTION, label='Inter-wing junction'),
            ]
            sm = plt.cm.ScalarMappable(
                cmap=WEIGHT_CMAP,
                norm=mcolors.Normalize(vmin=1, vmax=5)
                )
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, fraction=0.018, pad=0.02)
            cbar.set_label('Corridor cost', fontsize=14, color='#0B1F3B')
            cbar.set_ticks([1, 2, 3, 4, 5])
            cbar.ax.tick_params(labelsize=10)

            ax.set_xlim(-0.5, total_w + 0.5)
            ax.set_ylim(-1.0, self.WING_ROWS + 1.4)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title(
                title, fontsize=20, fontweight='bold',
                color='#0B1F3B', pad=10
                )
            plt.tight_layout()
            return fig

    facility_drawer = GraphDrawer()
    return (facility_drawer,)


@app.cell(hide_code=True)
def _(mo, re):
    class PseudocodeExplorer:
        def __init__(self):
            self.raw_pseudocode = open("memo1a1/raw_pseudocode.txt", encoding="utf-8").read()
            self.full_pseudocode = self._parse_pseudocode(self.raw_pseudocode)

        def get_fn_fancy(self, name: str, font_size: int = 12, numbered: bool = False):
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
            return self.get_lines_fancy(start_line, start_line + end_line + 1, font_size, numbered)

        def get_lines_fancy(self, start: int, stop: int, font_size: int = 12, numbered: bool = False):
            return mo.md(
                rf"""
        <div style="font-family: monospace; font-size: {font_size}px; white-space: pre-wrap;">{self.get_lines(start, stop, numbered)}</div>
        """
                )

        def get_lines(self, start: int, stop: int, numbered: bool):
            if numbered:
                splits = self.full_pseudocode.split('<br>')[start:stop]
                res = splits[0]
                for i in range(1, len(splits)):
                    res += f"<br><span class='pseudocode-bracket'>[{i}]</span> {splits[i]}"
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

            del i

            res = code.replace('\n', "<br>").replace("    ", "&#9;")
            res = re.sub("PROCEDURE(?= )", "<span class='pseudocode-command'>PROCEDURE</span>", res)
            res = re.sub("FUNCTION(?= )", "<span class='pseudocode-command'>FUNCTION</span>", res)
            res = re.sub("WHILE(?= )", "<span class='pseudocode-command'>WHILE</span>", res)
            res = re.sub("FOR EACH(?= )", "<span class='pseudocode-command'>FOR EACH</span>", res)
            res = re.sub(r"FOR(?= [^ ]+ <-)", "<span class='pseudocode-command'>FOR</span>", res)
            res = re.sub("IF(?= )", "<span class='pseudocode-command'>IF</span>", res)
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

    pseudocode_explorer = PseudocodeExplorer()
    return (pseudocode_explorer,)


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
def _(mo):
    mo.md(r"""
    # 2 Time complexity
    ## 2.1 Different problem approaches
    The design of the algorithm used to solve this problem is what determines its hard-ness, and to demonstrate that, I will juxtapose two algorithms that both solve the problem differently live in **P**, with my algorithm that is certainly **NP-Hard** and the single decision that makes this distinction.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.1.1 ExitOnlyBFS
    The first algorithm ignores supplies and uses bfs to find the nearest exit to leave the facility. An high-level abstraction of the algorithm is outlined below:
    ```
    ExitOnlyBFS(graph: Graph, entry: Vertex, exits: Set) -> Path:
    1  frontier <- Queue containing entry             O(1)
    2  seen     <- Set containing entry               O(1)
    3  While frontier is not empty Do                 loop runs at most V times
    4      current <- frontier.dequeue()              O(1) (V times)
    5      If current in exits Do                     O(1)
    6          Return ReconstructPath(current)        O(V) (once)
    7      Foreach neighbour of current Do            2E times in total
    8          If neighbour not in seen Do            O(1)
    9              seen.add(neighbour)                O(1)
    10             frontier.enqueue(neighbour)        O(1)
    11 Return empty                                   O(1)
    ```
    Since the while loop (3) runs at most $|V|$ times, each vertex may have up to $|V|$ neighbours with the foreach loop (7) running that many times with all other costs in the loop are constant, *ExitOnlyBFS* can be bound in $O(V^2)$ worst-case time complexity. This bound, however, can be tightened to $O(V \cdot E)$ by realising this inner loop runs $\displaystyle\sum_{v \in V} \deg(v) = 2|E|$ times for a undirected graph. This, coupled with the return statement (6) running once (even though it is a for loop that runs $|V|$ times and it has $O(V)$ cost) allows this tight bound, which may be further tightened by the facility's connected property to $O(E)$ given $|V| \leq |E| - 1$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.1.2 GreedyCollect
    ```
    GreedyCollect(graph: Graph, entry: Vertex, exits: Set, supplies: Set) -> Path:
    1  current   ← entry                              O(1)
    2  remaining ← copy of supplies                   O(k)
    3  route     ← list containing entry              O(1)
    4  While remaining is not empty Do                loop runs exactly k times
    5      target ← DijkstraToNearest(current, remaining)   O((V + E) log V) (k times)
    6      route.append(PathTo(target))               O(V)
    7      remaining.remove(target)                   O(1)
    8      current ← target                           O(1)
    9  target ← DijkstraToNearest(current, exits)     O((V + E) log V) (once)
    10 route.append(PathTo(target))                   O(V)
    11 Return route                                   O(1)
    ```
    Since the while loop (4) runs $k$ times, with the inside of the loop costing $O((V + E) \log V)$ on the *Dijkstras* step (5), *GreedyCollect* can be bound in $O(k(V + E) \log V)$ which can be further refined to $O(k E \log V)$ using the same strategy in **2.1.1**.
    """)
    return


@app.cell(hide_code=True)
def _(mo, pseudocode_explorer):
    mo.md(rf"""
    ### 2.1.3 `ember_rescue`
    {pseudocode_explorer.get_fn_fancy("ember_rescue", numbered=True)}

    The step (and decision) that cause my algorithm to not run in polynomial time is the choice of how to approach the decision problem. While my algorithm resembles the second one analysed as it chooses to collect each supply, it deviates in its choice of deciding the order in which the supplies should be collected. By using an exact approach like dynamic programming (335) rather than a greedy approach like the second algorithm, my algorithm has a time complexity with respect to $|S|$, the number of supplies of $O(2^S)$, which exceeds the previous two algorithms which could be bounded in polynomial time.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.2 An analysis of the time complexity
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.2.1 Algorithm and sub-procedure time complexities
    """)
    return


@app.cell(hide_code=True)
def _(Complexity, mo, pseudocode_explorer, re, sym):
    class ProcedureTCExplorer:
        @classmethod
        def get_custom_explanation(cls, name):
            match name:
                case "dfs":
                    return """The while loop (6) runs exactly $|V|$ times, and the for loop runs an amortised $|E|$ times."""
                case "get_path_from_dfs":
                    return """The while loop (7) runs exactly $|V|$ times, where the lengths of the left and right paths increment by 0 or 1 each run of the loop. The for loops (18) (32) runs at most the length of the left and right paths, giving a triangular amount of runs. The inside of the ifs inside the for loops (19) (33) run exactly once, as it returns after that."""
                case "get_supplies_to_collect":
                    return r"""The first for loop (2) runs exactly $|A|$ times and the second for loop (7), which isn't nested, runs exactly $|S|$ times."""
                case "max":
                    return r"""You could ask a year 7 to do this one for you"""
                case "get_path_length":
                    return r"""The for loop (2) runs exactly $n - 1$ times."""
                case "reverse":
                    return r"""The for loop (2) runs exactly $n$ times."""
                case "reconstruct_path":
                    return r"""The while loop (2) can run at most $|V|$ times, as valid first inputs represent a directed tree graph with $|V|$ verticies. The call to reverse is done with $n = |V|$"""
                case "dijkstra":
                    return r"""The for loops (2) (6) run exactly $|V|$ times. Since the while loop removes 1 item from the priority queue each loop, it runs at most $|V|$ times. The inside of the if (12) runs at most $|S|$ times, as the algorithm only can remove each vertex from the priority queue once. This calls reconstruct path $|S|$ times with $V = V$."""
                case "get_path_matrix":
                    return r"""The for loop (2) runs exactly $|S| + 1$ times. This for loop runs dijkstra that many times, however, this call can be amortised for a closer bound, as $m_1 \log n_1 + m_2 \log n_2 + \dots + m_k \log n_k \leq m \log n \vert n = n_1 + n_2 + \dots + n_k, m = m_1 + m_2 + \dots + m_k \mid n, m, k \in \mathbb{Z}^+ \cup \{0\}$"""
                case "get_path_cost_matrix":
                    return r"""The outer for loop (2) runs exactly $|S| + 1$ times, as for valid inputs, it contains an entry for each supply and entrance. The inner for loop (5) runs exactly $|S| + |X|$ times, as for valid inputs, it contains an entry for each supply and exit. Therefore `get_path_length` gets called $(|S| + 1)(|S| + |X|)$ times. """
                case "dp_recursive":
                    return r"""The time complexity of this function is dominated by the cost of 1 function run, and the total number of runs. This total number of runs is $1 + \displaystyle\sum_{k=1}^{|A|} |S| \binom{|S| - 1}{k - 1}$ (similar to OEIS A155865). This is equal to the exponential minus hyperbolic function part. It is known that the if fuel = 0 (9) only will happen $|X|$ times and each other and the first 2 lines will run $\sim |S|!$ times."""
                case "dp":
                    return r"""dp_recursive is only called once (1), and then the for loop (4) runs exactly $|S| + 2$ times."""
                case "get_F_path_from_H_path":
                    return r"""The outer for loop (2) runs $n - 1$ times, and then inner for loop runs"""
                case "get_which_wing":
                    return r"""The for loop (1) runs exactly |V_W| times."""
                case "get_G_path_from_F_path":
                    return r"""The outer for loop (2) runs $n - 1$ times, which calls `get_which_wing` 2 times. The inner for (9) runs at most $|V|$ times, as the maximal path length between two verticies in the same wing is that. This cost is always greater than the if (13), which is mutually exclusive with this line."""
                case "get_F":
                    return r"""The first for loop (2) runs exactly $|S| + |X| + 1$ times. The second for loop (7) runs exactly $|E_W|$ times. The third for loop runs exactly $|V_W|$ times, which has a first inner for loop (18) running an amortised total of $|S| + |X| + 1$ times, and the second double nest loop (22 & 23) which runs `get_path_from_bfs` and `get_path_length` $\frac{1}{2} (|S| + |X| + 1) (|S| + |X|)$ times due to the triangle structure of the for loop."""
                case "get_new_supply_storage":
                    return r"""The first for loop (2) runs exactly $n$ times, with the `push` (4) happening $|S|$ times. The second for loop (9) runs exactly $|A|$ times."""
                case "ember_rescue":
                    return r"""This algorithm calls most of the procedures previously mentioned. It also includes two for loops (4) (12), which run $|A|$ and $|V_W|$ times respectively. The second for loop calls `dfs` which has an amortised time complexity of $O(|V| + |E|)$."""

        @staticmethod
        def replace_var_names_size(in_str: str):
            return in_str.replace("V", "|V|").replace("E", "|E|").replace("W", "|V_W|").replace("J", "|E_W|").replace("S", "|A|").replace("Q", "|X|").replace("P", "|S|")

        @staticmethod
        def replace_var_names(in_str: str):
            return in_str.replace("V", "V").replace("E", "E").replace("W", "V_W").replace("J", "E_W").replace("S", "A").replace("Q", "X").replace("P", "S")

        @staticmethod
        def get_function_n(name: str):
            match name:
                case "get_path_from_dfs":
                    return "size of the input map (prev)"
                case "get_path_length":
                    return "size of the input list (path)"
                case "reverse":
                    return "size of the input list (list)"
                case "reconstruct_path":
                    return "size of the input map (prev)"
                case "get_F_path_from_H_path":
                    return "size of the input list (H_path)"
                case "get_G_path_from_F_path":
                    return "size of the input list (F_path)"
                case "get_new_supply_storage":
                    return "size of the input list (H_path)"

        @classmethod
        def bandaid_fix_t_n(cls, fn_name: str, latex: str):
            match fn_name:
                case "ember_rescue":
                    spacer = r"\\ & \quad \;"
                    return latex[:136] + spacer + latex[136:211] + spacer + latex[211:375] + spacer + latex[375:636] + spacer + latex[636:747 + 26] + spacer + latex[747 + 26:]
                case _:
                    return latex

        @classmethod
        def bandaid_fix_big_o(cls, fn_name: str, latex: str):
            search = re.search(r"\-([^\-]+)\\log", latex)
            log_at_start = False
            if search:
                log_at_start = search.start() == 0
            latex = re.sub(r"\-([^\-]+)\\log", ('' if log_at_start else "+") + r"\1\\log", latex)
            match fn_name:
                case "ember_rescue":
                    return latex[:97] + r"\\ & \quad \;" + latex[97:]
                case _:
                    return latex

        @classmethod
        def get_function(cls, name: str):
            complexity = Complexity.get_from_fn_name(name, True)
            complexity_nonexact = Complexity.get_from_fn_name(name, False)
            var_names = ""
            is_symbolic = not isinstance(complexity, int) and not isinstance(complexity, float)
            if is_symbolic:
                complexity = complexity.simplify()
                complexity_nonexact = complexity_nonexact.simplify(inverse=True)
                var_names = [cls.replace_var_names(i.name) for i in complexity.free_symbols]

            var_explanation_dict = {
                "V": "set of vertices",
                "E": "set of edges",
                "V_W": "set of input wing graphs",
                "E_W": "set of inter-wing junctions",
                "A": "array representing CRUDY-1's supply storage",
                "X": "set of exit vertices",
                "S": "set of supply vertices",
                "n": cls.get_function_n(name)
            }
            var_explanation = ""
            if len(var_names) > 0:
                n = var_names[0]
                var_explanation = "where " + f"${n}$ is the {var_explanation_dict[n]}"
                if len(var_names) > 1:
                    for n in var_names[:-1]:
                        var_explanation += f", ${n}$ is the {var_explanation_dict[n]}"

                    n = var_names[-1]
                    var_explanation += f" and ${n}$ is the {var_explanation_dict[n]}"

                var_explanation += ':'

            pseudocode = pseudocode_explorer.get_fn_fancy(name, numbered=True)
            o_args = []
            if is_symbolic:
                o_args = [(x, sym.oo) for x in complexity_nonexact.free_symbols]

            t_n_latex = cls.replace_var_names_size(sym.latex(complexity))
            t_n_latex = cls.bandaid_fix_t_n(name, t_n_latex)

            big_o_latex = cls.replace_var_names_size(sym.latex(sym.O(complexity_nonexact, *o_args).expr.simplify(inverse=True)))
            big_o_latex = cls.bandaid_fix_big_o(name, big_o_latex)
            if name == "ember_rescue":
                big_o_latex = r"O \Bigl( " + big_o_latex + r" \Bigr)"
            else:
                big_o_latex = r"O \left( " + big_o_latex + r" \right)"

            return mo.md(
                fr"""
                ### {"Procedure" if name != "ember" else "Algorithm"} `{name}`
                {pseudocode}

                $$\begin{{align*}}
                T({','.join(var_names)}) &= {t_n_latex}\\
                &= {big_o_latex}
                \end{{align*}}$$

                {var_explanation}

                {cls.get_custom_explanation(name)}
            """
                )

    proc_tc_explorer = ProcedureTCExplorer()
    mo.ui.tabs(
        {
            "dfs": proc_tc_explorer.get_function("dfs"),
            "get_path_from_dfs": proc_tc_explorer.get_function("get_path_from_dfs"),
            "get_supplies_to_collect": proc_tc_explorer.get_function("get_supplies_to_collect"),
            "max": proc_tc_explorer.get_function("max"),
            "get_path_length": proc_tc_explorer.get_function("get_path_length"),
            "reverse": proc_tc_explorer.get_function("reverse"),
            "reconstruct_path": proc_tc_explorer.get_function("reconstruct_path"),
            "dijkstra": proc_tc_explorer.get_function("dijkstra"),
            "get_path_matrix": proc_tc_explorer.get_function("get_path_matrix"),
            "get_path_cost_matrix": proc_tc_explorer.get_function("get_path_cost_matrix"),
            "dp_recursive": proc_tc_explorer.get_function("dp_recursive"),
            "dp": proc_tc_explorer.get_function("dp"),
            "get_F_path_from_H_path": proc_tc_explorer.get_function("get_F_path_from_H_path"),
            "get_which_wing": proc_tc_explorer.get_function("get_which_wing"),
            "get_G_path_from_F_path": proc_tc_explorer.get_function("get_G_path_from_F_path"),
            "get_F": proc_tc_explorer.get_function("get_F"),
            "get_new_supply_storage": proc_tc_explorer.get_function("get_new_supply_storage"),
            "ember_rescue": proc_tc_explorer.get_function("ember_rescue"),
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.2.2 Amendment time complexity changes
    In the first amendment, it was revealed the facility may be multi-wing. This introduced two new variables, $V_E$ and $V_W$, and required a rethinking of the abstraction of the problem.

    Compared with an more optimal algorithm that would've worked before this amendment, this variable $V_W$, roughly required a linear cost increase. This was not true for the variable $E_W$, which broke the tree structure assumption of the facility, as now only each wing was observed to be a tree.

    This required Dijkstra's algorithm to be used which increase the order from $O(|V| + |E|)$ to $O(|E| + |V| \log |V|)$. As discussed previously, this order change could've been mitigated by using Thorup99, but due to its high constant costs and difficulty of implementation, it was avoided.

    In the second amendment, it was discovered that sectors of the facility do not have uniform traversal costs. This did not increase the complexity of the problem, as the abstraction model already has weighted edges, which 'absorbed' this traversal cost into it.
    """)
    return


@app.cell(hide_code=True)
def _(Complexity, facility_drawer, mo, np):
    _abs_graph = facility_drawer.get_abstracted_graph()
    _exits = {facility_drawer.exit_a, facility_drawer.exit_b}
    _supplies = set(facility_drawer.supplies)
    _storage = tuple([None] * 5)
    _supply_map = {i: hash(i) for i in facility_drawer.supplies}

    _vw = len(_abs_graph[0])
    _a = len(_storage)
    _v = sum([len(w) for w in _abs_graph[0]])
    _ve = len(_abs_graph[1])
    _x = len(_exits)
    _e = sum([len(w.edges) for w in _abs_graph[0]])
    _s = len(_supplies)

    mo.md(
        fr"""
    ### 2.2.3 Current operation counts
    On the my current facility seed, using the upper-bound time complexity found in 2.2.1, we get
    $T({_vw}, {_a}, {_v}, {_ve}, {_x}, {_e}, {_s}) = {np.format_float_scientific(np.ceil(Complexity.ember_rescue(_v, _e, _vw, _ve, _s, _e, _a, True).evalf()), precision=3)}$
    """
        )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.2.4 Operational cost explorer
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    _pretty_name = {
        "v": "Vertex count",
        "w": "Wing count",
        "p": "Supply count",
        "q": "Exit count",
        "e": "Edge count",
        "j": "Inter-wing junction count",
        "s": "CRUDY-1 supply storage size",
        "op_count": "Operation count"
    }

    _range_max = {
        "v": 150,
        "w": 150,
        "p": 50,
        "q": 50,
        "e": 150,
        "j": 150,
        "s": 50,
    }

    _initial_value = {
        "v": 70,
        "w": 150,
        "p": 11,
        "q": 4,
        "e": 150,
        "j": 150,
        "s": 50,
    }

    op_cost_dict = mo.ui.dictionary(
        {_pretty_name[name]: mo.ui.slider(1, _range_max[name], 1, label=_pretty_name[name], show_value=True, value=_initial_value[name]) for name in _pretty_name if name != "op_count"},    label="Variables"
    )

    op_cost_dict
    return (op_cost_dict,)


@app.cell(hide_code=True)
def _(Complexity, mo, np, op_cost_dict, sym):
    _v, _e, _w, _j, _p, _q, _s = sym.symbols("V,E,W,J,P,Q,S", positive=True, integer=True)

    @mo.cache
    def _get_formula():
        return sym.lambdify((_v, _e, _w, _j, _p, _q, _s), Complexity.ember_rescue(_v, _e, _w, _j, _p, _q, _s, True), "numpy")

    _pretty_name = {
        "v": "Vertex count",
        "w": "Wing count",
        "p": "Supply count",
        "q": "Exit count",
        "e": "Edge count",
        "j": "Inter-wing junction count",
        "s": "CRUDY-1 supply storage size",
        "op_count": "Operation count"
    }

    mo.md(rf"""
    $$T({op_cost_dict[_pretty_name["v"]].value}, {op_cost_dict[_pretty_name["e"]].value}, {op_cost_dict[_pretty_name["w"]].value}, {op_cost_dict[_pretty_name["j"]].value}, {op_cost_dict[_pretty_name["p"]].value}, {op_cost_dict[_pretty_name["q"]].value}, {op_cost_dict[_pretty_name["s"]].value}) = {np.format_float_scientific(np.ceil(_get_formula()(op_cost_dict[_pretty_name["v"]].value, op_cost_dict[_pretty_name["e"]].value, op_cost_dict[_pretty_name["w"]].value, op_cost_dict[_pretty_name["j"]].value, op_cost_dict[_pretty_name["p"]].value, op_cost_dict[_pretty_name["q"]].value, op_cost_dict[_pretty_name["s"]].value)), precision=3)}$$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.3 Extension to Full-scale Missions
    While the algorithm may be practical for small, 3 wing facilities with 5 total supplies, actual facilities may not be so ideal. For the algorithm to be considered for real, large-scale disaster sites, it must run well on these. In this section I will outline the boundaries of what the algorithm can and can't do, modeling possible large facilies using predefined or variable rulesets.

    In this extension, I will analyse the bounds of a largest facility the algorithm could handle by analysing the growth rate of the algorithm's worst case time complexity in relation to each variable individually, keeping the others constant.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.3.1 Partial growth rates
    """)
    return


@app.cell(hide_code=True)
def _(Complexity, mo, np, plt, sym):
    _MAX_VALUE = 150

    _pretty_name = {
        "v": "Vertex count",
        "w": "Wing count",
        "p": "Supply count",
        "q": "Exit count",
        "e": "Edge count",
        "j": "Inter-wing junction count",
        "s": "CRUDY-1 supply storage size",
        "op_count": "Operation count"
    }

    _fix_value = {
        "v": 1,
        "e": 1,
        "w": 1,
        "p": 1,
        "q": 1,
        "e": 1,
        "j": 1,
        "s": 1
    }

    _n, _m = sym.symbols("n,m", positive=True, integer=True)

    def get_v(name, var_name):
        if name != var_name:
            return _fix_value[name]
        else:
            return _n

    functions = {name: sym.lambdify((_n,), Complexity.ember_rescue(get_v("v", name), get_v("e", name), get_v("w", name), get_v("j", name), get_v("p", name), get_v("q", name), get_v("s", name), True), "numpy") for name in _pretty_name if name != "op_count"}

    # add it as area as p and s are dependent (in terms of range)
    function_p_s = sym.lambdify((_n, _m), Complexity.ember_rescue(get_v("v", "p"), get_v("e", "p"), get_v("w", "p"), get_v("j", "p"), _n, get_v("q", "p"), _m, True), "numpy")

    def _plot(name):
        _fig, _ax = plt.subplots(1, 1, figsize=(12, 6))
        if name == "s":
            max_value = 0
            colors = plt.cm.viridis(np.linspace(0, 1, _MAX_VALUE))
            for m in range(0, _MAX_VALUE, 5):
                max_value = function_p_s(m, _MAX_VALUE)
                _ax.plot(list(range(1, _MAX_VALUE)), [function_p_s(m, i) for i in range(1, _MAX_VALUE)], label=_pretty_name[name], color=colors[m])

            sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(vmin=0, vmax=_MAX_VALUE))
            axcb = _fig.colorbar(sm, ax=_ax, ticks=list(range(0, _MAX_VALUE + 1, 25)))
            axcb.set_label(f"Fixed {_pretty_name["p"]}", fontsize=14)
            _ax.set_yscale("log", base=10)
            _ax.set_ylim(0, 10 ** (np.log10(max_value) * 1.1))
        elif name == "p":
            max_value = 0
            colors = plt.cm.viridis(np.linspace(0, 1, _MAX_VALUE))
            for m in range(0, _MAX_VALUE, 5):
                max_value = function_p_s(_MAX_VALUE - 1, m)
                _ax.plot(list(range(m + 1, _MAX_VALUE)), [function_p_s(i, m) for i in range(m + 1, _MAX_VALUE)], label=_pretty_name[name], color=colors[m])

            sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(vmin=0, vmax=_MAX_VALUE))
            axcb = _fig.colorbar(sm, ax=_ax, ticks=list(range(0, _MAX_VALUE + 1, 25)))
            axcb.set_label(f"Fixed {_pretty_name["s"]}", fontsize=14)
            _ax.set_yscale("log", base=10)
            _ax.set_ylim(0, 10 ** (np.log10(max_value) * 1.1))
        else:
            _ax.plot(list(range(1, _MAX_VALUE)), [functions[name](i) for i in range(1, _MAX_VALUE)], label=_pretty_name[name], color="#74c7ec")
            max_value = functions[name](_MAX_VALUE)
            _ax.set_ylim(1, max_value * 1.1)

        _ax.set_xlabel(_pretty_name[name], fontsize=14)
        _ax.set_title(f"{_pretty_name[name]} vs Operation count", fontsize=16)
        _ax.set_xlim(0, _MAX_VALUE)
        _ax.tick_params(axis='x', which='major', labelsize=14)
        _ax.set_ylabel("Operation count", fontsize=14)
        plt.xticks(list(range(0, _MAX_VALUE + 1, 25)))

        _fig.tight_layout()
        return _fig

    partial_growth_tabs = mo.ui.tabs({_pretty_name[name]: _plot(name) for name in _pretty_name if name != "op_count"})
    partial_growth_tabs
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Partial Growth")}</span>

    Figure {get_fig("Partial Growth")} shows the growth of the time complexity in relation to each variable in the problem. In each figure that is not normalised, every other variable is fixed to 1, as otherwise constant costs make the graphs useless. 

    The number of wings, edges and interwing junctions have linear growth, while the number of vertices and exits display polynomial growth.

    Since the growth rate of supplies and supply storage are related, different values were fixed to show the relationship between the growth rates.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.3.2 Practical maximal input
    To find a maximum input size, we must first define a processing power for the CRUDY-1. With cursory search into drone **printed circuit boards** (PCBs), I discovered that drone's main compute power is from their **microcontroller unit** (MCU). The dominant producer of MCUs are **STMicroelectronic** (STM) with their _STM32_ series, with other brands not common in commerical grade drones.

    STM have 4 types of MCUs: 'Mainstream', 'Ultra-low-power', 'High-performance' and 'Wireless'. Most sources online I could find report that drones use MCUs from the 'High-performance' rnage, but since CRUDY-1 is traversing through a large facility, I decided to pick from the high end of their 'Ultra-low-power' range. This also has the benefit of being transferable to the 'High-performance' units, as if it can run on a low-end performance unit, it will run on a high-end one.

    The range of these chosen units is from the _STM32U5_ range, with up to 160 Mhz, to the _STM32L0_ range, with up to 32 Mhz. This is often an idealised, optimal value though, and real processors often can do more than 1 instruction per CPU cycle. DMIPS is an old benchmark used to 'solve' this problem, and the two MCU ranges selected have 240 DMIPS and 30 DMIPS respectively. While this is a better benchmark, modern benchmarks like CoreMark give more accurate comparisons, with scores of 651 and 455 respectively. CoreMark doesn't translate well to a 'performance number' and mainly serves as a comparison between two different CPUs, so I will be using the DMIPS values cautiously. Specifically, I will be using a value of 130 million basic operations/second, slightly lower than the median DMIPS value of the 'Ultra-low-power' STM32 MCUs.

    I decided that 1 second to find a route would be suitable, which gives an upper bound of 70 total vertices, 150 wings, 150 total intra-wing edges, 150 inter-wing edges, 4 exits, 11 supplies and 11 a model of CRUDY-1 will 11 supply storage, noting reducing this has little effect on the number of operations. This gives a total of 126.8 million operations which is <1 second on this theoretical MCU. This upper bound does include the current 3-wing facilities with a mean 68 vertices, 65 edges, 3 inter-wing junctions, 5 supplies and 2 exit, and with the current 5 supply-storage CRUDY-1 model.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.3.3 Relook at suitability
    With this new performance data, we can determine the current algorithm is suitable for current facility, and slightly ones with double the supplies or vertices. If facilities with double supplies and vertices, or a larger number of these two variables exist the algorithm will immediately become unfeasable due to polynomial and exponential growth causing small changes to greatly increase run costs.

    It would be wise to consider replacing the quadratic time sub-procedures in the algorithm with linear or quasi-linear time ones to prepare for this in advance, or to test some heuristic methods, in the eventual case larger disaster sites are found and we need to quickly find a more efficient algorithm to extract critical supplies.
    """)
    return


@app.cell(hide_code=True)
def algorithm_explorer_header(mo):
    mo.md(r"""
    # 3 Algorithm
    """)
    return


@app.cell(hide_code=True)
def _(mo, pseudocode_explorer):
    mo.md(rf"""
    ## 3.1 Bug-fixes and updates
    ### 3.1.1 `get_path_length` was updated to handle 0-length paths
    {pseudocode_explorer.get_fn_fancy("get_path_length", numbered=True)}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.2 Algorithm explorer
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
    mo.vstack(
        [
            mo.hstack(
                [
                    mo.stat(
                        label="Complete Path length",
                        value=f"{len(_path) - 1} steps"
                        ),
                    mo.stat(
                        label="Supplies collected",
                        value=f"{len([None for u in _path[:path_len.value] if u in _supplies])}/{len(_supplies)}"
                        ),
                    mo.stat(
                        label="Ends at exit",
                        value="✅ Yes" if _path[-1] in _exits else "❌ No"
                        ),
                    mo.stat(
                        label="All moves valid",
                        value="✅ Yes" if all(_has_edge(_path[i], _path[i + 1]) for i in range(path_len.value)) else "❌ No"
                        )
                ], gap=1, wrap=True
            ),
            path_len
        ]
    )
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


if __name__ == "__main__":
    app.run()
