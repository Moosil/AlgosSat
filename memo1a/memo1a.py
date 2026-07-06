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

    return chain, copy, mo, mpatches, nx, plt, random


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
    - The previous model wasn't taking advantage of properties of this problem
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
    ### 1.2.1 Algorithm & Abstraction Changes
    The previous algorithm assumed the facility was just one wing, and could be represented as a tree. While it could work on this graph with a flat graph abstraction, I chose to instead revise the algorithm for the new problem.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 2 Abstraction
    Let $G = (V_w, E_w, w)$ be a meta-graph, with $V_w=\{W_1, W_2, \dots, W_k\}$ being a set of undirected weighted graphs, $E_w \subseteq \{\{u, v\} \vert u \in V_n, v \in V_m, n \neq m\}$ being a set of edges between adjacent wings, $W_n, W_m$ of the facility, with $k$ being the number of wings in the facility, and $\forall n \leq k, W_n = (V_n, E_n)$.

    $V = V_1 \cup V_2 \cup \dots \cup V_k$ and $\forall n, m \leq k, V_n \cap V_m = \varnothing \iff n \neq m$ and $V_n = V_m \iff n = m$, with $V$ representing the salient sectors of the facility $E = E_1 \cup E_2 \cup \dots \cup E_k$ and $\forall n, m \leq k, E_n \cap E_m = \varnothing \iff n \neq m$ and $E_n = E_m \iff n = m$, with $E$ representing the paths between those adjacent salient sectors, and positive integer edge weight function $w: E \cup E_w \to \mathbb{N}$ representing the spans of sectors between two salient sectors which are adjacent to just two other sectors. If $(u, v) \notin E$, define $w(u, v) = \infty$.

    We will designate source vertex $s \in V$, the set of sink vertices $X \subseteq V$, and the set of prize vertices $S \subseteq V$, each representing the entry, exit, and supply unit-containing sectors respectively.

    We will have $A$ be an array of size 5 representing CRUDY-1's supply unit storage, which contains `SupplyID`s or the null ID: 0, function $M: S \to \text{SupplyID}$ mapping each supply vertex to its `SupplyID`, and set $F$ be the set of found `SupplyID`s. When a supply is collected, it will be added to $A$, and $A_\text{new}$ will be returned.

    We will be designing an algorithm to traverse meta-graph $G$, from $s$ to an $x$, returning an ordered sequence of vertices in list $W$, and CRUDY-1's updated supply unit storage.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.1 Inputs & Outputs
    The specificities of the inputs and outputs are above, and both concise lists are below:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.1.1 Inputs
    1. $G$
    2. $s$
    3. $X$
    4. $S$
    5. $A$
    6. $M$
    7. $F$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2.1.2 Outputs
    1. $W$
    2. $A_\text{new}$
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.2 Output Constraints
    The algorithm should output an ordered sequence of vertices $(v_1, v_2, \dots, v_n)$, with $\forall m < n, v_m \in V \cup V_w$, $v_1 = s$, and $v_n \in X$. It should aim to collect as many supply vertices as possible.

    $\forall i \leq \text{length}(A), A_\text{new}[i] \neq A[i] \implies A[i] = \varnothing$ and $A[i] \neq \varnothing \iff A_\text{new} = A[i]$
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

    The **Hierarchical graph** representation uses a meta-graph, a graph where each vertex is a graph, to represent the wings of the facility. Each wing is an vertex in the meta-graph and the connecting coridoors between each wing will be the edges. These vertex-graphs will be represented the same way as in Memo 1.

    The **Flat graph** representation uses a graph to representing the facility. The facility will be represented the same way as in Memo 1, except edges can now also represent inter-wing coridoors between junction sectors.

    First we can notice that, with an algorithmic process, it is possible to flatten the hierarchical graph into the flat graph by adding each vertex and edge in each vertex of the meta-graph to a empty graph and then adding each edge from the meta-graph as an edge in this graph. Therefore we can conclude that the hierarchical graph has more information than the flat graph, and the flat graph _loses_ information.

    If we were to adopt the flat representation and continue to use the previous algorithm, we would notice a performance penalty, as our dijkstra's algorithm cost scales with the number of vertices in the full flat representation. With 4 wings, this is barely noticable, but if new information was to reveal a larger facility, the cost would quickly become enough to make the algorithm not feasable.

    This hierarchical graph represents the physical properties of the facility more closely, and this additional information can be used to inform a more efficient algorithm. There is only a small, linear-time cost associated with converting the hierarchical graph to the flat graph representation, and therefore it is worth using the hierarchical representation to allow a better algorithm to be used.
    """)
    return


@app.cell
def _():
    """Hierarchical vs Flat graph algorithm time"""
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

    For Set operations, the mathematical symbol will be preferred ($\cup$, $\cap$, $\backslash$, $\Delta$, $\vert \dots \vert$, $\in$, $\subset$, $\subseteq$ and $=$ respectively)

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
    - $\text{Keys}: \text{Map} \to \text{Set}[\text{Key}]$

    ### 2.6.3 List
    - $\text{push}: \text{List} \times \text{Item} \to \text{List}$
    - $\text{pop}: \text{List} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{is\_empty}: \text{List} \to \text{Boolean}$
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

    Heuristic algorithms are more efficient ways of searching a small subset of the solution space that is likely to hold the optimal solution. They will also used to provide a fast upper-bound. 2-opt and 3-opt are powerful heuristics running in $O(n^2)$ and $O(n^3)$ respectively and get much closer than nearest neighbour. Lin-kernighan, which adapts the k-opt, runs in $O(n^2.2)$ time and is much close than both 2 and 3-opt. This can be chained, combined with a meta-heuristic algorithm tabu-search to prohibit found local minima and hopefully find a global minima.

    #### 3.1.2.2 Backtracking & Linear Programming

    The problem can be expressed as a integer linear program (ILP) that if solved, will give the optimal solution to any problem instance as shown below. $\begin{array}{lrrll}
    \text{min} & \displaystyle\sum_{u \in S \cup \{e\}} \displaystyle\sum_{v \in S \cup X} c_{uv} x_{uv} & & & \\
    \text{s.t.} & \displaystyle\sum_{v \in S \cup X} & x_{uv} & = 1 & \forall u \in S \cup \{e\}; \\
    & \displaystyle\sum_{u \in S \cup \{e\}} & x_{uv} & = 1 & \forall v \in S; \\
    & \displaystyle\sum_{u \in Q \cup \{e\}} \displaystyle\sum_{v \in Q \cup X} & x_{uv} &\leq |S| + 1 & \forall Q \subseteq S; \\
    & & x_{uv} &\in \{0, 1\} & &
    \end{array}$

    where$x_{uv} = \begin{cases}
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

    #### 3.1.2.3 Backtracking & Greedy / Heuristic

    Instead of linear programming overhead, we will instead create a tree whose root node is the entry, and leaf nodes are the exits. The branch nodes will be supplies, and the tree will contain each possible ordering of supplies. Searching this tree exhaustively is too time consuming, but we will instead compute a lower bound for each branch and prune those that have a lower bound greater than an upper bound we find. We will prefer depth first search on this tree to hopefully reduce our upper bound.

    To calculate the lower bounds, we first define $T_x = (V_S', E_S', w_S)$ to be a minimum spanning tree of a subset of $G_S = (V_S, E_S, w_S)$, where $V_S' = V_S \ \{x\}$. Then our lower bound will be $\displaystyle\min_{x \in X} \displaystyle\sum_{\{u, v\} \in E_S'} w_S(u, v.

    To calculate the upper bound, we can find one greedily using a greedy algorithm considered above. We will use a modification of the Lin-Kernighan Heuristic for this purpose. As shown below, we can expect ~12% solution gap for 5 supplies.

    #### 3.1.2.4 Brute-force

    Unfortunately, this problem has small enough $n$ that even the cost of repeatedly finding lower bounds is enough to make nieve brute force more efficient than Branch and bound and Lin-Kernighan, beaten only by Nearest neighbour, which is not exact. Since the runtime of Brute-force in this problem is low, we will use the same algorithm as in Memo 1 for stage 2, recursive brute-force.
    """)
    return


@app.cell
def _(plt):
    _data_brute_force = [9.400000000000001e-06,2.164e-05,7.708000000000001e-05,0.0004078500000000001,0.0024332000000000004,0.01711474,0.16651036000000002,1.6340282600000002,16.59655123,130.9417754]
    _data_branch_and_bound = [0.00038199,0.00136872,0.00612076,0.022506820000000004,0.08311501,0.26701634,0.9436050100000001,1.5229356600000001,6.59688893,3.6579898]
    _data_nearest_neighbour = [6.270000000000001e-06,7.43e-06,1.4460000000000002e-05,1.163e-05,1.2760000000000001e-05,1.4540000000000001e-05,1.665e-05,1.8670000000000003e-05,2.1810000000000003e-05,2.472e-05,2.5810000000000005e-05,2.8840000000000002e-05,3.086e-05,4.2730000000000006e-05,3.951e-05,4.131e-05,4.388000000000001e-05,4.731e-05,8.1e-05,6.82e-05,6.96e-05,7.350000000000001e-05,7.900000000000001e-05,8.39e-05,8.67e-05,9.27e-05,0.0002538,0.0001431,9.94e-05,0.0001071,0.000115,0.0001194,0.0001269,0.0001297,0.0001303,0.0001473,0.00015030000000000002,0.0001595,0.00015780000000000001,0.0001789,0.00019610000000000002,0.0001974,0.000209,0.00021600000000000002,0.0002134,0.0002254,0.0002809,0.0002482,0.00024200000000000003,0.00024890000000000003,0.0002633,0.0002677,0.0002809,0.00028900000000000003,0.00030930000000000004,0.0003064,0.0003192,0.00032480000000000003,0.0003323,0.0003411,0.0003637,0.00036710000000000003,0.0003796,0.0005753,0.00039890000000000005,0.0004018,0.0004059,0.0004263,0.00044520000000000003,0.00045220000000000004,0.00046520000000000003,0.00047870000000000003,0.0004922,0.0005083,0.0005289,0.0005367,0.0005452,0.0005465,0.0015204,0.0005571,0.0005767000000000001,0.0006050000000000001,0.0006875000000000001,0.0006577,0.0006948000000000001,0.0006991,0.000711,0.0007118000000000001,0.0007492,0.0007545000000000001,0.0007618000000000001,0.0007786000000000001,0.0007801,0.0008219000000000001,0.0008190000000000001,0.0008486,0.0008751000000000001,0.0008993]
    _data_lin_kernighan = [0.0001017,0.00013758000000000002,0.00026988,0.00036490000000000003,0.0005146300000000001,0.0007108,0.0009627800000000001,0.00131383,0.0014377600000000002,0.0018070800000000002,0.0025650200000000003,0.0031454200000000003,0.0033789900000000006,0.0049346,0.0055303900000000005,0.007394490000000001,0.00829403,0.00941312,0.0039345000000000005,0.0041478,0.004743300000000001,0.0045415,0.0048947,0.0054383,0.0065658,0.0067648000000000005,0.006992300000000001,0.008744700000000001,0.007468700000000001,0.0090393,0.0112969,0.010661700000000001,0.015110900000000002,0.0130235,0.0140444,0.0169301,0.021728300000000002,0.029162,0.0338094,0.0345527,0.038339500000000006,0.0460657,0.0611041,0.0587053,0.0722793,0.0773292,0.0841214,0.09166010000000001,0.10660370000000001,0.11081780000000001,0.1218183,0.14642090000000002,0.1482165,0.18951980000000002,0.2029814,0.23812850000000002,0.24091410000000002,0.28944420000000004,0.3016151,0.3269696,0.35769650000000003,0.3435302,0.45921120000000004,0.5068758,0.20932910000000002,0.5504193000000001,0.5856132000000001,0.6330972,0.6425996,0.6871557,0.7721858,0.7866022,0.8199189,0.8599855000000001,0.9603877000000001,0.0089177,1.0469717,0.9971110000000001,1.2440345000000002,1.0307895,1.0849713,1.1504269,1.2012740000000002,1.2386941,0.36228160000000004,1.4069538000000001,1.3261769,1.4711739000000001,1.5595736,1.5790983,1.6374989000000002,1.1390892000000001,1.7154255,1.77176,1.8395085000000002,1.9003779,0.4290295,2.0640527]

    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
    _ax1.scatter([i+2 for i in range(len(_data_brute_force))], _data_brute_force, c='b', label="Brute force", marker='.')
    _ax1.scatter([i+2 for i in range(len(_data_branch_and_bound))], _data_branch_and_bound, c='r', label="Branch and bound", marker='.')
    _ax1.scatter([i+2 for i in range(len(_data_nearest_neighbour))], _data_nearest_neighbour, c='g', label="Nearest neighbour", marker='.')
    _ax1.scatter([i+2 for i in range(len(_data_lin_kernighan))], _data_lin_kernighan, c='orange', label="Lin-Kernighan", marker='.')
    _ax1.legend(loc="upper right")
    _ax1.set_yscale("log", base=10)

    _local_range = range(2, 7)
    _range_len = _local_range.stop-_local_range.start

    _ax2.scatter([i for i in _local_range], _data_brute_force[:_range_len], c='b', label="Brute force", marker='o')
    _ax2.scatter([i for i in _local_range], _data_branch_and_bound[:_range_len], c='r', label="Branch and bound", marker='o')
    _ax2.scatter([i for i in _local_range], _data_nearest_neighbour[:_range_len], c='g', label="Nearest neighbour", marker='o')
    _ax2.scatter([i for i in _local_range], _data_lin_kernighan[:_range_len], c='orange', label="Lin-Kernighan", marker='o')
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

    At $n = 5 = |S|$, which is what $|S|$ is in the problem, we can notice that Brute force runs faster than Branch and bound, and isn't much slower than Nearest neighbour. This is the reason why it will be used over those other more efficient approaches.
    <br><span style='color: silver;'>(as seen in right figure)</span>

    If $n$ was to increase, it will become impossible to consider Brute-force, and Branch-and-bound will only be usable with significant optimisations (discussed later). This can be seen in the left figure, with both these algorithms not being graphed after $n = 12$
    """)
    return


@app.cell
def _(plt):
    _data_brute_force_length = [86.8,153.9,164.9,217.7,230.8,291.7,307.6,364.0,378.3,401.0]
    _data_branch_and_bound_length = [86.8,153.9,164.9,217.7,230.8,291.7,307.6,364.0,378.3,401.0]
    _data_nearest_neighbour_length = [87.3,162.8,182.2,245.8,259.2,337.7,353.8,421.2,439.4,495.5,520.9,585.7,601.4,690.8,711.5,793.6,813.8,898.2,724.0,803.0,805.0,890.0,906.0,953.0,957.0,983.0,1002.0,1076.0,1102.0,1143.0,1165.0,1257.0,1265.0,1352.0,1378.0,1514.0,1554.0,1601.0,1659.0,1692.0,1730.0,1853.0,1879.0,1982.0,2024.0,2101.0,2097.0,2171.0,2319.0,2345.0,2361.0,2464.0,2466.0,2644.0,2652.0,2731.0,2733.0,2863.0,2873.0,3040.0,3056.0,3141.0,3163.0,3333.0,3335.0,3417.0,3421.0,3496.0,3554.0,3595.0,3723.0,3803.0,3831.0,3984.0,3990.0,4067.0,4139.0,4199.0,4261.0,4370.0,4386.0,4427.0,4489.0,4573.0,4583.0,4707.0,4719.0,4761.0,4863.0,4934.0,4968.0,5104.0,5110.0,5232.0,5234.0,5253.0,5255.0,5436.0]
    _data_lin_kernighan_length = [87.3,160.8,181.2,239.2,259.0,327.1,345.4,416.4,436.4,470.5,510.3,573.9,568.0,688.8,682.9,766.8,801.4,893.6,724.0,803.0,805.0,890.0,906.0,953.0,957.0,983.0,1002.0,1076.0,1102.0,1141.0,1143.0,1257.0,1265.0,1302.0,1378.0,1424.0,1554.0,1511.0,1569.0,1692.0,1700.0,1777.0,1817.0,1920.0,1962.0,2077.0,2097.0,2137.0,2247.0,2345.0,2283.0,2372.0,2466.0,2644.0,2652.0,2599.0,2601.0,2833.0,2843.0,2952.0,3056.0,3141.0,3163.0,3153.0,3327.0,3337.0,3249.0,3496.0,3516.0,3595.0,3681.0,3717.0,3831.0,3868.0,3990.0,3979.0,4139.0,4165.0,4137.0,4252.0,4386.0,4321.0,4383.0,4515.0,4477.0,4707.0,4715.0,4761.0,4863.0,4856.0,4968.0,5050.0,5058.0,5140.0,5234.0,5209.0,5255.0,5436.0]

    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(10, 6))
    _ax1.scatter([i+2 for i in range(len(_data_brute_force_length))], _data_brute_force_length, c='b', label="Brute force", marker='.')
    _ax1.scatter([i+2 for i in range(len(_data_branch_and_bound_length))], _data_branch_and_bound_length, c='r', label="Branch and bound", marker='.')
    _ax1.scatter([i+2 for i in range(len(_data_nearest_neighbour_length))], _data_nearest_neighbour_length, c='g', label="Nearest neighbour", marker='.')
    _ax1.scatter([i+2 for i in range(len(_data_lin_kernighan_length))], _data_lin_kernighan_length, c='orange', label="Lin-Kernighan", marker='.')
    _ax1.set_title("Different approaches' solution length")
    _ax1.legend(loc="upper right")
    _ax1.set_ylabel("Average Solution Length (units)")

    def _solution_gap(data) -> list[float]:
        return [100 * (data[i] - _data_branch_and_bound_length[i]) / _data_branch_and_bound_length[i] for i in range(min(len(_data_branch_and_bound_length), len(data)))]

    _ax2.scatter([i+2 for i in range(len(_data_brute_force_length))], _solution_gap(_data_brute_force_length), c='b', label="Brute force", marker='o')
    _ax2.scatter([i+2 for i in range(len(_data_branch_and_bound_length))], _solution_gap(_data_branch_and_bound_length), c='r', label="Branch and bound", marker='.')
    _ax2.scatter([i+2 for i in range(len(_data_branch_and_bound_length))], _solution_gap(_data_nearest_neighbour_length), c='g', label="Nearest neighbour", marker='o')
    _ax2.scatter([i+2 for i in range(len(_data_branch_and_bound_length))], _solution_gap(_data_nearest_neighbour_length), c='orange', label="Lin-Kernighan", marker='.')
    _ax2.set_title("Different approaches' optimality gap")
    _ax2.legend(loc="upper right")
    _ax2.set_ylabel("Average Solution Gap (%)")
    _ax2.set_xticks(range(len(_data_branch_and_bound_length) + 2))

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
    ## 3.2 Balancing Priorities
    """)
    return


@app.cell
def _():
    """add some animations for different goals cause it looks cool"""
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.3 Wing traversal strategy
    The algorithm will traverse between wings based on the best walk, not necessarily collecting each supply in a wing before moving to the next wing and often coming back to a wing previously traversed through. This was done to use a common path optimisation where directly travelling between two junctions in a wing, $j_1$ and $j_2$, may be slower than a path through $j_1$, $j_1'$, $j_2'$ and $j_2$, where $j_n'$ is the vertex a junction connects to via an interwing coridoor.

    Since we are still aiming for an exact algorithm that always outputs the optimal solution, we must allow for revisiting wings and partial collection of supplies.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3.4 Revised Algorithm
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3.4.1 Explanation
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
    ### 3.4.2 Algorithm Explorer
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
    These value **HIGHLY** depend on the marimo virtual machine, and can vary by up to 5 orders of magnitude. On my machine, I get Runtime: 2.72ms, Memory: 336 B
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
    Notes for Pseudocode:
    - RAISE is used when a function _may_ not return something, but that would occur only for an invalid input
    - syntax highlighting is weird but not much I can do about that...
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div style="font-family: monospace; font-size: 14px; white-space: pre-wrap;">PROCEDURE bfs(g: Graph, source: Vertex) -> Map[Vertex, Vertex]<br>&#9;dist <- map with ∞ FOR EACH vertex IN g.get_vertices(); dist[source] <- 0<br>&#9;visited <- ∅<br>&#9;prev <- empty map<br>&#9;stack <- [source]<br>&#9;<br>&#9;WHILE stack.size() > 0 DO<br>&#9;&#9;u <- stack.pop()<br>&#9;&#9;<br>&#9;&#9;IF u ∉ visited THEN<br>&#9;&#9;&#9;visited <- visited ∪ {u}<br>&#9;&#9;&#9;<br>&#9;&#9;&#9;FOR EACH v IN g.neighbours(u) DO<br>&#9;&#9;&#9;&#9;w <- g.get_edge_weight(u, v)<br>&#9;&#9;&#9;&#9;IF dist[u] + w < dist[v] THEN<br>&#9;&#9;&#9;&#9;&#9;prev[v] <- u<br>&#9;&#9;&#9;&#9;&#9;dist[v] <- dist[u] + w<br>&#9;&#9;&#9;&#9;&#9;stack.push(v)<br>&#9;&#9;&#9;&#9;END IF<br>&#9;&#9;&#9;END FOR<br>&#9;&#9;END IF<br>&#9;END WHILE<br>&#9;RETURN prev<br>END PROCEDURE<br><br>PROCEDURE get_path_from_bfs(source: Vertex, sink: Vertex, prev: Map[Vertex, Vertex]) -> List[Vertex]<br>&#9;left_path <- [source]<br>&#9;right_path <- [sink]<br>&#9;left <- source<br>&#9;right <- sink<br>&#9;<br>&#9;WHILE prev.has(left) OR prev.has(right) DO<br>&#9;&#9;IF prev.has(left) THEN<br>&#9;&#9;&#9;left <- prev[left]<br>&#9;&#9;&#9;left_path.push(left)<br>&#9;&#9;END IF<br>&#9;&#9;<br>&#9;&#9;IF prev.has(right) THEN<br>&#9;&#9;&#9;right <- prev[right]<br>&#9;&#9;&#9;right_path.push(right)<br>&#9;&#9;END IF<br>&#9;&#9;<br>&#9;&#9;FOR i <- 1 TO |left_path| DO<br>&#9;&#9;&#9;IF right = left_path[i] THEN<br>&#9;&#9;&#9;&#9;res <- []<br>&#9;&#9;&#9;&#9;FOR j <- 1 TO i DO<br>&#9;&#9;&#9;&#9;&#9;res.push(left_path[j])<br>&#9;&#9;&#9;&#9;END FOR<br>&#9;&#9;&#9;&#9;<br>&#9;&#9;&#9;&#9;FOR j <- 1 TO |right_path| DO<br>&#9;&#9;&#9;&#9;&#9;res.push(right_path[1 + |right_path| - j])<br>&#9;&#9;&#9;&#9;END FOR<br>&#9;&#9;&#9;&#9;RETURN res<br>&#9;&#9;&#9;END IF<br>&#9;&#9;END FOR<br>&#9;&#9;<br>&#9;&#9;FOR i <- 1 TO |right_path| DO<br>&#9;&#9;&#9;IF left = right_path[i] THEN<br>&#9;&#9;&#9;&#9;res <- []<br>&#9;&#9;&#9;&#9;FOR j <- 1 TO |left_path| DO<br>&#9;&#9;&#9;&#9;&#9;res.push(left_path[j])<br>&#9;&#9;&#9;&#9;END FOR<br>&#9;&#9;&#9;&#9;<br>&#9;&#9;&#9;&#9;FOR j <- 1 TO i DO<br>&#9;&#9;&#9;&#9;&#9;res.push(right_path[1 + i - j])<br>&#9;&#9;&#9;&#9;END FOR<br>&#9;&#9;&#9;&#9;RETURN res<br>&#9;&#9;&#9;END IF<br>&#9;&#9;END FOR<br>&#9;END WHILE<br>&#9;RAISE InputError<br>END PROCEDURE<br><br>PROCEDURE get_supplies_to_collect(supplies: Set[Vertex], vertex_to_supply_id: Map[Vertex, SupplyID], found_supply_ids: Set[SupplyID], supply_storage: Array[SupplyID, 5]) -> Set[Supply]<br>&#9;dont_collect_supply_ids <- found_supply_ids<br>&#9;FOR EACH supply IN supply_storage DO<br>&#9;&#9;dont_collect_supply_ids <- dont_collect_supply_ids ∪ {supply}<br>&#9;END FOR<br><br>&#9;res <- ∅<br>&#9;FOR EACH supply IN supplies DO<br>&#9;&#9;IF vertex_to_supply_id[supply] ∉ dont_collect_supply_ids THEN<br>&#9;&#9;&#9;res <- res ∪ {supply}<br>&#9;&#9;END IF<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE max(a: Integer, b: Integer) -> Integer<br>&#9;IF a > b THEN<br>&#9;&#9;RETURN a<br>&#9;END IF<br>&#9;RETURN b<br>END PROCEDURE<br><br>PROCEDURE get_path_length(g: Graph, path: List[Vertex]) -> Positive Integer or 0<br>&#9;res <- 0<br>&#9;FOR i <- 1 TO |path| - 1 DO<br>&#9;&#9;res <- res + g.get_edge_weight(path[i], path[i + 1])<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE reverse(list: List) -> List<br>&#9;res <- []<br>&#9;FOR i <- 1 TO |list| DO<br>&#9;&#9;res.push(list[1 + |list| - i])<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE reconstruct_path(prev: Map[Vertex, Vertex], sink: Vertex) -> List[Vertex]<br>&#9;res <- [sink]<br>&#9;WHILE prev.has(curr) DO<br>&#9;&#9;curr <- prev[curr]<br>&#9;&#9;res.push(curr)<br>&#9;END WHILE<br>&#9;RETURN reverse(res)<br>END PROCEDURE<br><br>PROCEDURE dijkstra(g: Graph, source: Vertex, sinks: Set[Vertex]) -> Map[Vertex, list[Vertex]]<br>&#9;res <- empty Map<br>&#9;dist <- map with ∞ FOR EACH vertex IN g.get_vertices(); dist[source] <- 0<br>&#9;prev <- empty map<br>&#9;<br>&#9;pq <- Priority Queue<br>&#9;FOR EACH vertex IN g.get_vertices() DO<br>&#9;&#9;pq.enqueue(vertex, dist[vertex])<br>&#9;END FOR<br>&#9;WHILE |pq| > 0 DO<br>&#9;&#9;u <- pq.extract_min()<br>&#9;&#9;<br>&#9;&#9;IF u ∈ sinks THEN<br>&#9;&#9;&#9;res[u] <- reconstruct_path(prev, u)<br>&#9;&#9;&#9;IF |res| = |sinks| THEN<br>&#9;&#9;&#9;&#9;RETURN res<br>&#9;&#9;&#9;END IF<br>&#9;&#9;END IF<br>&#9;&#9;<br>&#9;&#9;FOR EACH v IN g.neighbours(u) DO<br>&#9;&#9;&#9;w <- g.get_edge_weight(u, v)<br>&#9;&#9;&#9;IF dist[u] + w < dist[v] THEN<br>&#9;&#9;&#9;&#9;prev[v] <- u<br>&#9;&#9;&#9;&#9;dist[v] <- dist[u] + w<br>&#9;&#9;&#9;&#9;pq.update_priority(v, dist[v])<br>&#9;&#9;&#9;END IF<br>&#9;&#9;END FOR<br>&#9;END WHILE<br>&#9;RAISE InputError<br>END PROCEDURE<br><br>PROCEDURE get_path_matrix(g: Graph, entry: Vertex, exits: set[Vertex], supplies: set[Vertex]) -> Map[Vertex, Map[Vertex, List[Vertex]]]<br>&#9;res <- empty Map<br>&#9;FOR EACH source IN supplies ∪ {entry} DO<br>&#9;&#9;res[source] <- dijkstra(g, source, supplies ∪ exits)<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE get_path_cost_matrix(g: Graph, path_matrix: Map[Vertex, Map[Vertex, List[Vertex]]]) -> Map[Vertex, Map[Vertex, Positive Integer or 0]]<br>&#9;res <- empty Map<br>&#9;FOR EACH source IN path_matrix.keys() DO<br>&#9;&#9;res[source] <- empty Map<br>&#9;&#9;sink_paths <- path_matrix[source]<br>&#9;&#9;FOR EACH sink IN sink_paths.keys() DO<br>&#9;&#9;&#9;res[source][sink] <- get_path_length(g, path)<br>&#9;&#9;END FOR<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE brute_force_recursive(entry: Vertex, supplies: Set[Vertex], exits: Set[Vertex], path_cost_matrix: Map[Vertex, Map[Vertex, Positive Integer or 0]], fuel: Positive Integer or 0) -> Tuple[List[Vertex], Positive Integer or 0]<br>&#9;min_cost <- ∞<br>&#9;min_cost_path <- []<br>&#9;<br>&#9;IF fuel = 0 THEN<br>&#9;&#9;FOR EACH exit IN exits DO<br>&#9;&#9;&#9;cost <- path_cost_matrix[source][exit]<br>&#9;&#9;&#9;IF cost < min_cost THEN<br>&#9;&#9;&#9;&#9;min_cost <- cost<br>&#9;&#9;&#9;&#9;min_cost_path <- [sink]<br>&#9;&#9;&#9;END IF<br>&#9;&#9;END FOR<br>&#9;END IF<br>&#9;IF fuel != 0 THEN<br>&#9;&#9;FOR EACH sink IN sinks DO<br>&#9;&#9;&#9;recursive_res <- brute_force_recursive(sink, sinks \ {sink}, exits, path_cost_matrix, fuel - 1)<br>&#9;&#9;&#9;min_path_through <- recursive_res[0]<br>&#9;&#9;&#9;cost <- recursive_res[1]<br>&#9;&#9;&#9;cost <- cost + path_cost_matrix[source][sink]<br>&#9;&#9;&#9;IF cost < min_cost THEN <br>&#9;&#9;&#9;&#9;min_cost <- cost<br>&#9;&#9;&#9;&#9;min_cost_path <- [sink]<br>&#9;&#9;&#9;&#9;FOR vertex IN min_path_through DO<br>&#9;&#9;&#9;&#9;&#9;min_cost_path.push(vertex)<br>&#9;&#9;&#9;&#9;END FOR<br>&#9;&#9;&#9;END IF<br>&#9;&#9;END FOR<br>&#9;END IF<br>&#9;RETURN (min_cost_walk, min_cost)<br>END PROCEDURE<br><br>PROCEDURE brute_force(entry: Vertex, supplies: Set[Vertex], exits: Set[Vertex], path_cost_matrix: Map[Vertex, Map[Vertex, Positive Integer or 0]], fuel: Positive Integer or 0) -> List[Vertex]<br>&#9;path <- brute_force_recursive(entry, supplies, exits, path_cost_matrix, fuel)[0]<br><br>&#9;res <- [entry]<br>&#9;FOR EACH vertex IN path DO<br>&#9;&#9;res.push(path)<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE get_F_path_from_H_path(H_path: List[Vertex], path_matrix: Map[Vertex, Map[Vertex, List[Vertex]]]) -> List[Vertex]<br>&#9;res <- []<br>&#9;FOR i <- 1 TO |H_path| - 1 DO<br>&#9;&#9;path <- path_matrix[H_path[i]][H_path[i + 1]]<br>&#9;&#9;FOR j <- 1 TO |path| - 1 DO<br>&#9;&#9;&#9;res.push(path[j])<br>&#9;&#9;END FOR<br>&#9;END FOR<br>&#9;res.push(H_path[|H_path|])<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE get_which_wing(G: Tuple[Set[Graph], Set[Tuple[Vertex, Vertex]]], vertex: Vertex) -> Graph<br>&#9;FOR EACH wing IN G[0] DO<br>&#9;&#9;IF vertex IN g.get_vertices() THEN<br>&#9;&#9;&#9;RETURN g<br>&#9;&#9;END IF<br>&#9;END FOR<br>&#9;RAISE InputError<br>END PROCEDURE<br><br>PROCEDURE get_G_path_from_F_path(G: Tuple[Set[Graph], Set[Tuple[Vertex, Vertex]]], F_path: List[Vertex], prevs: Map[Graph, Map[VertexT, VertexT]]) -> List[Vertex]<br>&#9;res <- []<br>&#9;FOR i <- 1 TO |F_path| - 1 DO<br>&#9;&#9;u <- F_path[i]<br>&#9;&#9;v <- F_path[i + 1]<br>&#9;&#9;u_wing <- get_which_wing(G, u)<br>&#9;&#9;v_wing <- get_which_wing(G, v)<br>&#9;&#9;IF u_wing = v_wing THEN<br>&#9;&#9;&#9;path <- get_path_from_bfs(u, v, prevs[u_wing])<br>&#9;&#9;&#9;FOR j <- 1 TO |path| - 1 DO<br>&#9;&#9;&#9;&#9;res.push(path[j])<br>&#9;&#9;&#9;END FOR<br>&#9;&#9;END IF<br>&#9;&#9;IF u_wing != v_wing THEN<br>&#9;&#9;&#9;res.push(u)<br>&#9;&#9;END IF<br>&#9;END FOR<br>&#9;res.push(F_path[|F_path|])<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE get_F(G: Tuple[Set[Graph], Set[Tuple[Vertex, Vertex]]], entry: Vertex, supplies: Set[Vertex], exits: Set[Vertex], prevs: Map[Vertex, Vertex]) -> Graph<br>&#9;res <- empty Graph<br>&#9;FOR EACH v IN {entry} ∪ supplies ∪ exits DO<br>&#9;&#9;res.add_vertex(v)<br>&#9;END FOR<br>&#9;<br>&#9;junction_vertices <- ∅<br>&#9;FOR EACH e IN G[1] DO<br>&#9;&#9;res.add_vertex(e[0])<br>&#9;&#9;res.add_vertex(e[1])<br>&#9;&#9;res.add_edge(e[0], e[1], 1)<br>&#9;&#9;<br>&#9;&#9;junction_vertices <- junction_vertices ∪ {e[0]}<br>&#9;&#9;junction_vertices <- junction_vertices ∪ {e[1]}<br>&#9;END FOR<br>&#9;<br>&#9;FOR EACH wing IN G[0] DO<br>&#9;&#9;salient_vertices <- []<br>&#9;&#9;FOR EACH v IN ({entry} ∩ wing.get_vertices()) ∪ (supplies ∩ wing.get_vertices()) ∪ (exits ∩ wing.get_vertices()) ∪ (junction_vertices ∩ wing.get_vertices()) DO<br>&#9;&#9;&#9;salient_vertices.push(v)<br>&#9;&#9;END FOR<br>&#9;&#9;<br>&#9;&#9;FOR i <- 1 TO |salient_vertices| DO<br>&#9;&#9;&#9;FOR j <- i + 1 TO |salient_vertices| DO<br>&#9;&#9;&#9;&#9;u <- salient_vertices[i]<br>&#9;&#9;&#9;&#9;v <- salient_vertices[i + 1]<br>&#9;&#9;&#9;&#9;<br>&#9;&#9;&#9;&#9;path <- get_path_from_bfs(u, v, prevs[wing])<br>&#9;&#9;&#9;&#9;weight <- get_path_length(wing, path)<br>&#9;&#9;&#9;&#9;<br>&#9;&#9;&#9;&#9;res.add_edge(u, v, weight)<br>&#9;&#9;&#9;END FOR<br>&#9;&#9;END FOR<br>&#9;END FOR<br>&#9;RETURN res<br>END PROCEDURE<br><br>PROCEDURE get_new_supply_storage(supply_storage: Array[SupplyID, 5], vertex_to_supply_id: Map[Vertex, SupplyID], num_of_supplies_to_collect: Positive Integer, H_path: List[VertexT]) -> Array[SupplyID, 5]<br>&#9;collected_supplies <- []<br>&#9;FOR EACH v IN H_path DO<br>&#9;&#9;IF v ∈ uncollected_supplies THEN<br>&#9;&#9;&#9;collected_supplies.push(v)<br>&#9;&#9;END IF<br>&#9;END FOR<br>&#9;<br>&#9;supply_idx <- 1<br>&#9;supply_storage_idx <- 1<br>&#9;WHILE supply_storage_idx <= |supply_storage| AND supply_idx <= num_of_supplies_to_collect DO<br>&#9;&#9;IF supply_storage[supply_storage_idx] = NULL THEN<br>&#9;&#9;&#9;supply_storage[supply_storage_idx] <- vertex_to_supply_id[collected_supplies[supply_idx]]<br>&#9;&#9;&#9;supply_idx <- supply_idx + 1<br>&#9;&#9;END IF<br>&#9;END WHILE<br>&#9;RETURN supply_storage<br>END PROCEDURE<br><br>FUNCTION ember_rescue(G: Tuple[Set[Graph], Set[Tuple[Vertex, Vertex]]], entry: Vertex, exits: Set[Vertex], supplies: Set[Vertex], exits: Set[Vertex], supply_storage: Array[SupplyID, 5], vertex_to_supply_id: Map[Vertex, SupplyID], found_supply_ids: Set[SupplyID]) -> Tuple[List[Vertex], Array[Supply, 5]]<br>&#9;uncollected_supplies <- get_supplies_to_collect(supplies, vertex_to_supply_id, found_supply_ids, supply_storage)<br>&#9;<br>&#9;num_of_supplies_to_collect <- 0<br>&#9;FOR EACH id IN supply_storage DO<br>&#9;&#9;IF id isn't the null id THEN<br>&#9;&#9;&#9;num_of_supplies_to_collect <- num_of_supplies_to_collect + 1<br>&#9;&#9;END IF<br>&#9;END FOR<br>&#9;num_of_supplies_to_collect <- max(num_of_supplies_to_collect, |supplies|)<br>&#9;<br>&#9;prevs <- empty map<br>&#9;FOR EACH wing IN G[0] DO<br>&#9;&#9;IF |wing.get_vertices()| > 0 THEN<br>&#9;&#9;&#9;prevs[wing] <- bfs(wing, a vertex in wing)<br>&#9;&#9;END IF<br>&#9;END FOR<br>&#9;<br>&#9;F = get_F(G, entry, supplies, exits, prevs)<br><br>&#9;path_matrix <- get_path_matrix(F, entry, exits, uncollected_supplies)<br>&#9;<br>&#9;path_cost_matrix <- get_path_cost_matrix(F, path_matrix)<br>&#9;<br>&#9;H_path <- brute_force(entry, supplies, exits, path_cost_matrix, num_of_supplies_to_collect)<br>&#9;<br>&#9;F_path <- get_F_path_from_H_path(H_path, path_matrix)<br>&#9;<br>&#9;G_path <- get_G_path_from_F_path(G, F_path, prevs)<br>&#9;<br>&#9;new_supply_storage <- get_new_supply_storage(supply_storage, vertex_to_supply_id, num_of_supplies_to_collect, H_path)<br>&#9;RETURN G_path, supply_storage<br>END FUNCTION</div>
    """)
    return


@app.cell
def _():
    """python code"""
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
    - Each wing is connected, allows only 1 depth first search to be run on each wing. Without this assumption, we would need to run it starting from each supply, entry, exit and junction in each wing, drastically reducing the time and space efficiency of the algorithm which would also need to store each `prev` Map
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
    - Talk about the making the algorithm without assuming the size of the facility is just what we have right now
    """)
    return


if __name__ == "__main__":
    app.run()
