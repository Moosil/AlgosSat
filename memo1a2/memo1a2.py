import marimo

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

            def _alpha_cost(c1, r1, c2, r2):
                return 1

            def _beta_cost(c1, r1, c2, r2):
                return 1 + max(c1, c2) // 3

            def _seeded_rng(wing_idx):
                return random.Random(int_seed * 41 + wing_idx * 3331)

            cost_models = []
            for w, wg in enumerate(self.weighted_wings):
                if w == 0:
                    cost_fn = _alpha_cost
                    model_name = "Uniform (cost = 1)"
                    rng = None
                elif w == 1:
                    cost_fn = _beta_cost
                    model_name = "Depth-based (cost = 1 + floor(col / 3))"
                    rng = None
                else:
                    rng = _seeded_rng(w)
                    edge_list = list(wg.edges())
                    edge_costs = {tuple(sorted(e)): rng.randint(1, 5) for e in edge_list}
                    cost_fn = None
                    model_name = f"Seed-randomised (cost ∈ {{1..5}})"

                cost_models.append(model_name)

                for (c1, r1), (c2, r2) in wg.edges():
                    if cost_fn is not None:
                        w_cost = cost_fn(c1, r1, c2, r2)
                    else:
                        key = tuple(sorted([(c1, r1), (c2, r2)]))
                        w_cost = edge_costs[key]
                    wg[(c1, r1)][(c2, r2)]['weight'] = w_cost

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
                de = [(w, c, r) for (c, r) in wg.nodes()
                      if wg.degree((c, r)) == 1 and (w, c, r) not in reserved]
                srng.shuffle(de)
                per_wing_cands.append(de)

            # Round-robin: up to 2 supplies per wing, 5 total
            self.supplies = []
            for _ in range(2):
                for wl in per_wing_cands:
                    if len(self.supplies) >= 5:
                        break
                    for n in wl:
                        if n not in self.supplies:
                            self.supplies.append(n)
                            break
                if len(self.supplies) >= 5:
                    break

            self.supplies = self.supplies[:5]
            self._setup_cost_models()

        def draw_multi_wing(self, weighted=True, highlight_path=None, node_colors=None,
                            supply_collected=None, title="Multi-Wing Facility"):
            COL_BG = '#F5F7FA'
            COL_GRID = '#C8D0DC'
            COL_WALL = '#44546A'
            COL_ENTRY = '#0B6E6B'
            COL_EXIT = '#7A1E2C'
            COL_SUPPLY = '#4AA8A0'
            COL_PATH = '#0B6E6B'
            COL_VISITED = '#B8D8D7'
            COL_FRONTIER = '#F4C97A'
            COL_CURRENT = '#E8603C'
            COL_JUNCTION = '#7A1E2C'

            _GAP = 1  # grid-unit gap between wings in the visualisation

            # Weight colour scale: 1=lightest, 5=darkest
            WEIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
                'wcost', ['#B8E0DE', '#F4C97A', '#E88A4A', '#C84A30', '#7A1E2C']
            )

            def _weight_colour(w, wmin=1, wmax=5):
                t = (w - wmin) / max(wmax - wmin, 1)
                return WEIGHT_CMAP(t)

            total_w = self.n_wings * self.WING_COLS + (self.n_wings - 1) * _GAP

            fig_w = max(10., total_w * 0.35)
            fig_h = max(5., self.WING_ROWS * 0.35 + 1.2)
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
                            color=COL_GRID, lw=0.4, zorder=1)
                for r in range(self.WING_ROWS + 1):
                    ax.plot([ox, ox + self.WING_COLS], [r, r],
                            color=COL_GRID, lw=0.4, zorder=1)

                # Wing border
                ax.add_patch(plt.Rectangle(
                    (ox, 0), self.WING_COLS,self.WING_ROWS,
                    fill=False, edgecolor=COL_WALL, lw=2.2, zorder=3))

                # Wing label
                ax.text(ox + self.WING_COLS / 2,self.WING_ROWS + 0.38,
                        f"Wing {self.wing_names[w]}",
                        ha='center', va='bottom', fontsize=9,
                        fontweight='bold', color='#0B1F3B', zorder=8)

                # Draw each corridor coloured by weight
                for (c1, r1), (c2, r2) in wing.edges():
                    cost = wing[(c1, r1)][(c2, r2)].get('weight', 1)
                    col = _weight_colour(cost)
                    x1, y1 = ox + c1 + 0.5, r1 + 0.5
                    x2, y2 = ox + c2 + 0.5, r2 + 0.5
                    ax.plot(
                        [x1, x2], [y1, y2], color=col, lw=3.5,
                        solid_capstyle='round', zorder=1, alpha=0.85
                    )

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
                ax.plot([x1, x2], [y1, y2],
                        color=COL_JUNCTION, lw=1.8,
                        linestyle='--', alpha=0.7, zorder=4)
                ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=5)
                ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=5)

            # Supply markers
            for i, (ws, cs, rs) in enumerate(self.supplies):
                ox = xoff(ws)
                already = supply_collected and (ws, cs, rs) in supply_collected
                col = '#AAAAAA' if already else COL_SUPPLY
                mkr = 'x' if already else '*'
                ax.plot(ox + cs + 0.5, rs + 0.5,
                        marker=mkr, markersize=14, color=col,
                        markeredgecolor=COL_ENTRY if not already else '#999',
                        markeredgewidth=0.8, zorder=5)
                ax.text(ox + cs + 0.62, rs + 0.58, f'S{i + 1}',
                        fontsize=6, color=COL_WALL, zorder=6)

            # Entry marker
            we, ce, re = self.entry
            ox = xoff(we)
            ax.add_patch(plt.Circle(
                (ox + ce + 0.5, re + 0.5), 0.28,
                color=COL_ENTRY, zorder=6))
            ax.text(ox + ce + 0.5, re + 0.5, 'E',
                    ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=7)

            # Exit markers
            for lbl, (wx, cx, rx) in [('A', self.exit_a), ('B', self.exit_b)]:
                ox = xoff(wx)
                ax.add_patch(plt.Circle(
                    (ox + cx + 0.5, rx + 0.5), 0.28,
                    color=COL_EXIT, zorder=6))
                ax.text(ox + cx + 0.5, rx + 0.5, lbl,
                        ha='center', va='center',
                        fontsize=6, color='white', fontweight='bold', zorder=7)

            # Highlight path
            if highlight_path and len(highlight_path) > 1:
                cost_total = 0
                plt.rc('text', usetex=True)
                plt.rc('text.latex', preamble=r'\usepackage{amsmath}')
                for i in range(len(highlight_path) - 1):
                    w1, c1, r1 = highlight_path[i]
                    w2, c2, r2 = highlight_path[i + 1]
                    ax.plot(
                        [xoff(w1) + c1 + 0.5, xoff(w2) + c2 + 0.5],
                        [r1 + 0.5, r2 + 0.5],
                        color=COL_PATH, lw=1.8, linestyle='--',
                        alpha=0.75, zorder=4)

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
            if node_colors:
                legend_items += [
                    mpatches.Patch(color=COL_VISITED, alpha=0.5, label='Visited'),
                    mpatches.Patch(color=COL_FRONTIER, alpha=0.5, label='Frontier'),
                    mpatches.Patch(color=COL_CURRENT, alpha=0.7, label='Current'),
                ]
            ax.legend(handles=legend_items, loc='upper left',
                      fontsize=7, framealpha=0.9)

            ax.set_xlim(-0.5, total_w + 0.5)
            ax.set_ylim(-0.9,self.WING_ROWS + 1.1)
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
def limitations_of_previous_model(mo):
    mo.md(r"""
    ## 1.1 Limitations of Previous Model
    - The previous model assumed the facility's sectors had equal traversal costs.
    """)
    return


@app.cell(hide_code=True)
def amendment_revisions(mo):
    mo.md(r"""
    ## 1.2 Amendment Revisions
    The previous abstraction assumed the facility's sectors had equal traversal costs. This required that edges in each wing of $G$ were given cost based on traversal cost instead of number of sectors.

    Otherwise, the algorithm still works on this facility, as the weight changes don't change the tree structure or introduce more supplies.
    """)
    return


@app.cell(hide_code=True)
def abstraction(mo):
    mo.md(r"""
    # 2 Abstraction
    Let $G = (V_w, E_w, w)$ be a meta-graph, with $V_w=\{W_1, W_2, \dots, W_k\}$ being a set of undirected weighted graphs, $E_w \subseteq \{\{u, v\} \vert u \in V_n, v \in V_m, n \neq m\}$ being a set of edges between adjacent wings, $W_n, W_m$ of the facility, with $k$ being the number of wings in the facility, and $\forall n \leq k, W_n = (V_n, E_n)$.

    $V = V_1 \cup V_2 \cup \dots \cup V_k$ and $\forall n, m \leq k, V_n \cap V_m = \varnothing \iff n \neq m$ and $V_n = V_m \iff n = m$, with $V$ representing the salient sectors of the facility $E = E_1 \cup E_2 \cup \dots \cup E_k$ and $\forall n, m \leq k, E_n \cap E_m = \varnothing \iff n \neq m$ and $E_n = E_m \iff n = m$, with $E$ representing the paths between those adjacent salient sectors, and positive integer edge weight function $w: E \cup E_w \to \mathbb{N}$ representing the total cost of traversing the span of sectors  which are adjacent to just two other sectors and between two salient sectors. If $(u, v) \notin E$, define $w(u, v) = \infty$.

    We will designate source vertex $s \in V$, the set of sink vertices $X \subseteq V$, and the set of prize vertices $S \subseteq V$, each representing the entry, exit, and supply unit-containing sectors respectively.

    We will have $A$ be an array of size 5 representing CRUDY-1's supply unit storage, which contains `SupplyID`s or NULL, function $M: S \to \text{SupplyID}$ mapping each supply vertex to its `SupplyID`, and set $F$ be the set of found `SupplyID`s. When a supply is collected, it will be added to $A$, and $A_\text{new}$ will be returned.

    We will be designing an algorithm to traverse meta-graph $G$, from $s$ to an $x$, returning an ordered sequence of vertices in list $W$, and CRUDY-1's updated supply unit storage.
    """)
    return


@app.cell(hide_code=True)
def signature_specification(mo):
    mo.md(r"""
    ## 2.1 Signature specification:
    $\text{ember\_rescue}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \times \text{Array}[\text{SupplyID}, 5] \times \text{Map}[\text{Vertex}, \text{SupplyID}] \times \text{Set}[\text{SupplyID}] \to \text{List}[\text{Vertex}] \times \text{Array}[\text{SupplyID}, 5]$
    """)
    return


@app.cell(hide_code=True)
def output_constraints(mo):
    mo.md(r"""
    ## 2.2 Output Constraints
    The algorithm should output an ordered sequence of vertices $(v_1, v_2, \dots, v_n)$, with $\forall m < n, v_m \in V \cup V_w$, $v_1 = s$, and $v_n \in X$. It should aim to collect as many supply vertices as possible, while reducing the total cost of this walk, $\displaystyle\sum_{i=0}^{n - 1} w(v_i, v_{i + 1})$.

    The algorithm should return CRUDY-1's new supply storage, updating it with each supply collected: $\forall i \leq |A|, A_\text{new}[i] \neq A[i] \implies A[i] = \text{NULL}$, $A[i] \neq \text{NULL} \iff A_\text{new} = A[i]$ and $\forall v \text{ in } W | v \in S, A_\text{new} \text{ contains } v$.
    """)
    return


@app.cell(hide_code=True)
def assumptions(mo):
    mo.md(r"""
    ## 2.3 Assumptions
    Assumptions about the problem allow use of more efficient or informed algorithms to be used. Outlined below are properties observed from all of a subset of facility maps examined:
    - Each wing is a tree: there is exactly 1 path CRUDY-1 can take through a wing from one sector to another, and thus this path **must** be a shortest path. This also means $\forall v \in V$, $\deg(v) \geq 1$
    - Each sector is adjacent to at most 4 other sectors: This means $\forall v \in V$, $\deg(v) \leq 4$
    - Sectors are never adjacent to themselves
    - Each junction vertex connects to a junction vertex in a different wing.

    Additionally, we make some assumptions that guide why our certain algorithm is chosen:
    - $|V_w|$, $|E_w|$, $|S|$ and $|X|$ are small
    - $|V_n|$, $|E_n|$ could be large for $n \leq k$

    Thus, our algorithm must scale well with $|V_n|$ and $|E_n|$, and there is less restriction of scaling with $|V_w|$, $|E_w|$, $|S|$ and $|X|$.
    """)
    return


@app.cell(hide_code=True)
def salient_features(mo):
    mo.md(r"""
    ## 2.4 Salient Features
    Decisions made for how much abstraction is done on certain properties of the problem are guided by maintaining correctness, completeness, and allowing for an appropriate run-time given the size of each variable in the current problem. In particular, finding an exact solution requires searching through a portion of the solution space, and thus we have an at most exponential growth in $O(b^d)$. Reducing $b$ and $d$ allow for further depth and will allow the algorithm to run faster, allow for exact algorithms/better heuristic upper-bounds, and allow for this algorithm to be considered on larger facilities.

    By representing the facility as a hierarchical graph, we can use strategies to reduce the depth of the combinatorial explosion of algorithms that can be used to assist with the objective. Instead of $O(b^d)$ exploding with $d = |E|$, we can instead have it increase with $d = |V_w|$ instead. We have each wing be a vertex on $G$, and each junction and inter-wing corridor.

    We choose to abstract individual sectors of the facility, opting to instead represent a subset of salient sectors to be on any wing graph $W_n$, abstracting the sectors on the paths between these salient sectors as edge weight through the function $w$.

    These salient sectors are sectors adjacent to 1, 3 or 4 other sectors, and sectors containing supply units, entrances, junctions or exits. Without any one of these, we do not fully capture each wing of the facility in our abstraction.

    CRUDY-1's limited supply storage is represented by $A$, with $F$ being already collected supplies <span>&ndash;</span> CRUDY-1 does not need to collect these supplies <span>&ndash;</span> and $M$ finding the `SupplyID` of a particular supply vertex.
    """)
    return


@app.cell(hide_code=True)
def hierarchical_vs_flat_graph(mo):
    mo.md(r"""
    ## 2.5 Hierarchical vs Flat graph
    When adapting from a single-wing facility to a multi-wing one, there are two obvious ways to represent the multiple wings.

    Recall in Memo 1, the facility's singular wing was represented as a graph, with each vertex representing a salient sector and each edge a connecting walk between those salient sectors.

    The **Hierarchical graph** representation uses a meta-graph, a graph where each vertex is another graph, to represent the wings of the facility. Each wing is an vertex in the meta-graph and the connecting corridors between each wing will be the edges. These vertex-graphs will be represented the same way as in Memo 1.

    The **Flat graph** representation uses a graph to representing the facility. The facility will be represented the same way as in Memo 1, except edges can now also represent inter-wing corridors between junction sectors.

    First we can notice that, with an algorithmic process, it is possible to flatten the hierarchical graph into the flat graph by adding each vertex and edge in each vertex of the meta-graph to a empty graph and then adding each edge from the meta-graph as an edge in this graph. Therefore we can conclude that the hierarchical graph has more information than the flat graph, and the flat graph _loses_ information.

    If we were to adopt the flat representation and continue to use the previous algorithm, we would notice a performance penalty, as our dijkstra's algorithm cost scales with the number of vertices in the full flat representation. With 4 wings, this is barely noticeable, but if new information was to reveal a larger facility, the cost would quickly become enough to make the algorithm not feasible.

    This hierarchical graph represents the physical properties of the facility more closely, and this additional information can be used to inform a more efficient algorithm. There is only a small, linear-time cost associated with converting the hierarchical graph to the flat graph representation, and therefore it is worth using the hierarchical representation to allow a better algorithm to be used.
    """)
    return


@app.cell
def hierarchical_vs_flat_runtime(pd, plt):
    _df = pd.read_csv("memo1a2/data_memos.csv")

    def box_scatter(x, y):
        _fig, ((_ax1, _ax2), (_ax3, _ax4)) = plt.subplots(2, 2, figsize=(6, 6), height_ratios=[14, 1], width_ratios=[1, 14])
        _ax2.scatter(x, y, c='b', marker='o', s=10, alpha=.01)
        _ax2.set_xlim(0, 10)
        _ax2.set_ylim(0, 10)

        _ax1.boxplot(y, orientation="vertical", widths=[.9])
        _ax1.set_ylim(0, 10)
        _ax1.margins(x=0)
        _ax1.set_axis_off()

        _ax4.boxplot(x, orientation="horizontal", widths=[.9])
        _ax4.set_xlim(0, 10)
        _ax4.margins(y=0)
        _ax4.set_axis_off()

        _ax3.set_axis_off()

        _fig.suptitle("Comparing Hierarchical & Flat graph implementations")
        _fig.supxlabel("Flat graph time (ms)")
        _fig.supylabel("Hierarchical graph time (ms)")

        _fig.tight_layout()
        return _fig

    box_scatter(_df["Memo1 time"], _df["Memo1A1 time"])
    return


@app.cell(hide_code=True)
def hierarchical_vs_flat_runtime_comment(get_fig, mo):
    mo.md(rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Comparing Hierarchical & Flat graph implementations")}</span>

    Figure {get_fig("Comparing Hierarchical & Flat graph implementations")} shows a runtime comparison of algorithms solving this problem on both the flat and hierarchical graph, implemented in python. This shows the hierarchical graph is ~10% better median, 12% better 3rd quartile, and a smaller inter-quartile range. This means it is consistently more efficient than the flat graph over the test set of 10,000 facility blueprints
    """)
    return


@app.cell(hide_code=True)
def hierarchical_no_adt_justification(mo):
    mo.md(r"""
    ### 2.5.1
    No new ADT operations are _required_ to use the hierarchical graph. Finding the wing of a vertex $v$ is possible in $|W|$ time by checking for each $w = (V_w, E_w) \in W$, if $v \in V_w$. This is possible due to assumption that each wing's vertex sets are disjoint. There is a tradeoff between storage and efficiency here, with storing the wings allowing for quick retrieval at the cost of space and getting the wings being a time cost. I chose to the latter option as it seemed in implementation that finding the wings did not affect performance to any noticeable amount
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.5.2 Flat Graph Is Better
    While it is certain for this algorithmic idea, a hierarchical graph abstraction is better, it could be argued for large $n$, [**Thorup99**](https://doi.org/10.1145/316542.316548), a linear time undirected single source shortest path (SSSP) algorithm would be better to find the shortest paths between between supplies, as its component tree structure is close to the facility's structure, and a minimum spanning tree can be found quite quickly due to the flattened facility graph being _almost_ a tree.

    This would remove the need for the creation of $F$, as the algorithm can be run on the original flattened facility. The reason why this is not applicable to this problem is due to the time constraint, with Thorup's SSSP algorithm being difficult to implement. It almost might suffer from the same problems as other efficient algorithms that will be considered: that $n$ isn't large enough to outweigh lower order costs of an algorithm. This is less likely to be a problem, as in stage 1 of the algorithm, the input graph has much larger $n$.
    """)
    return


@app.cell(hide_code=True)
def sector_traversal_costs(mo):
    mo.md(r"""
    ## 2.6 Sector traversal costs
    In this amendment, weighted sector traversal costs were added, but due to my abstraction already having a weight mapping $w$, which abstracts the costs of traversing between two sectors in the facility graph $G$. Wings are not treated differently, as weights are given as part of the abstraction precomputed. This allows for further abstraction of unnecessary features and avoid creating algorithms to address specific cost profiles of wings, which allows the algorithm to address new wings without revisions.
    """)
    return


@app.cell(hide_code=True)
def adts(mo):
    mo.md(r"""
    ## 2.7 ADTs
    Since we are using a hierarchical graph representation, we will need to represent this as an ADT. To do this, we will require one new ADT, the tuple. The Hyper

    We do _not_ need each vertex to store its wing, because we can check that by checking if that vertex is each wing's vertex set.

    Indices of ordered data structures and keys of maps will be accessed with `foo[index]` syntax. Lists will be created with `[a, b, ...]` syntax, tuples will be created with `(a, b, ...)` syntax, and sets will be created with `{a, b, ...}` syntax, with empty set being denoted by <span class="pseudocode-bracket">∅</span>.

    A recap of each ADT and its signature specifications are below:

    ### 2.7.1 Graph

    Edges are a tuple of two vertices

    - $\text{get\_vertices}: \text{Graph} \to \text{Set}[\text{Vertex}]$
    - $\text{get\_edges}: \text{Graph} \to \text{Set}[\text{Edge}]$
    - $\text{add\_vertex}: \text{Graph} \times \text{Vertex} \to \text{Graph}$
    - $\text{add\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \times \mathbb{R}^+ \cup \{0\} \to \text{Graph}$
    - $\text{remove\_vertex}: \text{Graph} \times \text{Vertex} \to \text{Graph}$
    - $\text{remove\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \to \text{Graph}$
    - $\text{get\_neighbours}: \text{Graph} \times \text{Vertex} \to \text{Set}[\text{Vertex}]$
    - $\text{has\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \to \text{Boolean}$
    - $\text{get\_vertices}: \text{Graph} \to \text{Set}[\text{Vertex}]$
    - $\text{set\_edge\_weight}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \times \mathbb{R}^+ \cup \{0\} \to \text{Graph}$
    - $\text{get\_edge\_weight}: \text{Graph} \times \text{Vertex} \times \text{Vertex}) \to \mathbb{R}^+ \cup \{0\}$

    ### 2.7.2 Set
    - $\text{union}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{intersection}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{symmetric\_difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{size}: \text{Set} \to \mathbb{R}^+ \cup \{0\}$
    - $\text{element\_of}: \text{Set} \times \text{Item} \to \text{boolean}$
    - $\text{strict\_subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{are\_equal}: \text{Set} \times \text{Set} \to \text{boolean}$

    ### 2.7.3 Map
    - $\text{size}: \text{Map} \to \mathbb{R}^+ \cup \{0\}$
    - $\text{has}: \text{Map} \times \text{Key} \to \text{boolean}$
    - $\text{at}: \text{Map} \times \text{Key} \to \text{Value}$
    - $\text{remove}: \text{Map} \times \text{Key} \to \text{Map}$
    - $\text{set}: \text{Map} \times \text{Key} \times \text{Value} \to \text{Map}$
    - $\text{get\_keys}: \text{Map} \to \text{Set}[\text{Key}]$

    ### 2.7.3 List
    - $\text{push}: \text{List} \times \text{Item} \to \text{List}$
    - $\text{pop}: \text{List} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ### 2.7.4 Array
    - $\text{set}: \text{Array} \times \mathbb{Z}^+ \times \text{Item} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ### 2.7.5 Tuple
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ### 2.6.6 ADT Non-extension Justification
    It was suggested that an ADT operation was required that, given a sector, returns adjacent unvisited sectors that contain no previously collect supply units. This operation could be used in either the **depth first search** or **dijkstra's algorithm** procedures in the algorithm, but is not useful.

    However my algorithm handles both parts of this operation as procedures of the algorithm. In stage 1, it removes previously collected supplies from the supplies set. In the **depth first search** step, while it would then be possible to traverse less of the tree, it could be possible for a uncollected supply to be on the path to a collected supply, and therefore adding this operation and using it could remove the possibility of collecting certain supplies in a facility.

    While no such facility blueprint has been discovered, this small optimisation is not worth the risk of the algorithm not working on future facilities. We want to minimise assumptions not clearly defined in the mission directive as we do not know if all facilities have supplies at dead-ends.

    Additionally, this addition would not assist in the **dijkstra's algorithm** step or the entirety of stage 2, which combined, account for the majority of the time cost of this algorithm.
    """)
    return


@app.cell(hide_code=True)
def adt_justification(mo):
    mo.md(r"""
    ## 2.6 Justification of Each ADT
    Above, I justified the use of the graph in the hierarchical representation.

    By using a graph, we can encapsulate only the salient features of the facility, where other structures would introduce non-salient features.

    Since a correct output must go from the entry sector to an entry sector, it is required to give the corresponding vertices of the graph as input to the algorithm. The same reasoning applies to the supplies set, as an optimal walk through the facility should collect all supplies. An alternate way of abstracting the problem, particularly supplies is discussed [below](## 2.7 An Alternate Problem Abstraction), so more justification of the supply set is there.

    The last three parameters abstract CRUDY-1's supply storage. An array with fixed length is suitable for CRUDY-1's fixed-size supply storage and due to the non-uniqueness of supply units, supply vertex to supply id lookup with a map allows non-collection of duplicate supplies. These collected supplies are stored in a set due to fast `contains` checks and the non-requirement of an ordered data structure.
    """)
    return


@app.cell(hide_code=True)
def alternate_problem_abstraction(mo):
    mo.md(r"""
    ## 2.7 An Alternate Problem Abstraction
    One problem with this abstraction is it only assigns reward to supplies. In the problem description, it says walk length should be minimised _and_ that maintaining structural integrity is important. This suggest that there might be some penalty with traversing large portions of the facility that may outweigh collecting a distant supply. I will first propose an alternate abstraction to the problem that encapsulates this aim and then justify why that abstraction is not suitable for this problem.

    The abstraction adds a new function $r: \text{Vertex} \times \text{Vertex} \to \mathbb{R}$, which gives reward or penalty of traversing from the first input vertex to the second one. We can assign each edge entering a supply vertex a positive reward and each other edge a negative one. We also must disallow traversing a supply vertex more than once.

    This problem, however is more complex than the original problem, with the problem not being reducible to a travelling salesman like problem with $n = |S| = 5$ as each edge and therefore vertex must be considered in the walk. Due to the problem being a minimum cost walk, it is more complex than a travelling salesman problem, and due to its minimisation nature, a integer linear program formulation may seem possible, but will not be nearly as efficient as an algorithm run on the abstraction proposed above.

    Additionally, solutions to the abstraction above will traverse a particular edge in the vast majority of cases two times, which often cannot be reduced due to each wing being a tree, therefore there is often only 1 path between two sectors. This means solutions to the abstraction above will often be optimal or close to optimal in this more complex problem.

    The difficulty of this new abstraction also causes exact algorithms to be likely to inefficient, which means heuristic solutions may even be worse than solution found on the abstraction above. This is the reason this alternate abstraction is not the one used when solving this problem.

    However, this abstraction does better encapsulate the problem's facets, and if more time was given, a more efficient algorithm could be found for this abstraction that gives better results. This time constraint due to the urgency of the situation does constrain the complexity of algorithms used, unfortunately.
    """)
    return


@app.cell(hide_code=True)
def algorithm_design_header(mo):
    mo.md(r"""
    # 3 Algorithm Design
    """)
    return


@app.cell(hide_code=True)
def algorithmic_approaches(mo):
    mo.md(r"""
    ## 3.1 Algorithmic Approaches
    We will first consider multiple algorithmic approaches to this problem, before choosing a subset of them to be used in the final algorithm. This will include both design patterns and methods of formulating the problem.

    ### 3.1.1 Stage 1

    The first stage of the algorithm will be to find the shortest paths between each supply, entrance and exit vertex in $G$. We then turn this into super graph $G_S$

    Since we are using a hierarchical abstraction of the facility, there are two shortest path cases: intra-wing and inter-wing.

    For shortest paths that are inter-wing, due to the tree structure of each wing, there is only 1 path between each vertex, and thus it will be the shortest path. We can use BFS or DFS to find this shortest path in linear time.

    For shortest paths that are intra-wing, we will use dijkstra's on a graph of supplies, entrances, exits and junctions. This is possible because intra-wing paths _must_ pass through at least one junction. This inner abstraction reduces the size of $n$, as we cannot use DFS or BFS here.

    If the shortest path is between two vertices in the same wing, we have a lower-bound from the previous case and can early-return if we are not finding a shorter path, which improves efficiency.

    This sub-problem is best solved by Dijkstra's algorithm. Due to small $n$, more efficient alternatives like Duan et al. 2025 and Thorup 1999, which solve the problem in sub quasi-linear time and linear time respectively, will not be considered due to high constant costs and difficulty of implementation.

    ### 3.1.2 Stage 2

    The second stage of the algorithm is to find the ordering of supplies that produces the shortest walk on $G$ from the entrance vertex, through each supply and ending at an exit vertex. The first stage allows a smaller $n$ for algorithms used here, as it allows $n$ to be $|S|$ instead of $|V|$.

    Since this problem is similar to the Travelling Salesman Problem (TSP), we will primarily consider design approaches that are used to solve this problem.

    #### 3.1.2.1 Greedy & Heuristic

    Greedy patterns are often efficient, but will be unlikely to find an optimal solution, unless the problem has the greedy property. Due to small $n$, and the facility not having the greedy property, we will avoid Greedy algorithms in finding an exact solution. Greedy algorithms will be used in the algorithm to provide a fast upper-bound on path length which is useful for other approaches.

    Heuristic algorithms are more efficient ways of searching a small subset of the solution space that is likely to hold the optimal solution. They will also used to provide a fast upper-bound. **2-opt** and **3-opt** are powerful heuristics running in $O(n^2)$ and $O(n^3)$ respectively and get much closer than **nearest neighbour**. **Lin-kernighan**, which adapts the **k-opt**, runs in $O(n^{2.2})$ time and is much close than both 2 and 3-opt. This can be chained, combined with a meta-heuristic algorithm **tabu-search** to prohibit found local minima and hopefully find a global minima.

    #### 3.1.2.2 Backtracking & Linear Programming

    The problem can be expressed as a integer linear program (ILP) that if solved, will give the optimal solution to any problem instance as shown below. $\begin{array}{lrrll}
    \text{min} & \displaystyle\sum_{u \in S \cup \{e\}} \displaystyle\sum_{v \in S \cup X} c_{uv} x_{uv} & & & \\
    \text{s.t.} & \displaystyle\sum_{v \in S \cup X} & x_{uv} & = 1 & \forall u \in S \cup \{e\}; \\
    & \displaystyle\sum_{u \in S \cup \{e\}} & x_{uv} & = 1 & \forall v \in S; \\
    & \displaystyle\sum_{u \in Q \cup \{e\}} \displaystyle\sum_{v \in Q \cup X} & x_{uv} &\leq |S| + 1 & \forall Q \subseteq S; \\
    & & x_{uv} &\in \{0, 1\} & &
    \end{array}$

    where $x_{uv} = \begin{cases}
    1 &  \text{path goes from u to v} \\
    x   &  \text{otherwise}
    \end{cases}$

    However, solving this problem naively will be slower than even **brute force**, as the final constrain is actually $|S|!$ constraints, leading to worse than factorial time. We instead relax this problem to a linear program and remove the subcycle elimination constraint with

    $\begin{array}{lrrll}
    \text{min} & \displaystyle\sum_{u \in S \cup \{e\}} \displaystyle\sum_{v \in S \cup X} c_{uv} x_{uv} & & & \\
    \text{s.t.} & \displaystyle\sum_{v \in S \cup X} & x_{uv} & = 1 & \forall u \in S \cup \{e\}; \\
    & \displaystyle\sum_{u \in S \cup \{e\}} & x_{uv} & = 1 & \forall v \in S; \\
    & 0 \leq & x_{uv} &\leq 1 & &
    \end{array}$

    We can then use **branch and cut**, a backtracking algorithm, to add only subcycle elimination constraints that are broken, allowing for "only" quadratic-in-$n$ constraints. **Branch and cut** is a variant of **branch and bound**, and we will calculate the lower bound of a branch by solving a linear relaxation of the problem by removing $x \in \{0, 1\}$ from the restrictions, but leaving other cuts. If this lower bound is higher than the lower bound we have found, we backtrack early.

    Then we check if the solution breaks any of the subcycle elimination constraints, adding them and repeating until we have a solution that doesn't break any of these constraints. If $\forall u, v, x_{uv} \in \{0, 1\}$, we have a new lower bound and we backtrack as this is the lower bound of this branch, otherwise we branch from this node to two nodes, one where a non-integer $x_{uv} = 0$, and one where that $x_{uv} = 1$.

    We can also check if this solution is optimal by inputting it into the dual problem, where if it is optimal, it should be a valid solution.

    The dual problem, with $y_v$ being the dual variable for $\displaystyle\sum_{u \in S \cup \{e\}} x_{uv} = 1$, $z_u$ being the dual variable for $\displaystyle\sum_{v \in S \cup X} x_{uv} = 1$ and $W_Q$ being the dual variable for $\displaystyle\sum_{u \in Q \cup \{e\}} \displaystyle\sum_{v \in Q \cup X} x_{uv} \leq |S| + 1$ can be found by setting $A \leftarrow A^T$, swapping $b$ and $c$, and setting the inequality of the constraints to $\leq$ (for minimisation) of the linear program expressed in canonical form:

    $$\begin{array}{lrrll}
    & \text{maximise} & \displaystyle\sum_{v \in S \cup x} y_v + \displaystyle\sum_{u \in S \cup \{e\}} z_u & & & \\
    & \text{subject to} & y_u + z_v + \displaystyle\sum_{\{u, v\} \in \delta(Q)} W_Q &\leq c_{uv} &\forall u \in S \cup \{e\}, v \in S \cup X \\
    & & y_u, z_v &\in \mathbb{R} & &
    \end{array}$$

    The problem with all this is the $n$ is so small that constant and lower order costs of solving linear programming problems many times is greater than other more naive algorithms.

    Additionally, this linear program only works for the subset of problems where CRUDY-1 has exactly the same number of supplies it could collect in the facility to the number of supply storage slots it has. In the case it has fewer supply storage slots, a linear program for this problem will be much more difficult to create.

    #### 3.1.2.3 Branch and bound

    Instead of linear programming overhead, we will instead create a tree whose root vertex is the entry, and leaf vertices are the exits. The branch vertices will be supplies, and the tree will contain each possible ordering of supplies. We can then find lower and upper bounds for a particular branch vertex and prune it if its lower bound is greater or equal to the lowest found upper bound

    To calculate the lower bounds, we will add to the current branch's walk minimum cost edges until there are $k + 1$ edges, where $k$ is

    To calculate the upper bound, we can find one greedily using a greedy algorithm considered above. We will use a modification of the **Lin-Kernighan Heuristic** for this purpose. As shown below, we can expect ~12% solution gap for 5 supplies.

    #### 3.1.2.4 Brute Force

    This problem has small enough $n$ that even the cost of repeatedly finding lower bounds is enough to make naive **brute force** more efficient than **branch and bound** and **Lin-Kernighan**, beaten only by **nearest neighbour** and one other algorithm, the former of which is not exact.

    #### 3.1.2.5 Dynamic Programming

    Top-down **dynamic programming** uses memoisation to store solutions of recursive sub-problems and when the sub-problem is called again, it can recall the solution. This is particularily effective in this problem due to often finding sub-problem solutions. Memoisation in the problem results in $T(n) = n + n(n - 1) + n(n - 1)(n - 2) + \dots + \frac{n!}{\lfloor \frac{n}{2} \rfloor!} + \frac{n!}{\lceil \frac{n+1}{2} \rceil!} + \dots + n + 1 = O(n^{\lfloor \frac{n}{2} \rfloor}) < O(n!)$, which makes it faster than **brute force**, with the downside of requiring more space.
    """)
    return


@app.cell
def runtime_fig(pd, plt):
    _df = pd.read_csv("memo1a2/data_stage_2.csv")

    _dot_size = 2.
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 6))

    def _plot(ax, name, c, label):
        ax.scatter([i+2 for i in range(len(_df[name]))], _df[name], c=c, label=label, s=_dot_size)


    _plot(_ax1, "brute force time", "b", "Brute force")
    _plot(_ax1, "branch & bound time", "r", "Branch and bound")
    _plot(_ax1, "dynamic programming time", "purple", "Dynamic programming")
    _plot(_ax1, "nearest neighbour time", "g", "Nearest neighbour")
    _plot(_ax1, "lin-kernighan time", "orange", "Lin-Kernighan")
    _ax1.legend(loc="upper right")
    _ax1.set_yscale("log", base=10)

    _dot_size = 3.
    _local_range = range(3, 8)
    _range_len = _local_range.stop - _local_range.start
    def _plot(ax, name, c, label):
        ax.plot(list(_local_range), _df[name][_local_range.start - 2:_local_range.stop - 2], "-o", c=c, label=label, ms=_dot_size)

    _plot(_ax2, "brute force time", "b", "Brute force")
    _plot(_ax2, "branch & bound time", "r", "Branch and bound")
    _plot(_ax2, "dynamic programming time", "purple", "Dynamic programming")
    _plot(_ax2, "nearest neighbour time", "g", "Nearest neighbour")
    _plot(_ax2, "lin-kernighan time", "orange", "Lin-Kernighan")
    _ax2.legend(loc="upper right")
    _ax2.set_yscale("log", base=10)
    _ax2.set_xticks(_local_range)

    _fig.suptitle("Different approaches' runtime")
    _fig.supxlabel("Supply Unit (# of)")
    _fig.supylabel("Runtime (s)")
    _fig.tight_layout()

    _fig
    return


@app.cell(hide_code=True)
def runtime_explanation(get_fig, mo):
    mo.md(rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Different approaches' runtime")}</span><br>
    <span style="color: var(--ctp-mocha-overlay1); font-size: 10px">Note the logarithmic scale</span>

    ### 3.1.3 Evaluation of Runtimes
    The left of figure {get_fig("Different approaches' runtime")} shows that for large $n$, **brute force** has the worst run-time, followed closely by **branch and bound**, and dynamic programming . The heuristic algorithms then follow, with **Lin-Kernighan** running **nearest neighbour** to get its first guess (which it finds a local solution of), it takes longer than **nearest neighbour** does.

    However, the right of figure {get_fig("Different approaches' runtime")} shows that at $n = |S| = 5$ as it is in the problem, **dynamic programming** runs an order of magnitude faster than **brute force** and **branch and bound**. While it is ~1.5 orders of magnitude slower than **nearest neighbour**, it is still very fast and is optimal. This is the reason why it will be used over those other more efficient approaches.

    If $n$ was to increase, it will become impossible to consider **brute force** and **dynamic programming**, and **branch and bound** will only be usable with significant optimisations (discussed later). This can be seen in the left figure, with **brute force** and **dynamic programming** these algorithms not being graphed after $n = 20$
    """)
    return


@app.cell
def optimality_sol_gap_fig(np, pd, plt):
    _df = pd.read_csv("memo1a2/data_stage_2_100_trials.csv")

    _dot_size = 2.
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 6))

    def _plot(ax, name, c, label):
        ax.scatter([i+2 for i in range(len(_df[name]))], _df[name], c=c, label=label, s=_dot_size)

    _plot(_ax1, "brute force length", "b", "Brute force")
    _plot(_ax1, "branch & bound length", "r", "Branch and bound")
    _plot(_ax1, "dynamic programming length", "purple", "Dynamic programming")
    _plot(_ax1, "nearest neighbour length", "g", "Nearest neighbour")
    _plot(_ax1, "lin-kernighan length", "orange", "Lin-Kernighan")
    _ax1.set_title("Different approaches' solution length")
    _ax1.legend(loc="upper right")
    _ax1.set_ylabel("Average Solution Length (units)")


    _dot_size = 3.
    _local_range = range(3, 8)
    _range_len = _local_range.stop - _local_range.start

    _solution_gap_len = len([None for i in np.isnan(_df["brute force length"]) if not i])
    def _solution_gap(data) -> list[float]:
        return [100 * (data[i] - _df["brute force length"][i]) / _df["brute force length"][i] for i in range(min(_solution_gap_len, len([None for i in data if i])))]

    def _plot(ax, name, c, label):
        ax.plot([i+2 for i in range(_solution_gap_len)], _solution_gap(_df[name]), "-o", c=c, label=label, ms=_dot_size)

    _plot(_ax2, "brute force length", "b", "Brute force")
    _plot(_ax2, "branch & bound length", "r", "Branch and bound")
    _plot(_ax2, "dynamic programming length", "purple", "Dynamic programming")
    _plot(_ax2, "nearest neighbour length", "g", "Nearest neighbour")
    _plot(_ax2, "lin-kernighan length", "orange", "Lin-Kernighan")
    _ax2.set_title("Different approaches' optimality gap")
    _ax2.legend(loc="upper right")
    _ax2.set_ylabel("Average Solution Gap (%)")

    _fig.supxlabel("Supply Unit (# of)")
    _fig.tight_layout()

    _fig
    return


@app.cell(hide_code=True)
def optimality_sol_gap_explanation(get_fig, mo):
    mo.md(rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Different approaches' solution length")}</span><br>
    <span style="color: var(--ctp-mocha-overlay1); font-size: 10px">Note the logarithmic scale</span>

    ### 3.1.4 Optimality & Solution Gap
    As seen in figure {get_fig("Different approaches' solution length")}, each algorithm poses a different gap from the optimal solution. An algorithm for a problem is optimal iff it has 0 solution gap on *all* problem instances. We calculate solution gap with $\displaystyle\frac{{\text{{Heuristic - Optimal}}}}{{\text{{Optimal}}}}$, and while **Lin-Kernighan** has a slightly better solution for large $n$. If the supply count were to reach a level where it is not possible to use an exact algorithm, **Lin-Kernighan** would be one of the best algorithms to use.
    """)
    return


@app.cell(hide_code=True)
def other_stage_2_opts_header(mo):
    mo.md(r"""
    ## 3.2 Other Stage 2 Options
    """)
    return


@app.cell(hide_code=True)
def branch_and_bound_explanation(mo):
    mo.md(r"""
    ### 3.2.1 Branch and Bound
    Branch and bound solves an optimisation problem by searching through the solution tree using either depth or breath first search. It finds sub-problems of the original problem and eliminates ones that cannot contain the optimal solution by finding their lower and upper bounds, comparing against the best found upper bound. If a subproblem $P'$ has a lower bound greater than the best upper bound, it cannot contain the solution and therefore does not need to be explored. This can reduce the solution tree in the average and best cases depending on the problem and the 'tightness' of the bounds: how close they are to the true lower and upper bounds of $P'$. To maintain correctness, the lower bound must be inclusive of the true lower bound and the upper bound must be inclusive of the true upper bound such that $lb_\text{true} \leq lb_\text{heuristic} \leq ub_\text{heuristic} \leq ub_\text{true}$. Due to the algorithm requiring fast lower and upper bound calculation, this is done with heuristic methods.

    While **branch and bound** and **brute force** share $\Theta(n!)$ worst case, the former will be much faster for large $n$. This, however is what makes it not suitable for this problem, as with $n = |S| = 5$, the cost of finding bounds outweighs the benefits of this algorithm.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.2.2 Brute force

    Brute force searches the entire solution space of the problem exhaustively, finding the best solution and returning it. It excels in testing optimality and correctness of other algorithms and in cases where $n$ is small.
    """)
    return


@app.cell(hide_code=True)
def lin_kernighan_explanation(mo):
    mo.md(r"""
    ### 3.2.3 Lin-Kernighan
    Lin-Kernighan is a heuristic algorithm for optimising a found solution to a shortest-path or cycle problem. It swaps different combinations of edges to find the local minimum of a solution. This will always produce a better or equal path than the one found, so it is a good step for finding a close-to-optimal solution for **branch and bound** algorithms or optimising a different heuristic algorithm.

    This algorithm runs in $O(n^{2.2})$ average case, but has significant constant and lower order costs, which make it less efficient than **dynamic programming** for this problem, while giving non-optimal solutions
    """)
    return


@app.cell(hide_code=True)
def nearest_neighbour_explanation(mo):
    mo.md(r"""
    ### 3.2.4 Nearest Neighbour
    Nearest neighbour is a greedy algorithm, which due to the physical representation of this problem being _almost_ a tree, performs quite well on this problem. It runs in $O(n^2)$ worst case, but with $n$ being small, **dyanmic programming** can find an optimal solution in an adequate amount of time
    """)
    return


@app.cell(hide_code=True)
def linear_programming_explanation(mo):
    mo.md(r"""
    ### 3.2.5 Linear programming
    For large $n$ travelling salesman problems, **branch and cut**, a combination of **branch and bound**, and **the cutting plane method**, performs well. This is normally done by solving a relaxed version of the problem and adding cuts back when the original problem's cuts are broken. Solving these relaxed linear programs can be done with the **simplex method**, however for $n = 5$, just one run of the algorithm takes longer than any other approach considered.

    Additionally, due to CRUDY-1 needing to pick up fewer than 5 supplies if it is carrying some, I was unable to create a tight enough linear program for this problem to be useful.
    """)
    return


@app.cell(hide_code=True)
def wing_traversal_strategy(mo):
    mo.md(r"""
    ## 3.2 Wing traversal strategy
    The algorithm will traverse between wings based on the best walk, not necessarily collecting each supply in a wing before moving to the next wing and often coming back to a wing previously traversed through. This was done to use a common path optimisation where directly travelling between two junctions in a wing, $j_1$ and $j_2$, may be slower than a path through $j_1$, $j_1'$, $j_2'$ and $j_2$, where $j_n'$ is the vertex a junction connects to via an interwing corridor.

    Since we are still aiming for an exact algorithm that always outputs the optimal solution, we must allow for revisiting wings and partial collection of supplies.
    """)
    return


@app.cell(hide_code=True)
def revised_algorithm_header(mo):
    mo.md(r"""
    ## 3.3 Revised Algorithm
    """)
    return


@app.cell(hide_code=True)
def algorithm_explanation(mo):
    mo.md(r"""
    ### 3.3.1 Explanation
    We split the algorithm into two stages, with the first stage creating a flat graph, $F$, where each vertex is a supply, junction, entry or exit, and edges between vertices exist if they are in the same wing, after which we will find the shortest path on $F$ between each entry and supply, and each exit and supply, creating a complete graph $H$ using these minimum cost paths as edge weights.

    In the second stage, the algorithm will find the shortest hamiltonian path on this second graph which starts at the entry and ends at an exit.

    For the first stage, we will run a depth first search on each wing to get a path between each vertex and a arbitrarily chosen source vertex. Since each wing is a tree, these paths must be shortest paths and we can find the shortest path between each vertex in the wing by tracing back the path from each vertex to the chosen vertex and removing any cycle in that path. A graph $F$ will be created using these shortest path distances, storing those shortest paths so we can convert between the $G$ and $F$ later. $F$ will contain every wing's vertices.

    After that, Dijkstra's algorithm will be run on $F$ to find the shortest paths between each entry and supply, and each exit and supply. The creation of $F$ efficiently reduces the size of $n$ for the input to Dijkstra's algorithm. These shortest paths will form a complete graph $H$ where each vertex is an entry, supply or exit and each edge's weight is the total cost of the shortest path between two vertices in $H$. We will likewise store these shortest paths for the path reconstruction.

    In the second stage, a **dynamic programming** algorithm will find the shortest hamiltonian walk on $H$. After which we use all the stored paths to reconstruct the final returned walk by converting from a walk on $H$, to one on $F$, finally to one on $G$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.3.2 Comparison with previous solutions
    While comparing this solution to the one from the previous amendment would be pointless (they're the same), comparing with Memo1 shows differences. That memo's solution does not use the tree structure of each wing, and skips the itermediatary $F$ graph. This causes it to run sub-optimally on the current facility given the flat abstraction.

    The need to abstract this property causes no limitations or downsides compared with the previous abstraction (from amendment 1), but if I was to have had each wing be an unweighted graph and using a flat graph abstraction, this would've removed the possibility of using depth or breath first search on the entire facility to get the shortest path between each supply.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.3.3 Comparison with previous facility
    With the addition of non-uniform cost sector traversal, CRUDY-1 avoids backtracking through the right of wing Beta. This is apparent in my facility with seed `28122007`, where in the previous facility, it collects $s_2$ when it passes by the upper junction between wings Alpha and Beta, whereas in the new facility, the cost of this traversal and backtrack causes this to be not done. This new solution walk is longer in terms of sectors traversed through but shorter in terms of total cost than the walk that collects $s_2$ earlier.
    """)
    return


@app.cell
def _(pd, plt):
    _df = pd.read_csv("memo1a2/data_facility.csv")

    _dot_size = 2.
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(12, 6))

    small_number = 1e-4
    _ax1.hist((_df["solution_len"] - _df["solution_len_unweighted"]) / _df["solution_len"], [-small_number, small_number, .01, .02, .03, .04, .05])
    _ax1.set_title("Solution hops on Weighted vs Unweighted Facilities")
    _ax1.set_ylabel("Difference between weighted and unweighted facility path lengths %")
    _ax1.set_ylim(0, 10000)

    _ax2.hist((_df["solution_cost_unweighted"] - _df["solution_cost"]) / _df["solution_len"], [-small_number, small_number, .01, .02, .03, .04, .05, .06, .07, .08, .09, .1])
    _ax2.set_title("Solution cost on Weighted vs Unweighted Facilities")
    _ax2.set_ylabel("Difference between weighted and unweighted facility path costs %")
    _ax2.set_ylim(0, 10000)

    _fig.tight_layout()

    _fig
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Weighted vs Unweighted Facilities")}</span><br>

    ### 3.1.4 Optimality & Solution Gap
    As seen in figure {get_fig("Weighted vs Unweighted Facilities")}, compared with the abstraction of uniform facility traversal cost, only ~2.5% of facilities had a longer optimal path and with the algorithm and abstraction from amendment 1, only ~7% of paths had greater cost on the new abstraction's $G$. The '0' bucket was decreased in width to highlight this fact.
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
        label="Step (drag to walk through the trace) ",
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
def pseudocode_and_impl_header(mo):
    mo.md(r"""
    # 4 Pseudocode & Implementation
    """)
    return


@app.cell(hide_code=True)
def pseudocode_header(mo):
    mo.md(r"""
    ## 4.1 Pseudocode
    Notes for Pseudocode:
    - RAISE is used when a function _may_ not return something, but that would occur only for an invalid input
    - SupplyID is a identifier for each supply, which is unique from each other supply that has different contents
    """)
    return


@app.cell
def pseudocode(mo, re):
    def _parse_pseudocode(code: str) -> str:
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
        res = re.sub(r"FOR(?=. <-)", "<span class='pseudocode-command'>FOR</span>", res)
        res = re.sub("IF(?= )", "<span class='pseudocode-command'>IF</span>", res)
        for command in ["PROCEDURE", "FUNCTION", "WHILE", "FOR", "IF"]:
            res = re.sub(f"END {command}", f"<span class='pseudocode-command'>END {command}</span>", res)


        for command in ["AND", "OR", "NOT", "RAISE", "DO", "THEN", "IN", "TO", "RETURN"]:
            res = re.sub(fr"(?:(?<=\s)|(?<=&#9;)|(?<=\<br\>)){command}(?:(?=\s)|(?=&#9;)|(?=\<br\>))", f"<span class='pseudocode-command'>{command}</span>", res)

        for operator in [r"<-", "=", ">", "<", "<=", ">=", "+", "-"]:
            res = re.sub(fr"(?<= ){operator}(?= )",  f"<span class='pseudocode-op'>{operator}</span>", res)


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
            surrounding = r"\s\.\:\,\(\)\[\]\{\}\<\>"
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

        adt_operators = ["get_vertices","get_edges","add_vertex","add_edge","remove_vertex","remove_edge","get_neighbours","has_edge","get_vertices","set_edge_weight","get_edge_weight","union","intersection","difference",'symmetric_difference',"size",'element_of',"strict_subset_of","subset_of","are_equal","size","has","at","remove","set","get_keys","push","pop","get","set","get","length",
        "enqueue","update_priority"]

        res = syntax_highlight_name(res, list(set(adt_operators)) + ["List", "Array", "Set", "Map", "Graph", "Tuple", "Priority Queue", "Positive Integer", "Integer", "Real"], "pseudocode-atomic")
        res = syntax_highlight_name(res, list(set(procedures)), "pseudocode-proc")
        res = syntax_highlight_name(res, ["SupplyID", "Vertex"], "pseudocode-type")

        res = find_all(res, "PROCEDURE</span>", syntax_highlight_proc)
        res = find_all(res, "FUNCTION</span>", syntax_highlight_proc)

        return res

    mo.md(rf"""
    <div style="font-family: monospace; font-size: 14px; white-space: pre-wrap;">{_parse_pseudocode(open("memo1a1/raw_pseudocode.txt", encoding="utf-8").read())}</div>
    """)
    return


@app.cell(hide_code=True)
def pseudocode_procedure_justification(mo):
    mo.md(r"""
    ### 4.1.1 Pseudocode Procedure Justification
    While many procedures can be justified due to duplication of use, encapsulating a well-known algorithm which improves the coherence of the pseudocode, or for labelling the goal or output of a block of code, some procedures need justification for why they weren't inlined.

    `get_path_from_bfs` is an example of one such that is easily traceable, and could be instead labelled with a comment. The reason why these were turned into procedures were to allow for implementors of this algorithm to more easily find optimisations that I may be unaware of. For a particular implementation, a memoisation modification of this procedure may increase the algorithm's efficiency, and by extracting this code as a procedure, it is easier to notice blocks of code that may run often and could be further optimised.
    
    In the function `ember_rescue`, the stages of the algorithm could be encapsulated in their own procedures. This was not done as it would require more auxiliary space in certain implementations, and this procedure would only be used once.
    """)
    return


@app.cell(hide_code=True)
def python_impl_header(mo):
    mo.md(r"""
    ## 4.2 Python Implementation
    """)
    return


@app.cell(hide_code=True)
def python_impl(mo):
    mo.ui.code_editor(open("memo1a1/raw_python.txt", encoding="utf-8").read(), disabled=True)
    return


@app.cell(hide_code=True)
def justification(mo):
    mo.md(r"""
    # 5 Justification
    """)
    return


@app.cell(hide_code=True)
def suitability(mo):
    mo.md(r"""
    ## 5.1 Suitability
    ### 5.1.1 Assumptions
    To allow for a more optimised solution, our algorithm makes assumptions about the problem:

    These assumptions are justified by checking a large quantity of facility blueprints, all of which satisfied the property:
    - Each wing being a tree graph allows for a more efficient algorithm used in stage 1.
    - The facility having at most 4 wings, and each wing being a 12x12 grid of sectors guides our choice of a exact algorithm: **dynamic programming** for stage 2, as well as the approach of abstracting the graph into a path cost matrix.
    - 5 supplies in the facility allows **dynamic programming**, **branch and bound** or **branch and bound** for stage 2. Without significant optimisations, these exact approaches would not be possible if the supplies grows above 7 or 8.
    - Each wing is connected, allows only 1 depth first search to be run on each wing. Without this assumption, we would need to run it starting from each supply, entry, exit and junction in each wing, drastically reducing the time and space efficiency of the algorithm which would also need to store each `prev` Map.
    - Each sector is connected to its adjacent sectors bi-directionally, which may if the previous assumption is not satisfied disallow collection of some supplies that are reachable but cannot be walked through and then to an exit.

    ### 5.1.2 Quality of Solutions
    The algorithm finds the global optimum, with brute force searching the entire solution space. Compared with the previous uniform cost facility, the algorithm avoids backtracking in the right part of Wing Beta. Particularily, in my seed, 28122007, the algorithm does not collect supply 2 when going past the junction connecting to the top of Wing Beta because it avoids the cost of backtracking and then eventually traversing that path again later. The path found traverses through 50 sectors more than when the algorithm was not informed of this non-uniform traversal cost.
    """)
    return


@app.cell(hide_code=True)
def coherence(mo):
    mo.md(r"""
    ## 5.2 Coherence
    - I use $\text{get\_neighbours}: \text{Graph} \times \text{Vertex} \to \text{Vertex}$ in the dijkstra's algorithm implementation in the algorithm to get the neighbours of the current visited vertex
    - I use $\text{has}: \text{Map} \times \text{Key} \to \text{Boolean}$ to reconstruct the shortest paths found by dijkstra's algorithm
    - Originally, I was going to use **branch and bound**, with the **Lin-Kernighan heuristic**, which requires the symmetric difference set operation, $\Delta$, which wasn't in the set ADT signature, which I resolved by adding a procedure for it
    - A consistent pseudocode style was used to allow correct implementation
    """)
    return


@app.cell(hide_code=True)
def fit_for_purpose(mo):
    mo.md(r"""
    ## 5.3 Fit for Purpose
    The algorithm considers each operational constraint:
    - Load capacity: $A$ holds the supplies that CRUDY-1 currently holds
    - Extraction: The algorithm always terminates at an exit
    - Energy budget: The algorithm always finds a minimum cost walk through the facility that collects all supplies and exits at an exit
    - Revisiting sectors: Is allowed and is used to find the shortest path
    - Supply collection: $\text{get\_unfound\_supplies}: \text{Set}[\text{Vertex}] \times \text{Map}[\text{Vertex}, \text{String or NULL}] \times Set[String] \to \text{Set}[\text{Vertex}]$ makes sure CRUDY-1 ignores already collected supplies
    - Objective: All supplies will be collected and there are no energy constraints
    - Mission Directive:
      - The algorithm does not priorities structural stability, as we have not information about how CRUDY-1 has any affect on the stability of sectors of the facility
      - The algorithm will always have a successful extraction if one exists.

    The algorithm is robust to different numbers and sizes of wings, and differing numbers of junction sectors, however would fail to run if there are too many supplies. In the case that a new report notices increased numbers of supplies and adjusts CRUDY-1's supply storage to collect more supplies, **brute force** and **dynamic programming** will be unusable and **branch and bound** will need to be further optimised, replaced with **branch and cut**, or may be not possible, in which case a heuristic approach will be used instead.
    """)
    return


@app.cell(hide_code=True)
def correctness_and_optimality(mo):
    mo.md(r"""
    ## 5.4 Correctness & Optimality
    On a test set of 100,000 facilities of different seeds, all outputs of the algorithm were correct. This means the algorithm is likely to be correct.

    The algorithm's stages also force correctness, with a solution always starting with the entry and ending with a vertex due to the fuel parameter of the recursive **dynamic programming** procedure. It also stores a map that can be used to transform between each abstracted graph created by the algorithm.

    **Dynamic programming** searches the entire solution space exhaustively, caching previously solved sub-problems, meaning it will find a global optimal solution. These maps convert this solution back to a walk on $G$, which means the algorithm will be optimal.
    """)
    return


@app.cell(hide_code=True)
def tractability(mo):
    mo.md(r"""
    ## 5.5 Tractability
    Since the size of $S$, $X$ and $A$ are constant for all problem instances, the algorithm only grows with the sizes of $V_w$, $E_w$, $V$, $E$, $M$ and $F$. The latter two are only used to remove already-collected supplies, which is done with a for-each loop, giving linear time complexity. The former four are related to the dijkstra's cost of finding the shortest paths between supplies, the intra-wing BFS step and creating the salient graph.

    Tractability is defined as running in polynomial time for each non-constant parameter.

    The dijkstra's cost is in order $O(n \log n + m)$, where $n$ is the number of supplies, exits, entrances and junctions combined and $m$ is the number of intra-wing edges between these, and the inter-wing edges between the junction. This gives a time complexity in order $O(|E_W| \log |E_W| + |E| + |E_W|), which is tractable.

    The intra-wing BFS step is in order $O(|V_k| + |E_k|)$ for each wing, thus it is in $O(|V| + |E|)$, which is tractable.

    The creation of the salient graph is a double nested for loop iterating on the entry, exit, supply and junction vertices, inside a loop on each wing. This gives a complexity in $O(|V_W||E_W|^2)$, which is tractable.

    Since each cost that scales with the non-constant variables runs in polynomial time, the algorithm is tractable.
    """)
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
