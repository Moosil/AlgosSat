import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium", app_title="Memo1", css_file="../custom.css")


@app.cell
def _():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import copy

    return mo, mpatches, nx, plt, random


@app.cell(hide_code=True)
def _(mpatches, nx, plt, random, seed_input):
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
            _GAP = 3  # grid-unit gap between wings in the visualisation

            total_w = self.n_wings * self.WING_COLS + (self.n_wings - 1) * _GAP

            fig_w = max(10., total_w * 0.58)
            fig_h = max(5., self.WING_ROWS * 0.58 + 1.2)
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
    # 1 Introduction
    We have been tasked to design a **decision architecture** for a robot. To do this, we will create a abstraction for this problem, and subsequently an algorithm to solve it.
    
    We will first abstract this problem, discuss and evaluate multiple approaches, before outlining the final chosen approach.
    
    After which, the algorithm will be implemented in python and run on multiple facilities, we will rigorously prove its correctness and completeness and visualise the running of the algorithm on a representation of the facility.
    ## 1.1 Limitations of Previous Model
    The previous model assumed the facility was just the one wing
    #todo
    ## 1.2 Amendment Revisions
    #todo
    # 2 Abstraction
    Let $G = (V_w, E_w, w)$ be a super-graph, with $V_w=\{W_1, W_2, \dots, W_k\}$ being a set of undirected weighted graphs, $E_w \subseteq \{\{u, v\} \vert u \in V_n, v \in V_m, n \neq m\}$ being a set of edges between adjacent wings, $W_n, W_m$ of the facility, with $k$ being the number of wings in the facility, and $\forall n \leq k, W_n = (V_n, E_n)$.
    
    $V = V_1 \cup V_2 \cup \dots \cup V_k$ and $\forall n, m \leq k, V_n \cap V_m = \varnothing \iff n \neq m$ and $V_n = V_m \iff n = m$, with $V$ representing the salient sectors of the facility $E = E_1 \cup E_2 \cup \dots \cup E_k$ and $\forall n, m \leq k, E_n \cap E_m = \varnothing \iff n \neq m$ and $E_n = E_m \iff n = m$, with $E$ representing the paths between those adjacent salient sectors, and positive integer edge weight function $w: E \cup E_w \to \mathbb{N}$ representing the spans of sectors between two salient sectors which are adjacent to just two other sectors. If $(u, v) \notin E$, define $w(u, v) = \infty$.
    
    We will designate source vertex $s \in V$, the set of sink vertices $X \subseteq V$, and the set of prize vertices $S \subseteq V$, each representing the entry, exit, and supply unit-containing sectors respectively.
    
    We will have $A$ be an array of size 5 representing CRUDY-1's supply unit storage, which contains `SupplyID`s or the null ID: 0, function $M: S \to \text{SupplyID}$ mapping each supply vertex to its `SupplyID`, and set $F$ be the set of found `SupplyID`s. When a supply is collected, it will be added to $A$, and $A_\text{new}$ will be returned.
    
    We will be designing an algorithm to traverse super-graph $G$, from $s$ to an $x$, returning an ordered sequence of vertices in list $W$, and CRUDY-1's updated supply unit storage.
    ## 2.1 Inputs & Outputs
    The specificities of the inputs and outputs are above, and both concise lists are below:
    ### 2.1.1 Inputs
    1. $G$
    2. $s$
    3. $X$
    4. $S$
    5. $A$
    6. $M$
    7. $F$
    ### 2.1.2 Outputs
    1. $W$
    2. $A_\text{new}$
    ## 2.2 Output Constraints
    The algorithm should output an ordered sequence of vertices $(v_1, v_2, \dots, v_n)$, with $\forall m < n, v_m \in V \cup V_w$, $v_1 = s$, and $v_n \in X$. It should aim to collect as many prize vertices as possible.
    
    $\forall i \leq \text{length}(A), A_\text{new}[i] \neq A[i] \implies A[i] = \varnothing$ and $A[i] \neq \varnothing \iff A_\text{new} = A[i]$
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
    
    ## 2.3 Salient Features
    Decisions made for how much abstraction is done on certain properties of the problem are guided by maintaining correctness, completeness, and allowing for an appropriate run-time given the size of each variable in the current problem. In particular, finding an exact solution requires searching through a portion of the solution space, and thus we have an at most exponential growth in $O(b^d)$. Reducing $b$ and $d$ allow for further depth and will allow the algorithm to run faster, allow for exact algorithms/better heuristic upper-bounds, and allow for this algorithm to be considered on larger facilities.
    
    By representing the facility as a hierarchical graph, we can use strategies to reduce the depth of the combinatorial explosion of algorithms that can be used to assist with the objective. Instead of $O(b^d)$ exploding with $d = |E|$, we can instead have it increase with $d = |V_w|$ instead. We have each wing be a vertex on $G$, and each junction and inter-wing corridor.
    
    We choose to abstract individual sectors of the facility, opting to instead represent a subset of salient sectors to be on any wing graph $W_n$, abstracting the sectors on the paths between these salient sectors as edge weight through the function $w$.
    
    These salient sectors are sectors adjacent to 1, 3 or 4 other sectors, and sectors containing supply units, entrances, junctions or exits. Without any one of these, we do not fully capture each wing of the facility in our abstraction.
    
    CRUDY-1's limited supply storage is represented by $A$, with $F$ being already collected supplies <span>&ndash;</span> CRUDY-1 does not need to collect these supplies <span>&ndash;</span> and $M$ finding the `SupplyID` of a particular supply vertex.
    # 2.4 Hierarchical vs Flat graph
    #todo
    %%graph of time to complete of different sizes%%
    ## 2.5 Justification of Each ADT
    #todo
    # 3 Algorithm Design
    ## 3.1 Algorithmic Design approaches
    #todo
    %%add some animations for each approach cause it looks cool%%
    ## 3.2 Balancing Priorities
    #todo
    %%add some animations for different goals cause it looks cool%%
    ## 3.3 Wing traversal strategy
    ### 3.3.1 Sub-problems
    #todo
    ### 3.3.2 Two strategies
    #todo
    %%graph of time of each%%
    ## 3.4 Revised Algorithm
    ### 3.4.1 Explanation
    #todo
    ### 3.4.2 Justification
    #todo
    
    %%ANIMATION%%
    # 4 Pseudocode
    %%This time I'm going to do each function separately and explain what it does%%
    #todo
    # 5 Justification
    ## 5.1 Suitability
    #todo
    ## 5.2 Coherence
    #todo
    ## 5.3 Fit for Purpose
    #todo
    %%Talk about the making the algorithm without assuming the size of the facility is just what we have right now%%
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Algorithm Explorer
    """)
    return


@app.cell(hide_code=True)
def algorithm_explorer(facility_drawer):
    facility_drawer.draw_multi_wing()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Justification

    ### Suitability
    - The number of supplies in the facility is low, and the number of verticies is much higher. This suits the time complexity scaling well with number of verticies and badly with number of supplies
    - The facilities size: 12x12 sectors means that max number of vertices in abstraction is 144 and this small size favours an algorithm that is easier to implement
    - Since the algorithm always finds the shortest route that collects all supplies to an exit, an edge case would be the seed that gives the worst facility for the algorithm
    - The algorithm was implemented in python and has an average runtime of 100 milliseconds, which allows CRUDY-1 to
    - Assumptions removed that will cause need for changes:
      - Facility isn't full connected
      - Facility sector adjacency becomes directed and $G$ isn't a fully connected component
      - Supply units have weight and CRUDY-1 should avoid carrying too many
      - Supply units have non-uniform weight
      - Facility isn't fully known when algorithm starts
      - More than 5 supplies (algorithm time grows quickly with supplies)
      - More drones
      - Sectors that break when you go through them (CRUDY-1 cannot revisit)
      - Many other things

    ### Coherance
    - I use $\text{get\_neighbours}: \text{Graph} \times \text{Vertex} \to \text{Vertex}$ in the dijkstra's algorithm implementation in the algorithm to get the neighbours of the current visited vertex
    - I use $\text{has}: \text{Map} \times \text{Key} \to \text{Boolean}$ to reconstruct the shortest paths found by dijkstra's algorithm
    - My pseudocode prefers square bracket notation to the ADT $\text{get}$ operation in Map and Array

    ### Operational Constraints
    - Load capacity: $A$ holds the supplies that CRUDY-1 currently holds
    - Extraction: The algorithm always terminates at an exit (proved below)
    - Energy budget: The algorithm always finds a minimum cost walk through the facility that collects all supplies and exits at an exit
    - Revisiting sectors: N/A (not a constraint)
    - Supply collection: $\text{get\_unfound\_supplies}: \text{Set}[\text{Vertex}] \times \{\text{Vertex} \to \text{String or NULL}\} \times Set[String] \to \text{Set}[\text{Vertex}]$ makes sure CRUDY-1 ignores already collected supplies
    - Objective: All supplies will be collected (proved below) and there are no energy constraints
    - Mission Directive:
      - The algorithm does not care about structural stability, as it will cross over a sector at most 3 times (proved below)
      - The algorithm will always have a successful extraction if one exists.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Proofs (barely)

    ### Tractablilibity

    The algorithm checked on a subset of 85000 facilities was correct for all such facilities

    ### Optimality

    Since the algorithm finds the shortest distance between each entry, supply and exit, and it the checks each ordering of entry to each supply to an exit, the walk found must be the shortest path
    """)
    return


if __name__ == "__main__":
    app.run()
