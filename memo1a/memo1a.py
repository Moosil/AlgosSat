import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium", app_title="Memo1A1", css_file="../custom.css")


@app.cell
def _():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import pandas as pd
    import numpy as np
    from scipy import stats
    import copy
    from itertools import chain
    import re
    import inspect

    return (
        chain,
        copy,
        inspect,
        mo,
        mpatches,
        np,
        nx,
        pd,
        plt,
        random,
        re,
        stats,
    )


@app.cell
def _():
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
def _(chain, copy, mpatches, nx, plt, random, seed_input):
    class GraphDrawer:
        def __init__(self) -> None:
            self.WING_COLS, self.WING_ROWS = 10, 10

            self.n_wings, self.wing_names, self.wings, self.entry, self.exit_a, self.exit_b, self.supplies, self.junctions = self._get_multi_wing_facility(seed_input.value)

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
                    if d == 2 and w_u not in self.supplies and w_u not in {self.exit_a, self.exit_b,
                                                                           self.entry} and w_u not in set(
                        chain(*self.junctions)):
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

        def _get_multi_wing_facility(self, seed):
            int_seed = int(seed)
            n_wings = 2 + (int_seed % 3)  # 2, 3, or 4 wings from seed
            wing_names = ['Alpha', 'Beta', 'Gamma', 'Delta'][:n_wings]

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
                    if len(supplies) >= 5:
                        break
                    for n in wl:
                        if n not in supplies:
                            supplies.append(n)
                            break
                if len(supplies) >= 5:
                    break

            return n_wings, wing_names, wings, entry, exit_a, exit_b, supplies[:5], junctions

        def draw_multi_wing(self, highlight_path=None, node_colors=None,
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

            total_w = self.n_wings * self.WING_COLS + (self.n_wings - 1) * _GAP

            fig_w = max(10., total_w * 0.35)
            fig_h = max(5., self.WING_ROWS * 0.35 + 1.2)
            fig, ax = plt.subplots(figsize=(fig_w, fig_h))
            ax.set_facecolor(COL_BG)
            fig.patch.set_facecolor(COL_BG)

            def xoff(w):
                return w * (self.WING_COLS + _GAP)

            # Draw each wing
            for w, wing in enumerate(self.wings):
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
                for i in range(len(highlight_path) - 1):
                    w1, c1, r1 = highlight_path[i]
                    w2, c2, r2 = highlight_path[i + 1]
                    ax.plot(
                        [xoff(w1) + c1 + 0.5, xoff(w2) + c2 + 0.5],
                        [r1 + 0.5, r2 + 0.5],
                        color=COL_PATH, lw=1.8, linestyle='--',
                        alpha=0.75, zorder=4)

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
def _(mo):
    mo.md(r"""
    # Settings
    """)
    return


@app.cell
def _(mo):
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
def _(mo):
    mo.md(r"""
    # Memo 1 Amendment 1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
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
    ## 1.1 Limitations of Previous Model
    - The previous model assumed the facility was just the one wing
    - The previous model wasn't taking full advantage of properties of this problem
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1.2 Amendment Revisions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The previous algorithm assumed the facility was just one wing, and could be represented as a tree. While it could work on this graph with a flat graph abstraction, I chose to instead revise the abstaction to a heuristic one for the new problem.

    I also discovered new ways of doing both stages of the algorithm, which were tested to determine that brute force is still the best way of doing this problem...
    """)
    return


@app.cell(hide_code=True)
def _(mo):
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
def _(mo):
    mo.md(r"""
    ## 2.1 Signature specification:
    $\text{ember\_rescue}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \times \text{Array}[\text{SupplyID}, 5] \times \text{Map}[\text{Vertex}, \text{SupplyID}] \times \text{Set}[\text{SupplyID}] \to \text{List}[\text{Vertex}] \times \text{Array}[\text{SupplyID}, 5]$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.2 Output Constraints
    The algorithm should output an ordered sequence of vertices $(v_1, v_2, \dots, v_n)$, with $\forall m < n, v_m \in V \cup V_w$, $v_1 = s$, and $v_n \in X$. It should aim to collect as many supply vertices as possible, while reducing the total cost of this walk, $\displaystyle\sum_{i=0}^{n - 1} w(v_i, v_{i + 1})$.

    The algorithm should return CRUDY-1's new supply storage, updating it with each supply collected: $\forall i \leq |A|, A_\text{new}[i] \neq A[i] \implies A[i] = \text{NULL}$, $A[i] \neq \text{NULL} \iff A_\text{new} = A[i]$ and $\forall v \text{ in } W | v \in S, A_\text{new} \text{ contains } v$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
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
def _(mo):
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
def _(mo):
    mo.md(r"""
    ## 2.5 Hierarchical vs Flat graph
    When adapting from a single-wing facility to a multi-wing one, there are two obvious ways to represent the multiple wings.

    Recall in Memo 1, the facility's singular wing was represented as a graph, with each vertex representing a salient sector and each edge a connecting walk between thoses salient sectors.

    The **Hierarchical graph** representation uses a meta-graph, a graph where each vertex is another graph, to represent the wings of the facility. Each wing is an vertex in the meta-graph and the connecting coridoors between each wing will be the edges. These vertex-graphs will be represented the same way as in Memo 1.

    The **Flat graph** representation uses a graph to representing the facility. The facility will be represented the same way as in Memo 1, except edges can now also represent inter-wing coridoors between junction sectors.

    First we can notice that, with an algorithmic process, it is possible to flatten the hierarchical graph into the flat graph by adding each vertex and edge in each vertex of the meta-graph to a empty graph and then adding each edge from the meta-graph as an edge in this graph. Therefore we can conclude that the hierarchical graph has more information than the flat graph, and the flat graph _loses_ information.

    If we were to adopt the flat representation and continue to use the previous algorithm, we would notice a performance penalty, as our dijkstra's algorithm cost scales with the number of vertices in the full flat representation. With 4 wings, this is barely noticable, but if new information was to reveal a larger facility, the cost would quickly become enough to make the algorithm not feasable.

    This hierarchical graph represents the physical properties of the facility more closely, and this additional information can be used to inform a more efficient algorithm. There is only a small, linear-time cost associated with converting the hierarchical graph to the flat graph representation, and therefore it is worth using the hierarchical representation to allow a better algorithm to be used.
    """)
    return


@app.cell
def _(np, pd, plt, stats):
    _df = pd.read_csv("memo1a/data_memos.csv")

    _df = _df[(np.abs(stats.zscore(_df)) < 2).all(axis=1)]

    _fig, ((_ax1, _ax2), (_ax3, _ax4)) = plt.subplots(2, 2, figsize=(6, 6), height_ratios=[14, 1], width_ratios=[1, 14])
    _ax2.scatter(_df["Memo1 time"], _df["Memo1A1 time"], c='b', label="Brute force", marker='o', s=10, alpha=.01)
    _ax2.set_xlim(0, 10)
    _ax2.set_ylim(0, 10)

    _ax1.boxplot(_df["Memo1A1 time"], orientation="vertical", widths=[.9])
    _ax1.set_ylim(0, 10)
    _ax1.margins(x=0)
    _ax1.set_axis_off()

    _ax4.boxplot(_df["Memo1 time"], orientation="horizontal", widths=[.9])
    _ax4.set_xlim(0, 10)
    _ax4.margins(y=0)
    _ax4.set_axis_off()

    _ax3.set_axis_off()

    _fig.suptitle("Comparing Hierarchical & Flat graph implementations")
    _fig.supxlabel("Flat graph time (ms)")
    _fig.supylabel("Hierarchical graph time (ms)")

    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(get_fig, mo):
    mo.md(rf"""
    <span style="color: var(--ctp-mocha-subtext0); ">Figure {get_fig("Comparing Hierarchical & Flat graph implementations")}</span>

    Figure {get_fig("Comparing Hierarchical & Flat graph implementations")} shows a runtime comparison of algorithms solving this problem on btoh the flat and hierarchical graph, implemented in python. This shows the hierarhical graph is ~9% better median, 25% better 3rd quartile, and a smaller inter-quartile range. This means it is consistently more efficient than the flat graph over the test set of 10,000 facility blueprints
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.5.1
    No new ADT operations are _required_ to use the hierarchical graph. Finding the wing of a vertex $v$ is possible in $|W|$ time by checking for each $w = (V_w, E_w) \in W$, if $v \in V_w$. This is possible due to assumption that each wing's vertex sets are disjoint. There is a tradeoff between storage and efficiency here, with storing the wings allowing for quick retrieval at the cost of space and getting the wings being a time cost. I chose to the latter option as it seemed in implementation that finding the wings did not affect performance to any noticeable amount
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.6 ADTs
    Since we are using a hierarchical graph representation, we will need to represent this as an ADT. To do this, we will require one new ADT, the tuple. The Hyper

    We do _not_ need each vertex to store its wing, because we can check that by checking if that vertex is each wing's vertex set.

    `foo.bar(a, b)` syntax will be used in pseudocode, rather than `bar(foo, a, b)`, and mathematical operators will be preferred for size of ADTs and set operations. Indices of ordered data structures and keys of maps will be accessed with `foo[index]` syntax. Lists will be created with `[a, b, ...]` syntax, tuples will be created with `(a, b, ...)` syntax, and sets will be created with `{a, b, ...}` syntax, with empty set being denoted by $\varnothing$

    A recap of each ADT and its signature specifications are below:

    ### 2.6.1 Graph

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

    ### 2.6.2 Set
    - $\text{union}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{intersection}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{symmetric\_difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{size}: \text{Set} \to \mathbb{R}^+ \cup \{0\}$
    - $\text{element\_of}: \text{Set} \times \text{Item} \to \text{boolean}$
    - $\text{strict\_subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{are\_equal}: \text{Set} \times \text{Set} \to \text{boolean}$

    ### 2.6.3 Map
    - $\text{size}: \text{Map} \to \mathbb{R}^+ \cup \{0\}$
    - $\text{has}: \text{Map} \times \text{Key} \to \text{boolean}$
    - $\text{at}: \text{Map} \times \text{Key} \to \text{Value}$
    - $\text{remove}: \text{Map} \times \text{Key} \to \text{Map}$
    - $\text{set}: \text{Map} \times \text{Key} \times \text{Value} \to \text{Map}$
    - $\text{get\_keys}: \text{Map} \to \text{Set}[\text{Key}]$

    ### 2.6.3 List
    - $\text{push}: \text{List} \times \text{Item} \to \text{List}$
    - $\text{pop}: \text{List} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ### 2.6.4 Array
    - $\text{set}: \text{Array} \times \mathbb{Z}^+ \times \text{Item} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ### 2.6.5 Tuple
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.6 Justification of Each ADT
    Above, I justified the use of the graph in the hierarchical representation.

    By using a graph, we can encapsulate only the salient features of a wubg, where other structures would introduce non-salient features.

    Each other parameter represents physical salient features of the facility, and without them, the problem would not be encapsulated in this abstraction.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 3 Algorithm Design
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.1 Algorithmic Approaches
    We will first consider multiple algorithmic approaches to this problem, before choosing a subset of them to be used in the final algorithm. This will include both design patterns and methods of formulating the problem.

    ### 3.1.1 All Pairs Shortest Paths

    The first stage of the algorithm will be to find the shortest paths between each supply, entrance and exit vertex in $G$. We then turn this into super graph $G_S$

    Since we are using a hierachical abstraction of the facility, there are two shortest path cases: intra-wing and inter-wing.

    For shortest paths that are inter-wing, due to the tree structure of each wing, there is only 1 path between each vertex, and thus it will be the shortest path. We can use BFS or DFS to find this shortest path in linear time.

    For shortest paths that are intra-wing, we will use dijkstra's on a graph of supplies, entrances, exits and junctions. This is possible because intra-wing paths _must_ pass through at least one junction. This inner abstraction reduces the size of $n$, as we cannot use DFS or BFS here.

    If the shortest path is between two vertices in the same wing, we have a lower-bound from the previous case and can early-return if we are not finding a shorter path, which improves efficiency.

    This sub-problem is best solved by Dijkstra's algorithm. Due to small $n$, more efficient alternatives like Duan et al. 2025 and Thorup 1999, which solve the problem in sub quasi-linear time and linear time respectively, will not be considered due to high constant costs and difficulty of implementation.

    ### 3.1.2 Supply Order Selection

    The second stage of the algorithm is to find the ordering of supplies that produces the shortest walk on $G$ from the entrance vertex, through each supply and ending at an exit vertex. The first stage allows a smaller $n$ for algorithms used here, as it allows $n$ to be $|S|$ instead of $|V|$.

    Since this problem is similar to the Travelling Salesman Problem (TSP), we will primarily consider design approaches that are used to solve this problem.

    #### 3.1.2.1 Greedy & Heuristic

    Greedy patterns are often efficient, but will be unlikely to find an optimal solution, unless the problem has the greedy property. Due to small $n$, and the facility not having the greedy property, we will avoid Greedy algorithms in finding an exact solution. Greedy algorithms will be used in the algorithm to provide a fast upper-bound on path length which is useful for other approaches.

    Heuristic algorithms are more efficient ways of searching a small subset of the solution space that is likely to hold the optimal solution. They will also used to provide a fast upper-bound. 2-opt and 3-opt are powerful heuristics running in $O(n^2)$ and $O(n^3)$ respectively and get much closer than nearest neighbour. Lin-kernighan, which adapts the k-opt, runs in $O(n^{2.2})$ time and is much close than both 2 and 3-opt. This can be chained, combined with a meta-heuristic algorithm tabu-search to prohibit found local minima and hopefully find a global minima.

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

    However, solving this problem nievely will be slower than brute force, as the final constrain is actually $|S|!$ constraints, leading to worse than factorial time. We instead relax this problem to a linear program and remove the subcycle elimination constraint with

    $\begin{array}{lrrll}
    \text{min} & \displaystyle\sum_{u \in S \cup \{e\}} \displaystyle\sum_{v \in S \cup X} c_{uv} x_{uv} & & & \\
    \text{s.t.} & \displaystyle\sum_{v \in S \cup X} & x_{uv} & = 1 & \forall u \in S \cup \{e\}; \\
    & \displaystyle\sum_{u \in S \cup \{e\}} & x_{uv} & = 1 & \forall v \in S; \\
    & 0 \leq & x_{uv} &\leq 1 & &
    \end{array}$

    We can then use branch and cut, a backtracking algorithm, to add only subcycle elimination constraints that are broken, allowing for "only" quadratic-in-$n$ constaints. Branch and cut is a variant of branch and bound, and we will calculate the lower bound of a branch by solving a linear relaxation of the problem by removing $x \in \{0, 1\}$ from the restrictions, but leaving other cuts. If this lower bound is higher than the lower bound we have found, we backtrack early.

    Then we check if the solution breaks any of the subcycle elimination constraints, adding them and repeating until we have a solution that doesn't break any of these constraints. If $\forall u, v, x_{uv} \in \{0, 1\}$, we have a new lower bound and we backtrack as this is the lower bound of this branch, otherwise we branch from this node to two nodes, one where a non-integer $x_{uv} = 0$, and one where that $x_{uv} = 1$.

    We can also check if this solution is optimal by inputting it into the dual problem, where if it is optimal, it should be a valid solution.

    The dual problem, with $y_v$ being the dual variable for $\displaystyle\sum_{u \in S \cup \{e\}} x_{uv} = 1$, $z_u$ being the dual variable for $\displaystyle\sum_{v \in S \cup X} x_{uv} = 1$ and $W_Q$ being the dual variable for $\displaystyle\sum_{u \in Q \cup \{e\}} \displaystyle\sum_{v \in Q \cup X} x_{uv} \leq |S| + 1$ can be found by setting $A \leftarrow A^T$, swapping $b$ and $c$, and setting the inequality of the constraints to $\leq$ (for minimisation) of the linear program expressed in canonical form:

    $$\begin{array}{lrrll}
    & \text{maximise} & \displaystyle\sum_{v \in S \cup x} y_v + \displaystyle\sum_{u \in S \cup \{e\}} z_u & & & \\
    & \text{subject to} & y_u + z_v + \displaystyle\sum_{\{u, v\} \in \delta(Q)} W_Q &\leq c_{uv} &\forall u \in S \cup \{e\}, v \in S \cup X \\
    & & y_u, z_v &\in \mathbb{R} & &
    \end{array}$$

    The problem with all this is the $n$ is so small that constant and lower order costs of solving linear programming problems many times is greater than other more nieve algorithms.

    Additionally, this linear program only works for the subset of problems where CRUDY-1 has exactly the same number of supplies it could collect in the facility to the number of supply storage slots it has. In the case it has fewer supply storage slots, a linear program for this problem will be much more difficult to create.

    #### 3.1.2.3 Branch and bound

    Instead of linear programming overhead, we will instead create a tree whose root vertex is the entry, and leaf vertices are the exits. The branch vertices will be supplies, and the tree will contain each possible ordering of supplies. We can then find lower and upper bounds for a particular branch vertex and prune it if its lower bound is greater or equal to the lowest found upper bound

    To calculate the lower bounds, we will add to the current branch's walk minimum cost edges until there are $k + 1$ edges, where $k$ is

    To calculate the upper bound, we can find one greedily using a greedy algorithm considered above. We will use a modification of the Lin-Kernighan Heuristic for this purpose. As shown below, we can expect ~12% solution gap for 5 supplies.

    #### 3.1.2.4 Brute-force

    Unfortunately, this problem has small enough $n$ that even the cost of repeatedly finding lower bounds is enough to make nieve brute force more efficient than Branch and bound and Lin-Kernighan, beaten only by Nearest neighbour, which is not exact. Since the runtime of Brute-force in this problem is low, we will use the same algorithm as in Memo 1 for stage 2, recursive brute-force.
    """)
    return


@app.cell
def _(pd, plt):
    _df = pd.read_csv("memo1a/data_stage_2.csv")

    _dot_size = 2.
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 6))

    def _plot(ax, name, c, label):
        ax.scatter([i+2 for i in range(len(_df[name]))], _df[name], c=c, label=label, s=_dot_size)


    _plot(_ax1, "brute force time", 'b', "Brute force")
    _plot(_ax1, "branch & bound time", 'r', "Branch and bound")
    _plot(_ax1, "nearest neighbour time", 'g', "Nearest neighbour")
    _plot(_ax1, "lin-kernighan time", 'orange', "Lin-Kernighan")
    _ax1.legend(loc="upper right")
    _ax1.set_yscale("log", base=10)

    _dot_size = 3.
    _local_range = range(3, 8)
    _range_len = _local_range.stop - _local_range.start
    def _plot(ax, name, c, label):
        ax.plot(list(_local_range), _df[name][_local_range.start - 2:_local_range.stop - 2], "-o", c=c, label=label, ms=_dot_size)

    _plot(_ax2, "brute force time", 'b', "Brute force")
    _plot(_ax2, "branch & bound time", 'r', "Branch and bound")
    _plot(_ax2, "nearest neighbour time", 'g', "Nearest neighbour")
    _plot(_ax2, "lin-kernighan time", 'orange', "Lin-Kernighan")
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
def _(mo):
    mo.md(r"""
    ### 3.1.3 Evaluation of Runtimes
    As expected, Brute force has the worst run-time, followed closely by Branch-and-bound. The heuristic algorithms then follow, with Lin-Kernighan running Nearest neighbour to get its first guess (which it finds a local solution of), it takes longer than Nearest neighbour does.
    <br><span style='color: silver;'>(as seen in left figure)</span>

    At $n = 5 = |S|$, which is what $|S|$ is in the problem, we can notice that Brute force runs an order of magnitude faster than Branch and bound. While it is ~1.5 orders of magnitude slower than nearest neighbour, it is still very fast and is optimal. This is the reason why it will be used over those other more efficient approaches.
    <br><span style='color: silver;'>(as seen in right figure)</span>

    If $n$ was to increase, it will become impossible to consider Brute-force, and Branch-and-bound will only be usable with significant optimisations (discussed later). This can be seen in the left figure, with both these algorithms not being graphed after $n = 12$
    """)
    return


@app.cell
def _(np, pd, plt):
    _df = pd.read_csv("memo1a/data_stage_2_100_trials.csv")

    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 6))
    _ax1.scatter([i+2 for i in range(len(_df["brute force length"]))], _df["brute force length"], c='b', label="Brute force", marker='.')
    _ax1.scatter([i+2 for i in range(len(_df["branch & bound length"]))], _df["branch & bound length"], c='r', label="Branch and bound", marker='.')
    _ax1.scatter([i+2 for i in range(len(_df["nearest neighbour length"]))], _df["nearest neighbour length"], c='g', label="Nearest neighbour", marker='.')
    _ax1.scatter([i+2 for i in range(len(_df["lin-kernighan length"]))], _df["lin-kernighan length"], c='orange', label="Lin-Kernighan", marker='.')
    _ax1.set_title("Different approaches' solution length")
    _ax1.legend(loc="upper right")
    _ax1.set_ylabel("Average Solution Length (units)")

    _solution_gap_len = len([None for i in np.isnan(_df["branch & bound length"]) if not i])

    def _solution_gap(data) -> list[float]:
        return [100 * (data[i] - _df["branch & bound length"][i]) / _df["branch & bound length"][i] for i in range(min(_solution_gap_len, len([None for i in data if i])))]

    _dot_size = 8
    _ax2.scatter([i+2 for i in range(_solution_gap_len)], _solution_gap(_df["brute force length"]), c='b', label="Brute force", marker='o', s=_dot_size, alpha=.7)
    _ax2.scatter([i+2 for i in range(_solution_gap_len)], _solution_gap(_df["branch & bound length"]), c='r', label="Branch and bound", marker='o', s=_dot_size, alpha=.7)
    _ax2.scatter([i+2 for i in range(_solution_gap_len)], _solution_gap(_df["nearest neighbour length"]), c='g', label="Nearest neighbour", marker='o', s=_dot_size, alpha=.7)
    _ax2.scatter([i+2 for i in range(_solution_gap_len)], _solution_gap(_df["lin-kernighan length"]), c='orange', label="Lin-Kernighan", marker='o', s=_dot_size, alpha=.7)
    _ax2.set_title("Different approaches' optimality gap")
    _ax2.legend(loc="upper right")
    _ax2.set_ylabel("Average Solution Gap (%)")

    _fig.supxlabel("Supply Unit (# of)")
    _fig.tight_layout()

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.1.4 Optimality & Solution Gap
    Each algorithm poses a different gap from the optimal solution. An algorithm for a problem is optimal iff it has 0 solution gap on *all* problem instances. We calculate solution gap with $\displaystyle\frac{\text{Heuristic - Optimal}}{\text{Optimal}}$, and while Lin-Kernighan has a slighly better solution for large $n$ <span style='color: silver;'>(as seen in left figure)</span>, for small $n$, which what this problem is, the solution provided by Nearest neighbour is a local optimal, and thus Lin-Kernighan cannot further optimise it <span style='color: silver;'>(as seen in right figure)</span>.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.2 Other Stage 2 Options
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.2.1 Branch and Bound
    Branch and bound solves an optimisation problem by searching through the solution tree using either depth or breath first search. It finds sub-problems of the original problem and eliminates ones that cannot contain the optimal solution by finding their lower and upper bounds, comparing against the best found upper bound. If a subproblem $P'$ has a lower bound greater than the best upper bound, it cannot contain the solution and therefore does not need to be explored. This can reduce the solution tree in the average and best cases depending on the problem and the 'tightness' of the bounds: how close they are to the true lower and upper bounds of $P'$. To maintain correctness, the lower bound must be inclusive of the true lower bound and the upper bound must be inclusive of the true upper bound such that $lb_\text{true} \leq lb_\text{heuristic} \leq ub_\text{heuristic} \leq ub_\text{true}$. Due to the algorithm requiring fast lower and upper bound calculation, this is done with heuristic methods.

    While branch and bound and brute force share $O(n!)$ worst case, branch and bound will be much faster for large $n$. This, however is what makes it not suitable for this problem, as with $n = |S| = 5$, the cost of finding bounds outweighs the benefits of this algorithm.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.2.2 Lin-Kernighan
    Lin-Kernighan is a heuristic algorithm for optimising a found solution to a shortest-path or cycle problem. It swaps different combinations of edges to find the local minimum of a solution. This will always produce a better or equal path than the one found, so it is a good step for finding a close-to-optimal solution for branch and bound algorithms or optimising a different heuristic algorithm.

    This algorithm runs in $O(n^{2.2})$ average case, but has significant constant and lower order costs, which make it less efficient than brute force for this problem, while giving non-optimal solutions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.2.3 Nearest Neighbour
    Nearest neighbour is a greedy algorithm, which due to the physical representation of this problem being _almost_ a tree, performs quite well on this problem. It runs in $O(n^2)$ worst case, but with $n$ being small, brute force can find an optimal solution in an adequate amount of time
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.2.4 Linear programming
    For large $n$ travelling salesman problems, branch and cut, a combination of branch and bound, and the cutting plane method, performs well. This is normally done by solving a relaxed version of the problem and adding cuts back when the original problem's cuts are broken. Solving these relaxed linear programs can be done with the simplex method, however for $n = 5$, just one run of the simplex method takes longer than any other approach considered.

    Additionally, due to CRUDY-1 needing to pick up fewer than 5 supplies if it is carrying some, I was unable to create a tight enough linear program for this problem to be useful.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.2 Wing traversal strategy
    The algorithm will traverse between wings based on the best walk, not necessarily collecting each supply in a wing before moving to the next wing and often coming back to a wing previously traversed through. This was done to use a common path optimisation where directly travelling between two junctions in a wing, $j_1$ and $j_2$, may be slower than a path through $j_1$, $j_1'$, $j_2'$ and $j_2$, where $j_n'$ is the vertex a junction connects to via an interwing coridoor.

    Since we are still aiming for an exact algorithm that always outputs the optimal solution, we must allow for revisiting wings and partial collection of supplies.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.3 Revised Algorithm
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.3.1 Explanation
    We split the algorithm into two stages, with the first stage creating a flat graph, $F$, where each vertex is a supply, junction, entry or exit, and edges between vertices exist if they are in the same wing, after which we will find the shortest path on $F$ between each entry and supply, and each exit and supply, creating a complete graph $H$ using these minimum cost paths as edge weights.

    In the second stage, the algorithm will find the shortest hamiltonian path on this second graph which starts at the entry and ends at an exit.

    For the first stage, we will run a depth first search on each wing to get a path between each vertex and a arbitrarily chosen source vertex. Since each wing is a tree, these paths must be shortest paths and we can find the shortest path between each vertex in the wing by tracing back the path from each vertex to the chosen vertex and removing any cycle in that path. A graph $F$ will be created using these shortest path distances, storing those shortest paths so we can convert between the $G$ and $F$ later. $F$ will contain every wing's vertices.

    After that, Dijkstra's algorithm will be run on $F$ to find the shortest paths between each entry and supply, and each exit and supply. The creation of $F$ efficiently reduces the size of $n$ for the input to Dijkstra's algorithm. These shortest paths will form a complete graph $H$ where each vertex is an entry, supply or exit and each edge's weight is the total cost of the shortest path between two vertices in $H$. We will likewise store these shortest paths for the path reconstruction.

    In the second stage, a brute force algorithm will find the shortest hamiltonian walk on $H$. After which we use all the stored paths to reconstruct the final returned walk by converting from a walk on $H$, to one on $F$, finally to one on $G$.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.3.2 Algorithm Explorer
    """)
    return


@app.cell
def _(facility_drawer, memo1a_algorithm, mo):
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
def _(mo):
    mo.md(r"""
    These value **HIGHLY** depend on the marimo virtual machine, and can vary by orders of magnitude. On my machine, I get Runtime: 2.72ms, Memory: 336 B
    """)
    return


@app.cell
def _(facility_drawer, mo):
    import memo1a_algorithm

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
def _(ember_rescue_cached, facility_drawer, mo, path_len):
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
def _(mo):
    mo.md(r"""
    # 4 Pseudocode & Implementation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4.1 Pseudocode
    Notes for Pseudocode:
    - RAISE is used when a function _may_ not return something, but that would occur only for an invalid input
    - SupplyID is a identifier for each supply, which is unique from each other supply that has different contents
    """)
    return


@app.cell
def _(mo, re):
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
    <div style="font-family: monospace; font-size: 14px; white-space: pre-wrap;">{_parse_pseudocode(open("memo1a/raw_pseudocode.txt", encoding="utf-8").read())}</div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4.2 Python Implementation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.ui.code_editor(r"""import heapq
    from collections import defaultdict
    from itertools import chain
    from typing import Generator, Iterable

    import networkx as nx
    import numpy as np


    class VertexT:
        pass


    WingT = nx.Graph

    SupplyID = int

    SupplyStorage = tuple[SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None, SupplyID | None]


    def bfs(g: nx.Graph, source: VertexT) -> dict[VertexT, VertexT | None]:
        dist = {s: float('infinity') for s in g}

        dist[source] = 0

        visited = set()

        prev: dict[VertexT, VertexT | None] = dict({source: None})
        stack: list[VertexT] = [source]
        while len(stack) > 0:
            u = stack.pop()

            if u in visited:
                continue

            visited.add(u)

            for v in g.neighbors(u):
                w = g.get_edge_data(u, v)["weight"]
                if dist[u] + w < dist[v]:
                    prev[v] = u
                    dist[v] = dist[u] + w
                    stack.append(v)

        return prev


    def get_pair_shortest_path(source: VertexT, sink: VertexT, prev: dict[VertexT, VertexT | None]) -> list[VertexT]:
        left_path = [source]
        right_path = [sink]
        left = source
        right = sink
        while True:
            if prev[left] is not None:
                left = prev[left]
                left_path.append(left)
            if prev[right] is not None:
                right = prev[right]
                right_path.append(right)

            if right in left_path:
                right_index = left_path.index(right)
                return left_path[:right_index] + list(reversed(right_path))

            if left in right_path:
                left_index = right_path.index(left)
                return left_path + list(reversed(right_path[:left_index]))


    def get_supplies_to_collect(
        supplies: set[VertexT], vertex_to_supply_id: dict[VertexT, SupplyID], found_supply_ids: set[SupplyID],
        supply_storage: SupplyStorage
    ) -> set[VertexT]:
        return supplies.difference(
            (s for s in supplies if vertex_to_supply_id[s] in found_supply_ids or vertex_to_supply_id[s] in supply_storage)
        )


    def get_which_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], vertex: VertexT) -> WingT:
        for g in G[0]:
            if vertex in g.nodes:
                return g
        raise ValueError(f"vertex {vertex} is not in any graph in G")


    def get_vertices_in_wing(wing: WingT, vertices: Iterable[VertexT]) -> Generator[VertexT]:
        return (v for v in vertices if v in wing.nodes)


    def get_junctions_in_wing(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], wing: WingT) -> Generator[VertexT]:
        return get_vertices_in_wing(wing, chain(*G[1]))


    def get_junction_other(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], junction: VertexT) -> VertexT:
        edge = tuple(next(filter(lambda e: junction in e, G[1])))
        if edge[0] == junction:
            return edge[1]
        else:
            return edge[0]


    def reconstruct_path(came_from: dict[VertexT, VertexT | None], e: VertexT) -> list[VertexT]:
        res = []
        curr = e
        while curr in came_from:
            res.append(curr)
            curr = came_from[curr]
        res.reverse()
        return res


    def dijkstra(g: nx.Graph, source: VertexT, sinks: set[VertexT]) -> dict[VertexT, list[VertexT]]:
        res = {}
        dist = {s: float('infinity') for s in g}

        dist[source] = 0

        # visited set replaced update(PQ, v)
        visited = set()

        prev: dict[VertexT, VertexT | None] = {source: None}
        pq = [(0., source)]
        heapq.heapify(pq)
        while len(pq) > 0:
            _, u = heapq.heappop(pq)

            # required for the python heapq that doesn't allow changing priority
            if u in visited:
                continue
            visited.add(u)

            if u in sinks:
                res[u] = reconstruct_path(prev, u)
                if len(res) == len(sinks):
                    return res

            for v in g.neighbors(u):
                w = g.get_edge_data(u, v)["weight"]
                if dist[u] + w < dist[v]:
                    prev[v] = u
                    dist[v] = dist[u] + w
                    heapq.heappush(pq, (dist[v], v))

        return res


    def get_apsp(g: nx.Graph, entry: VertexT, exits: set[VertexT], supplies: set[VertexT]) -> dict[VertexT, dict[VertexT, list[VertexT]]]:
        res: dict[VertexT, dict[VertexT, list[VertexT]]] = defaultdict(dict)
        for source in supplies.union((entry,)):
            res[source] = dijkstra(g, source, supplies.union(exits))

        return res


    def get_path_length(g: nx.Graph, path: list[VertexT]) -> int:
        return sum(g.get_edge_data(path[i], path[i + 1])["weight"] for i in range(len(path) - 1))


    def get_apsp_dist(g: nx.Graph, pair_path_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> dict[VertexT, dict[VertexT, int]]:
        res: dict[VertexT, dict[VertexT, int]] = defaultdict(dict)
        for source, sink_dict in pair_path_map.items():
            for sink, path in sink_dict.items():
                res[source][sink] = get_path_length(g, path)

        return res


    def brute_force_recursive(source: VertexT, sinks: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], fuel: int) -> tuple[list[VertexT], int]:
        min_cost = float('infinity')
        min_cost_walk = None

        if fuel == 0:
            for sink in exits:
                cost = dist_matrix[source][sink]
                if cost < min_cost:
                    min_cost_walk = [sink]
                    min_cost = cost
        else:
            for sink in sinks:
                min_walk_through, cost = brute_force_recursive(sink, sinks.difference({sink}), exits, dist_matrix, fuel - 1)
                cost += dist_matrix[source][sink]
                if cost < min_cost:
                    min_cost = cost
                    min_cost_walk = [sink] + min_walk_through

        return min_cost_walk, min_cost


    def brute_force(entry: VertexT, supplies: set[VertexT], exits: set[VertexT], dist_matrix: dict[VertexT, dict[VertexT, int]], max_supplies: int) -> list[VertexT]:
        return [entry] + brute_force_recursive(entry, supplies, exits, dist_matrix, max_supplies)[0]

        def get_path_from_super_path(super_path: list[VertexT], apsp_map: dict[VertexT, dict[VertexT, list[VertexT]]]) -> list[VertexT]:
        res = []
        for i in range(len(super_path) - 1):
            pair_path = apsp_map[super_path[i]][super_path[i + 1]]
            res += pair_path
            if i != len(super_path) - 2:
                res.pop()

        return res


    def get_path_from_super_path_bfs(G: tuple[set[WingT], set[tuple[VertexT, VertexT]]], super_path: list[VertexT], prevs: dict[WingT, dict[VertexT, VertexT | None]]) -> list[VertexT]:
        res = []
        for i in range(len(super_path) - 1):
            u, v = super_path[i], super_path[i + 1]
            u_wing, v_wing = get_which_wing(G, u), get_which_wing(G, v)
            if u_wing == v_wing:
                pair_path = get_pair_shortest_path(u, v, prevs[u_wing])
                res += pair_path
                res.pop()
            else:
                res.append(u)
        res.append(super_path[-1])
        return res


    def get_salient_graph(G, entry, supplies, exits, prevs):
        res = nx.Graph()
        res.add_node(entry)

        res.add_nodes_from(supplies)

        res.add_nodes_from(exits)

        for u, v in G[1]:
            res.add_node(u)
            res.add_node(v)
            res.add_edge(u, v, weight=1)

        for wing in G[0]:
            salient_in_wing = list(get_vertices_in_wing(wing, (entry,))) + list(get_vertices_in_wing(wing, exits)) + list(get_vertices_in_wing(wing, supplies)) + list(get_vertices_in_wing(wing, [u for u, _ in G[1]] + [v for _, v in G[1]]))
            for i in range(len(salient_in_wing)):
                for j in range(i + 1, len(salient_in_wing)):
                    u, v = salient_in_wing[i], salient_in_wing[j]
                    path = get_pair_shortest_path(u, v, prevs[wing])
                    res.add_edge(u, v, weight=get_path_length(wing, path))

        return res

        def ember_rescue(
        G: tuple[set[WingT], set[tuple[VertexT, VertexT]]],
        entry: VertexT,
        exits: set[VertexT],
        supplies: set[VertexT],
        supply_storage: SupplyStorage,
        vertex_to_supply_id: dict[VertexT, SupplyID],
        found_supply_ids: set[SupplyID]
    ) -> tuple[list[VertexT], SupplyStorage]:
        res: list[VertexT]

        supplies = get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)

        number_of_supplies_to_collect = min(len(supplies), len([None for i in supply_storage if i is None]))

        prevs: dict[WingT, dict[VertexT, VertexT | None]] = {wing: bfs(wing, list(wing.nodes)[0]) for wing in G[0]}

        salient_graph = get_salient_graph(G, entry, supplies, exits, prevs)

        apsp_map = get_apsp(salient_graph, entry, exits, supplies)
        apsp_dist_map = get_apsp_dist(salient_graph, apsp_map)

        super_path = brute_force(entry, supplies, exits, apsp_dist_map, number_of_supplies_to_collect)

        res = get_path_from_super_path(super_path, apsp_map)
        res = get_path_from_super_path_bfs(G, res, prevs)

        j: int = 0
        collected_supplies = [v for v in res if v in supplies]
        supply_storage = list(supply_storage)
        for i in range(len(supply_storage)):
            if j >= number_of_supplies_to_collect:
                break
            if supply_storage[i] is None:
                supply_storage[i] = vertex_to_supply_id[collected_supplies[j]]
                j += 1

        supply_storage = tuple(supply_storage)

        return res, supply_storage""", disabled=True)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 5 Justification
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5.1 Suitability
    To allow for a more optimised solution, our algorithm makes assumptions about the problem:

    These assumptions are justified by checking a large quantity of facility blueprints, all of which satisfied the property:
    - Each wing being a tree graph allows for a more efficient algorithm used in stage 1.
    - The facility having at most 4 wings, and each wing being a 12x12 grid of sectors guides our choice of a nieve algorithm: brute force for stage 2, as well as the approach of abstracting the graph into a path cost matrix.
    - 5 supplies in the facility allows brute force and branch and bound for stage 2. Without significant optimisations, these exact approaches would not be possible if the supplies grows above 7 or 8.
    - Each wing is connected, allows only 1 depth first search to be run on each wing. Without this assumption, we would need to run it starting from each supply, entry, exit and junction in each wing, drastically reducing the time and space efficiency of the algorithm which would also need to store each `prev` Map.
    - Each sector is connected to its adjacent sectors bi-directionally, which may if the previous assumption is not satisfied disallow collection of some supplies that are reachable but cannot be walked through and then to an exit.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5.2 Coherence
    - I use $\text{get\_neighbours}: \text{Graph} \times \text{Vertex} \to \text{Vertex}$ in the dijkstra's algorithm implementation in the algorithm to get the neighbours of the current visited vertex
    - I use $\text{has}: \text{Map} \times \text{Key} \to \text{Boolean}$ to reconstruct the shortest paths found by dijkstra's algorithm
    - Originally, I was going to use Branch and bound, with the Lin-Kernighan heuristic, which requires the symmetric difference set operation, $\Delta$, which wasn't in the set ADT signature, which I resolved by adding a procedure for it
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5.3 Fit for Purpose
    The algorithm considers each operational constraint:
    - Load capacity: $A$ holds the supplies that CRUDY-1 currently holds
    - Extraction: The algorithm always terminates at an exit
    - Energy budget: The algorithm always finds a minimum cost walk through the facility that collects all supplies and exits at an exit
    - Revisiting sectors: Is allowed and is used to find the shortest path
    - Supply collection: $\text{get\_unfound\_supplies}: \text{Set}[\text{Vertex}] \times \{\text{Vertex} \to \text{String or NULL}\} \times Set[String] \to \text{Set}[\text{Vertex}]$ makes sure CRUDY-1 ignores already collected supplies
    - Objective: All supplies will be collected and there are no energy constraints
    - Mission Directive:
      - The algorithm does not priorities structural stability, as we have not information about how CRUDY-1 has any affect on the stability of sectors of the facility
      - The algorithm will always have a successful extraction if one exists.

    The algorithm is robust to different numbers and sizes of wings, and differing numbers of junction sectors, however would fail to run if there are too many supplies. In the case that a new report notices increased numbers of supplies and adjusts CRUDY-1's supply storage to collect more supplies, brute force will be unusable and branch & bound will need to be further optimised, replaced with branch and cut, or may be not possible, in which case a heuristic approach will be used instead.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 6 Appendix
    # 6.1
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 6.2 Python Implementations
    """)
    return


@app.cell
def _(inspect, mo):
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
def _(get_impl_appendix, memo1a_algorithm, mo):
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
