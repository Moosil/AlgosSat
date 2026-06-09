import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    return mo, mpatches, nx, plt, random


@app.cell
def _(mpatches, nx, plt, random, seed_input):
    class GraphDrawer:
        def _neighbours(self, cols, rows, c, r):
            for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                nc, nr = c+dc, r+dr
                if 0 <= nc < cols and 0 <= nr < rows:
                    yield nc, nr

        def _build_graph(self, cols, rows, rng):
            visited = [[False] * rows for _ in range(cols)]
            graph = nx.Graph()
            for c in range(cols):
                for r in range(rows):
                    graph.add_node((c, r), pos=(c + 0.5, r + 0.5))
    
            def carve(c, r):
                visited[c][r] = True
                dirs = list(self._neighbours(cols, rows, c, r))
                rng.shuffle(dirs)
                for nc, nr in dirs:
                    if not visited[nc][nr]:
                        graph.add_edge((c, r), (nc, nr), weight=1)
                        carve(nc, nr)
    
            carve(0, 0)
            for c in range(cols):
                for r in range(rows):
                    if not visited[c][r]:
                        for nc, nr in _neighbours(cols, rows, c, r):
                            if visited[nc][nr]:
                                graph.add_edge((c, r), (nc, nr), weight=1)
                                carve(c, r)
                                break
            return graph

        def _place_supplies(self, graph, cols, rows, rng, reserved):
            dead_ends = [n for n in graph.nodes
                         if graph.degree(n) == 1 and n not in reserved]
            rng.shuffle(dead_ends)
            quadrants = [
                (0, cols//2, 0, rows//2),
                (cols//2, cols, 0, rows//2),
                (0, cols//2, rows//2, rows),
                (cols//2, cols, rows//2, rows),
            ]
            result, used = [], set(reserved)
            for qc1, qc2, qr1, qr2 in quadrants:
                if len(result) >= 5:
                    break
                cands = [n for n in dead_ends
                         if qc1 <= n[0] < qc2 and qr1 <= n[1] < qr2
                         and n not in used]
                if cands:
                    result.append(cands[0])
                    used.add(cands[0])
            for n in dead_ends:
                if len(result) >= 5:
                    break
                if n not in used:
                    result.append(n)
                    used.add(n)
            return result[:5]

        def _get_facility(self, seed):
            COLS, ROWS = 12, 12
            rng = random.Random(int(seed))
            graph = self._build_graph(COLS, ROWS, rng)
            entry  = (0, 0)
            exit_a = (COLS-1, ROWS-1)
            exit_b = (COLS-1, 0)
            reserved = {entry, exit_a, exit_b}
            rng2 = random.Random(int(seed))
            supplies = self._place_supplies(graph, COLS, ROWS, rng2, reserved)
            return graph, entry, exit_a, exit_b, supplies
    
        def _draw_facility(self, graph, entry, exit_a, exit_b, supplies,
                      highlight_path=None, title="Facility Layout",
                      node_colors=None, supply_collected=None,
                      figsize=(8, 8)):
            COLS, ROWS = 12, 12
            COL_BG       = '#F5F7FA'
            COL_GRID     = '#C8D0DC'
            COL_WALL     = '#44546A'
            COL_ENTRY    = '#0B6E6B'
            COL_EXIT     = '#7A1E2C'
            COL_SUPPLY   = '#4AA8A0'
            COL_PATH     = '#0B6E6B'
            COL_VISITED  = '#B8D8D7'
            COL_FRONTIER = '#F4C97A'
            COL_CURRENT  = '#E8603C'
    
            fig, ax = plt.subplots(figsize=figsize)
            ax.set_facecolor(COL_BG)
            fig.patch.set_facecolor(COL_BG)
    
            # Grid
            for c in range(COLS + 1):
                ax.plot([c, c], [0, ROWS], color=COL_GRID, lw=0.4, zorder=1)
            for r in range(ROWS + 1):
                ax.plot([0, COLS], [r, r], color=COL_GRID, lw=0.4, zorder=1)
    
            # Border
            for x0,y0,x1,y1 in [(0,0,COLS,0),(COLS,0,COLS,ROWS),(COLS,ROWS,0,ROWS),(0,ROWS,0,0)]:
                ax.plot([x0,x1],[y0,y1], color=COL_WALL, lw=2.2, zorder=3)
    
            # Internal walls
            for c in range(COLS):
                for r in range(ROWS):
                    if c+1 < COLS and not graph.has_edge((c,r),(c+1,r)):
                        ax.plot([c+1,c+1],[r,r+1], color=COL_WALL, lw=1.6, zorder=3)
                    if r+1 < ROWS and not graph.has_edge((c,r),(c,r+1)):
                        ax.plot([c,c+1],[r+1,r+1], color=COL_WALL, lw=1.6, zorder=3)
    
            # Highlighted nodes
            if node_colors:
                for node, color in node_colors.items():
                    c, r = node
                    rect = plt.Rectangle((c, r), 1, 1, color=color, alpha=0.50, zorder=2)
                    ax.add_patch(rect)
    
            # Solution path
            if highlight_path and len(highlight_path) > 1:
                px = [c + 0.5 for c,r in highlight_path]
                py = [r + 0.5 for c,r in highlight_path]
                ax.plot(px, py, color=COL_PATH, lw=1.8, linestyle='--', alpha=0.75, zorder=4)

            # Supply markers
            for i, (sc, sr) in enumerate(supplies):
                already = supply_collected and (sc, sr) in supply_collected
                col = '#AAAAAA' if already else COL_SUPPLY
                mkr = 'x'      if already else '*'
                ax.plot(sc+0.5, sr+0.5, marker=mkr, markersize=14, color=col,
                        markeredgecolor=COL_ENTRY if not already else '#999',
                        markeredgewidth=0.8, zorder=5)
                ax.text(sc+0.62, sr+0.58, f'S{i+1}', fontsize=6, color=COL_WALL, zorder=6)
    
            # Entry circle
            ec, er = entry
            ax.add_patch(plt.Circle((ec+0.5,er+0.5), 0.22, color=COL_ENTRY, zorder=6))
            ax.text(ec+0.5, er+0.5, 'E', ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=7)
    
            # Exit circles
            for lbl, node in [('A', exit_a), ('B', exit_b)]:
                xc, xr = node
                ax.add_patch(plt.Circle((xc+0.5,xr+0.5), 0.22, color=COL_EXIT, zorder=6))
                ax.text(xc+0.5, xr+0.5, lbl, ha='center', va='center',
                        fontsize=6, color='white', fontweight='bold', zorder=7)

            legend_items = [
                mpatches.Patch(color=COL_ENTRY,  label='Entry'),
                mpatches.Patch(color=COL_EXIT,   label='Exit A / B'),
                mpatches.Patch(color=COL_SUPPLY, label='Supply unit'),
            ]
            if node_colors:
                legend_items += [
                    mpatches.Patch(color=COL_VISITED,  alpha=0.5, label='Visited'),
                    mpatches.Patch(color=COL_FRONTIER, alpha=0.5, label='Frontier'),
                    mpatches.Patch(color=COL_CURRENT,  alpha=0.7, label='Current'),
                ]
            ax.legend(handles=legend_items, loc='upper left', fontsize=8, framealpha=0.9)
            ax.set_xlim(0, COLS); ax.set_ylim(0, ROWS)
            ax.set_aspect('equal'); ax.axis('off')
            ax.set_title(title, fontsize=11, fontweight='bold', color='#0B1F3B', pad=10)
            plt.tight_layout()
            return fig

        def draw_facility(self, seed, highlight_path=None, title="Facility Layout",
                          node_colors=None,  supply_collected=None,figsize=(8, 8)):
            _graph, _entry, _exit_a, _exit_b, _supplies = self._get_facility(seed_input.value)
            return self._draw_facility(_graph, _entry, _exit_a, _exit_b, _supplies)

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
    # Memo 1

    ## Defintions
    - **The ESRC**: the Emberlight Subterranean Research Complex
    - **Dead-end**: a sector adjacent to exactly 1 other sector
    - **Corridor**: a sector adjacent to exactly 2 other sectors
    - **Junction**: a sector adjacent to exactly 3 other sectors
    - **Crossroad**: a sector adjacent to exactly 4 other sectors
    - **Physical walk**: a walk CRUDY-1 could between two sectors. A physical walk does exist between all sectors in the facility (currently)
    -  **Salient sector**: a sector which is a junction, crossroad, supply unit, entry or exit, justified in **Action 2**.
    - **Tunnel**: a series of adjacent, **non-salient** **corridors** which connect two **salient sectors**

    ## Assumptions
    - CRUDY-1 knowns the current facility layout immediately upon entering it
    - CRUDY-1 can travel between adjacent sectors without turning
    - The facility is acyclic
    - The length of the walk CRUDY-1 does through the facility to go to the exit should be minimised
    - The time taken to find said walk should be minimised
    - Each supply has a unique identifier that can be represented as a non-empty string
    - There may be more than one of the same supply unit in the **ESRC**.
    - There are only 5 supplies in the facility
    - facility is full connected and contains no cycles (it is a tree)
    - the sectors in the facility connect in two directions
    - CRUDY-1 starts with 0 supplies in its storage

    ## ADT Operations

    ### Graph
    - $\text{add\_vertex}: \text{Graph} \times \text{Vertex} \to \text{Graph}$
    - $\text{add\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \times \mathbb{R}^+ \cup \{0\} \to \text{Graph}$
    - $\text{remove\_vertex}: \text{Graph} \times \text{Vertex} \to \text{Graph}$
    - $\text{remove\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \to \text{Graph}$
    - $\text{get\_neighbours}: \text{Graph} \times \text{Vertex} \to \text{Set}[\text{Vertex}]$
    - $\text{has\_edge}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \to \text{Boolean}$
    - $\text{get\_vertices}: \text{Graph} \to \text{Set}[\text{Vertex}]$
    - $\text{set\_edge\_weight}: \text{Graph} \times \text{Vertex} \times \text{Vertex} \times \mathbb{R}^+ \cup \{0\} \to \text{Graph}$
    - $\text{get\_edge\_weight}: \text{Graph} \times \text{Vertex} \times \text{Vertex}) \to \mathbb{R}^+ \cup \{0\}$

    ### Set
    - $\text{union}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{difference}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{intersection}: \text{Set} \times \text{Set} \to \text{Set}$
    - $\text{size}: \text{Set} \to \mathbb{R}^+ \cup \{0\}$
    - $\text{element\_of}: \text{Set} \times \text{Item} \to \text{boolean}$
    - $\text{subset\_of}: \text{Set} \times \text{Set} \to \text{boolean}$
    - $\text{are\_equal}: \text{Set} \times \text{Set} \to \text{boolean}$

    ### Map
    - $\text{size}: \text{Map} \to \mathbb{R}^+ \cup \{0\}$
    - $\text{has}: \text{Map} \times \text{Key} \to \text{boolean}$
    - $\text{at}: \text{Map} \times \text{Key} \to \text{Value}$
    - $\text{remove}: \text{Map} \times \text{Key} \to \text{Map}$
    - $\text{set}: \text{Map} \times \text{Key} \times \text{Value} \to \text{Map}$

    ### List
    - $\text{push}: \text{List} \times \text{Item} \to \text{List}$
    - $\text{pop}: \text{List} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{is\_empty}: \text{List} \to \text{Boolean}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ## Algorithm

    ### Worded defintion
    Given Graph $G = (V, E, w)$, vertex $v_e \in V$, Set of vertices $V_x \subseteq V$, Set of vertices $V_s \subseteq V$, Map $M_s: V \to \text{string or null}$, and Set $S$, return $W$

    ### Signature specification
    $G \times v_e \times V_x \times V_s \times M_s \times S \to W$

    ### Output Constraints

    $W$ is a list of vertices, where the first element is $v_e$ and the last element $\in V_x$ and the elements inbetween form a path through the graph where an edge in $G$ exists between each element of $W$ and the one following it.

    ### Parameter Justifications

    #### $G$
    $G$ represents the facility layout, encapsulating only the salient features of it.

    A graph allows a minimal abstraction, where other ADTs would introduce non-salient parts of the problem.

    The set of vertices $V$ abstracts the **salient sectors**

    The set of edges $E \subseteq \{\{u,v\} \mid u,v \in V, u \neq v\}$ abstracts the sector paths between **salient sectors**

    The weight function $w: V \times V \to \mathbb{R}^+ \cup \{0\}$ abstract long stretches of coridoor sectors. The weight function $w: \text{Vertex}

    #### $v_e$
    $v_e$ represents the entry vertex, where the algorithm should start and the first element of $W$

    #### $V_x$
    $V_x$ represents the exit vertices, where the algorithm can terminate and one vertex in $V_x$ must be the last element of $W$

    A set allows for checks against membership and other set operations compatible with the vertex set of $G$

    #### $V_s$

    $V_x$ represents the supply vertices, where a supply exists in the sector represented by the vertex. The algorithm should pass through as many of these vertices as possible in walk $W$

    A set allows for checks against membership and other set operations compatible with the vertex set of $G$

    #### $M_s$

    Map $M_s$ returns the uid of the supply at a vertex or null if no supply exists there.

    A map allows for key-value lookup, which allows mapping of each vertex to a string

    #### $S$

    What does it model?
    Set $S$ models all previously collected supply units as they may only collected once

    A set allows for fast checking of containing, which is important because CRUDY-1 must quickly evaluate if a supply unit should be collected (or if it has already previously been collected).

    #### $W$

    List $W$ abstracts valid movement on the facility, and is a walk on $G$

    Since $W$ models a sequence, it must be ordered. The size of $W$ is not constant, so an Array would not be applicable. There are no other properties to be satisfied, so a list was chosen.

    ## Abstraction of the problem

    ### Salient features
    - **Junctions** and **crossroads** in the facility. Each represent a decision point. These are modelled as vertices in $G$
    - Entry and exit points. The entry point represents where CRUDY-1 starts and exit points represent where it must end. These are modelled as vertices in $G$.
    ### Non-salient features
    - **Dead-ends**  and **corridors** without supply units in the facility. **Dead-ends** will never be traversed to as they cannot lead to exits or supply units, which are the only two sectors CRUDY-1 has a need to traverse. **Tunnels** connect two **salient sectors**, and can be thus modelled with the weight map $w$, increasing the cost of traversing the edge between those two **salient sectors**. Abstracting away tunnels reduces all non-salient **corridors**
    - As CRUDY-1 traverses the facility, its position is not stored as the facility layout is known and will not change due to the structural stability
    - CRUDY-1’s initial position is not stored as it is known to be the entry sector, of which only one is present
    - Physical mass of each supply units are uniform, thus only the amount of these same-weight supply units must be considered.
    - The actual traversal steps, as how CRUDY-1 traverses the facility is outside the abstraction

    ## Implementation

    ### Uniqueness of paths
    We assume the facility is *acyclic* and *fully connected*. Since we also assume the it is also undirected, the graph $G$ is a tree and thus a minimum spanning tree. Therefore every path between two vertices in $G$ is a minimum-cost path.

    ### Uniqueness of facilities
    Two facilities may have the their $G$ isomorphic, even if they have completely different layouts.

    ### Adjacency List vs Matrix
    With the current facilities size:
    - $|E| = |V| - 1$ due to the tree representation
    - Adjacency list: $2|E| = 2|V| - 1$ entries
    - Adjacency matrix: $|V|^2$ entries

    For this facility, an adjacency list would be more compact

    ### NetworkX signature specifications → Python[^3]
    - `Graph.add_node(node_for_adding, **attr)` is an operation synonymous of the `add_vertex` function
    - `Graph.add_edge(u_of_edge, v_of_edge, **attr)` is an operation synonymous of the `add_edge` function (using `Graph.add_edge(u, v, weight=w`))
    - `Graph.remove_node(n)` is an operation synonymous of the `remove_vertex` function
    - `Graph.remove_edge(u, v)` is an operation synonymous of the `remove_edge` function

    ### Design patterns

    | Approach                  | Examples                       | Correctness | Completeness | Viability                     | Weaknesses                                    |
    | ------------------------- | ------------------------------ | ----------- | ------------ | ----------------------------- | --------------------------------------------- |
    | Uninformed (Exhaustive)   | Depth first search, Dijkstra’s | Yes         | Yes          | No (too slow)                 | Slow (not acceptable)                         |
    | Informed (Heuristic)      | Best first search, A*          | Yes         | Yes          | Maybe (with a good heuristic) | Difficult to find good heuristic (ok)         |
    | Greedy                    | Nearest-Neighbour, Kruskal’s   | No          | Yes          | Yes                           | Non-optimal (ok)                              |
    | Informed (Meta-heuristic) | Tabu-search, swarm algorhithms | No          | Yes          | Yes                           | Needs an algorithm to generate solutions (ok) |
    |                           |                                |             |              |                               |                                               |

    A meta-heuristic algorithm is likely overkill for this problem, as |V| and |E| are small enough that other design patterns are more efficient. An greedy informed search algorithm like A* will be used for its fast $O(\space(|V|+|E|)\log(|V|)\space)$ time efficiency and simple implementation. The downside of A* is it requires knowledge of the entire graph.
    """)
    return


@app.cell
def _(facility_drawer, seed_input):
    facility_drawer.draw_facility(seed_input.value)
    return


if __name__ == "__main__":
    app.run()
