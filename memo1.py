import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium", app_title="Memo1", css_file="custom.css")


@app.cell
def _():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import copy

    return copy, mo, mpatches, nx, plt, random


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <mark></mark>
    """)
    return


@app.cell
def _(copy, mpatches, nx, plt, random, seed_input):
    class GraphDrawer:
        def __init__(self) -> None:
            self.graph, self.entry, self.exit_a, self.exit_b, self.supplies = self._get_facility(seed_input.value)

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
                        for nc, nr in self._neighbours(cols, rows, c, r):
                            if visited[nc][nr]:
                                graph.add_edge((c, r), (nc, nr), weight=1)
                                carve(c, r)
                                break
            return graph

        def get_abstracted_graph(self) -> nx.Graph:
            res = copy.deepcopy(self.graph)
            for u, d in self.graph.degree:
                if d == 2 and u not in self.supplies and u not in {self.exit_a, self.exit_b, self.entry}:
                    n0 = list(res.neighbors(u))[0]
                    n1 = list(res.neighbors(u))[1]
                    w = res.get_edge_data(u, n0)["weight"] + res.get_edge_data(u, n1)["weight"]
                    res.remove_node(u)
                    res.add_edge(n0, n1, weight=w)
            return res

        def get_path_from_super_path(self, path: list) -> list:
            res = []
            for i in range(len(path) - 1):
                for n in nx.shortest_path(self.graph, source=path[i], target=path[i + 1], weight="weight"):
                    res.append(n)
                res.pop()
            res.append(path[-1])
            return res


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
            return self._draw_facility(self.graph, self.entry, self.exit_a, self.exit_b, self.supplies, highlight_path=None, title="Facility Layout", node_colors=None,  supply_collected=None,figsize=(8, 8))

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

    ### Array
    - $\text{set}: \text{Array} \times \mathbb{Z}^+ \times \text{Item} \to \text{List}$
    - $\text{get}: \text{List} \times \mathbb{Z}^+ \to \text{Item}$
    - $\text{length}:\text{List} \to \mathbb{Z}^+$

    ## Algorithm

    ### Worded defintion
    Given Graph $G = (V, E, w)$, vertex $v_e \in V$, Set of vertices $V_x \subseteq V$, Set of vertices $V_s \subseteq V$, Map $M_s: V \to \text{string or null}$, Set $S$ and Array $A$, return $W \times A_1$

    ### Signature specification
    $\text{ember\_rescue}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \times \text{Map}[\text{Vertex}, \text{String or NULL}] \times \text{Set}[\text{String}] \times \text{Array}[\text{String}, 5] \to \text{List}[\text{Vertex}] \times \text{Array}[\text{String}, 5]$

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

    #### $A$

    What does it model?
    Array $A$ models CRUDY-1's limited supply unit storage

    An array has fixed size, like CRUDY-1's supply unit storage.

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

    ### NetworkX signature specifications → Pythonc
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

    #### Justification
    Due to small $|V|$ and $|E|$, meta-heuristic algorithms are overkill in complexity.

    The approach of finding pair-distances between supplies, entrances and exits, all of which there is a constant amount of, allows for otherwise too inefficient algorithms to be considered.

    Pairwise-paths can be found in quasi-linear time with dijkstra's algorithm, which is used over Floyd-Warshall due needing these paths between only a subset of $V$, allowing for $O(|V|log|V|) time complexity. A more complex algorithm like the one in [Thorup's 1999 paper](https://doi.org/10.1145/316542.316548).

    After pairwise-paths have been found, a super-path can be found from an entrance through supplies and to an exit by a simply brute force in $O(1)$ time, due to this constant amount of vertices in this super-path. A faster algorithm like branch and bound is overkill for this problem, as the constant factor is so small.

    This path may be then collapsed to a path through $G$ by storing the shortest paths found in the dijkstra's step in a map and retrieving them in constant time.

    ### Verbose Algorithm Explanation
    The algorithm first finds and stores the shortest paths and distances between each pair of vertices $u,v \in V_s$, $v_e \text{ and } v \in V_x$, and $u \in V_s, v \in V_x$ using Dijkstra's with total time complexity of $O(|V|(|V_s| + |V_x|) \log(|V|))$. It then uses a brute-force algorithm to select an order of supplies, starting from $v_e$ and ending at $v_x \in V_x$ with time complexity of $O(|V_s| + |V_x|)$. It then reconstructs the walk on $G$ from the shortest paths found at the beginning of the algorithm in $O(|V|)$ time, for a total time complexity of $O(|V|(|V_s| + |V_x|) \log(|V|) + |V|)$.

    Dijkstra’s is a search algorithm that starts at a vertex $s$ and expands it by adding all its neighbours to a priority queue of vertices seen but not expanded. Each vertex in this priority queue has priority based on distance from $s$. It then expands the next vertex in the pq and repeats until all the target vertices if found, where it returns the paths from $s$ to those vertices, otherwise returning the paths found from $s$ to those vertices that can be reached from $s$.

    ### Pseudocode
    ```
    FUNCTION swap(L: List, i: postive interger, j: positive interger) -> List
        res <- L
        res[i] <- L[j]
        res[j] <- L[i]
        return res
    END FUNCTION

    FUNCTION reverse(L: List) -> List
        res <- L
        FOR i <- 1 to ceil(length(L) / 2) DO
            res <- swap(res, i, length(L) - i)
        END FOR
        RETURN res
    END FUNCTION

    FUNCTION reconstruct_path(came_from: Map[Vertex, Vertex], e: Vertex) -> List[Vertex]
        res <- empty List
        curr <- e
        WHILE has(came_from, curr) DO
    	    push(res, curr)
    	    curr <- came_from[curr]
    	END WHILE
    	return reverse(res)
    END FUNCTION

    FUNCTION dijkstra(G: Graph, source: Vertex, sinks: Set[Vertex]) -> Map[Vertex, List[Vertex]]
    	res <- Map with empty List FOR EACH s in sinks
    	dist <- ∞ FOR EACH v in G
    	dist[source] <- 0
    	prev <- empty Map
    	pq <- priority queue containing all vertices keyed by dist
    	WHILE pq is not empty DO
    		u <- extractMin(pq)
    		IF u in sinks THEN
    			res[u] <- list with source then reconstruct_path(prev, u)
    			IF size(res) = res(sinks) THEN
    				RETURN res
    			END IF
    		END IF
    		FOR EACH v IN get_neighbours(G, u) DO
                w <- get_edge_weight(u, v)
    			IF dist[u] + w < dist[v] THEN
    				prev[v] <- u
    				dist[v] <- dist[u] + w
    				update(pq, v)
    			END IF
    		END FOR
    	RETURN res
    END FUNCTION

    FUNCTION some_pairs_shortest_path(G: Graph, sources: Set[Vertex], sinks: Set[Vertex]) -> Map[Vertex, Map[Vertex, List[Vertex]]]
    	res <- empty Map
    	FOR EACH source IN sources DO
    		paths <- dijkstra(G, source, difference(sinks, {source}))
    		FOR EACH sink IN difference(sinks, {source}) DO
    			res[source][sink] <- paths[sink]
    		END FOR
    	END FOR
    	RETURN res
    END FUNCTION

    FUNCTION get_path_length(G: Graph, path: List[Vertex]) -> positive interger or 0
    	res <- 0
    	FOR i <- 1 TO length(path) - 1 DO
    		res <- res + get_edge_weight(G, path[i], path[i + 1])
    	END FOR
    	RETURN res
    END FUNCTION

    FUNCTION get_pairs_path_distances(G: Graph, pair_path_map: Map[Vertex, Map[Vertex, List[Vertex]]]) -> Map[Vertex, Map[Vertex, positive interger or 0]]
    	res <- empty Map
    	FOR EACH (key_0, value_0) IN pair_path_map DO
    		FOR EACH (key_1, value_1) IN value_0 DO
    			res[key_0][key_1] <- get_path_length(G, value_1)
    		END FOR
    	END FOR
    	RETURN res
    END FUNCTION

    FUNCTION get_set(arr: Array) -> Set
        res <- empty set
        FOR EACH a IN arr DO
            add(res, a)
        END FOR
        return res
    END FUNCTION

    FUNCTION get_unfound_supplies(V_s: Set[Vertex], M_s: Map[Vertex, String OR NULL], S: Set[String], A: Array[String]) -> Set[Vertex]
    	res <- empty set

    	FOR EACH supply IN V_s DO
    		IF has(M_s, supply) and M_s[supply] is not NULL and not element_of(S, M_s[supply]) and not element_of(S, get_set(A)) THEN
    			add(res, supply)
    		END IF
    	END FOR

    	RETURN res
    END FUNCTION

    FUNCTION get_sublist(L: List, i: positive interger) -> List[List]
        res <- empty List
        FOR j <- 1 TO i - 1 DO
            push(res, L[j])
        END FOR
        FOR j <- i + 1 TO length(L) DO
            push(res, L[j])
        END FOR
        push(res, res)
        return res
    END FUNCTION

    FUNCTION generate_permutations(L: List, len_left: positive interger or 0) -> List[List[Vertex]]
        IF length(L) = 0 or len_left = 0 THEN
            RETURN empty List
        END IF
        IF length(L) = 1 and len_left >= 1 THEN
            RETURN Array with L in it
        END IF
        IF len_left = 1 THEN
            res = []
            FOR EACH item IN L:
                push(res, Array with item in it)
            RETURN res
        END IF

    	res <- empty List
    	FOR i <- 1 TO length(L) DO
            item <- L[i]
    		sublist <- get_sublist(L, i)
    		FOR EACH perm IN generate_permutations(sublist, len_left - 1) DO
    			curr <- List with item
    			FOR EACH perm_item IN perm DO
    				push(curr, perm_item)
    			END FOR
    			push(res, curr)
    		END FOR
    	END FOR
    	RETURN res
    END FUNCTION

    FUNCTION brute_force(G: Graph, v_e: Vertex, V_s: Set[Vertex], V_x: Set[Vertex], pair_path_map: Map[Vertex, Map[Vertex, List[Vertex]]], max_supplies: positive interger or 0) -> List[Vertex]

    	pair_path_cost_map <- get_pairs_path_distances(G, pair_path_map)

    	min_cost_found <- infinity
    	min_cost_walk <- null

        permutations <- generate_permutations(List with the items in V_s, max_supplies)

    	FOR EACH permutation IN permutations DO
    		cost <- pair_path_cost_map[v_e][permutation[1]]
    		FOR i <- 1 IN length(permutation) DO
    			cost <- cost + pair_path_cost_map[permutation[i]][permutation[i + 1]]
    		END FOR

    		min_exit_cost <- infinity
    		min_exit <- null
    		end <- permutation[length(permutation)]
    		FOR EACH exit IN V_x DO
    			IF pair_path_cost_map[end][exit] < min_exit_cost THEN
    				min_exit <- exit
    				min_exit_cost <- pair_path_cost_map[end][exit]
    			END IF
    		END FOR

    		IF cost + min_exit_cost < min_cost_found THEN
    			walk <- List containing v_e
    			FOR EACH vertex IN permutation DO
    				push(walk, vertex)
    			END FOR
    			push(walk, min_exit)
    			min_cost_walk <- walk
    			min_cost_found <- cost + min_exit_cost
    		END IF
    	END FOR
        IF length(permutations) == 0 THEN
            FOR EACH exit IN V_x DO
    			IF pair_path_cost_map[v_e][exit] < min_exit_cost THEN
    				min_exit <- exit
    				min_exit_cost <- pair_path_cost_map[v_e][exit]
    			END IF
    		END FOR
        END IF

    	return min_cost_walk
    END FUNCTION

    FUNCTION get_not_null_length(arr: Array) -> positive interger or 0
        res <- 0
        FOR EACH a in arr DO
            IF a isn't NULL THEN
                res <- res + 1
            END IF
        END FOR
        return res
    END FUNCTION

    FUNCTION ember_rescue(G: Graph, v_e: Vertex, V_x: Set[Vertex], V_s: Set[Vertex], M_s: Map[Vertex, String], A: Array[Vertex, size:5], S: Set[String]) -> List[Vertex]

    	unfound_supplies <- get_unfound_supplies(V_s, M_s, S, A)

    	pairs_paths <- some_pairs_shortest_path(G, union(unfound_supplies, {v_e}), union(union(unfound_supplies, V_x), {v_e}))

        num_supplies_carrying <- get_not_null_length(A)

    	super_path <- brute_force(G, v_e, unfound_supplies, V_x, pairs_paths, 5 - num_supplies_carrying)

    	res <- empty List
        A_1 <- A

    	FOR i <- 1 to length(super_path) - 1 DO
            IF has(M_s, super_path[i + 1]) and M_s[super_path[i + 1]] is not NULL THEN
                j <- 1
                WHILE get(A_1, j) is not NULL DO
                    j <- j + 1
                END WHILE
                set(A, j, M_s[super_path[i + 1]])
            END IF
    		pair_path <- pairs_paths[super_path[i][super_path[i + 1]]]
    		last_add <- if i == length(super_path) - 1 then 1 else 0
    		FOR j <- 1 to length(pair_path) - 1 + last_add DO
    			push(res, pair_path[j])
    		END FOR
    	END FOR

    	return res, A_1

    END FUNCTION
    ```

    ### Python Implementation
    """)
    return


@app.cell
def python_impl(mo):
    _impl_code_viewer: mo.md
    with open("memo1_algorithm.py","r") as f:
        _python_code = f.read()
        _impl_code_viewer = mo.md("```python\n" + _python_code + "\n```")

    _impl_code_viewer
    return


@app.cell
def algorithm_explorer_controls(facility_drawer, mo):
    import memo1_algorithm

    def _get_matrix(data: list[list[str | list]]) -> str:
        return rf"""$$\text{{res}}_{{\text{{distances}}}} = \begin{{bmatrix}}
                {r"\\".join(" & ".join((i if type(i) == str else str(len(i))) for i in j) for j in data)}
                \end{{bmatrix}}$$"""

    def _get_list(data: list) -> str:
        return r"\{" + ",".join(data) + r"\}"

    def _get_highlighted_pseudocode(pseudocode: str, line: int) -> str:
        splits = pseudocode.split("\n")
        return "\n".join(splits[:line + 1]) + "\n" + splits[line + 1] + " <--\n" + "\n".join(splits[line + 2:])

    class AlgorithmState:
        def __init__(self, g) -> None:
            self._pseudocode = """```\nFUNCTION some_pairs_shortest_path(...) -> ...
            res <- empty Map
            FOR EACH source IN sources DO
                    paths <- dijkstra(G, source, sinks)
                    FOR EACH sink IN sinks DO
                            res[source][sink] <- paths[sink]
                    END FOR
            END FOR
            RETURN res
    END FUNCTION\n```"""
            self.function = "some_pairs_shortest_path"
            self.line = 0
            self.pseudocode = _get_highlighted_pseudocode(self._pseudocode, self.line)
            self.data = {"graph": g, "sources": [facility_drawer.entry] + facility_drawer.supplies, "sinks": [facility_drawer.exit_a, facility_drawer.exit_b] + facility_drawer.supplies}

        def next(self) -> AlgorithmState:
            match self.function:
                case "some_pairs_shortest_path":
                    match self.line:
                        case 0:
                            self.data["res"] = [[r"\infty" if i != j else "0" for j in range(8)] for i in range(8)]

                            self.line += 1
                        case 1:
                            self.data["source"] = self.data.get("source", -1) + 1
                            if len(self.data["sources"]) > 0:
                                self.line += 1
                            else:
                                self.line = 7
                        case 2:
                            self.data["paths"] = memo1_algorithm.dijkstra(self.data["graph"], self.data["sources"][self.data["source"]], self.data["sinks"])
                            self.line += 1
                        case 3:
                            self.data["sink"] = self.data.get("sink", -1) + 1
                            if len(self.data["sinks"]) > 0:
                                self.line += 1
                            else:
                                self.line = 6
                        case 4:
                            self.data["res"][self.data["source"]][self.data["sink"]] = self.data["paths"][self.data["sinks"][self.data["sink"]]]
                            self.line += 1
                        case 5:
                            self.line += 1
                        case 6:
                            if self.data["sink"] < len(self.data["sinks"]):
                                self.line = 4
                            else:
                                self.line += 1
                        case 7:
                            if self.data["source"] < len(self.data["sources"]):
                                self.line = 2
                            else:
                                self.line += 1
                        case 8:
                            prev = self.data["prev"]
                            self.function = prev.function
                            self.line = prev.line
                            self._pseudocode = prev._pseudocode
                            self.pseudocode = prev.pseudocode
                            self.data = prev.data

            match self.function:
                case "some_pairs_shortest_path":
                    self.data["matrix_latex"] = _get_matrix(self.data["res"])


            self.pseudocode = _get_highlighted_pseudocode(self._pseudocode, self.line)
            return self

    next_button = mo.ui.button(on_click=lambda v: v.next(), label="Next", value=AlgorithmState(facility_drawer.get_abstracted_graph()))
    next_button
    return (next_button,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Algorithm Explorer
    """)
    return


@app.cell(hide_code=True)
def algorithm_explorer(facility_drawer, mo, next_button, seed_input):
    class AlgorithmVisualiser:
        def __init__(self) -> None:
            self.pseudocode_viewer = mo.md(next_button.value.pseudocode)
            self.shortest_path_matrix = mo.md(next_button.value.data.get("matrix_latex", r"$\text{res}_{\text{distances}} = \text{not defined}$"))

            self.facility_viewer = facility_drawer.draw_facility(seed_input.value)

            self.tabs = mo.ui.tabs({
                "Some Pairs Shortest Paths": mo.vstack([self.facility_viewer, self.pseudocode_viewer, self.shortest_path_matrix]),
                "Brute-Force Super-Path": mo.vstack([self.facility_viewer, self.pseudocode_viewer]),
                "Reconstruct Path": mo.vstack([self.facility_viewer, self.pseudocode_viewer])
            }, on_change=lambda tab_name: _vis.jump_to(tab_name))

    _vis = AlgorithmVisualiser()

    _title = mo.md("Algorithm Tracer")

    _vis.tabs
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Justification

    ### Suitability
    - The number of supplies in the facility is low, and the number of verticies is much higher. This suits the time complexity scaling well with number of verticies and badly with number of supplies
    - The facilities size: 12x12 sectors means that max number of vertices in abstraction is 144 and this small size favours an algorithm that is easier to implement
    - Since the algorithm always finds the shortest route that collects all supplies to an exit, an edge case would be the seed that gives the worst facility for the algorithm
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
    ## Proofs
    ### Time complexity
    I will analyse each functions' time complexity in order to find the overall complexity

    #### $\text{swap}: \text{List} \to \text{List}$
    Trivially $T(n) = O(1) = \Omega(1) = \Theta(1)$

    #### $\text{reverse}: \text{List} \to \text{List}$
    For $L$ being the List input and $n = |L|$,

    Calls `swap` $\lceil{\frac{n}{2}}\rceil$ times $\therefore T(n) \frac{n}{2} = O(n) = \Omega(n) = \Theta(n)$

    #### $\text{reconstruct\_path}: \text{Map}[\text{Vertex}, \text{Vertex}] \times \text{Vertex} \to \text{List}[\text{Vertex}]$

    For $M$ being the Map input and $n = |keys(M)|$,

    Calls $O(1)$ operations up to $n$ times, then `reverse` with $n = n \\ \therefore T(n) = O(n) = \Omega(n) = \Theta(1)$

    #### $\text{dijkstra}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \to \text{Map}[\text{Vertex}, \text{List}[\text{Vertex}]]$

    For $G = (V, E)$ being the graph input, $n = |V|, m = |E|$, and $S$ being the third input and $s = |S|$,

    Creates a priority queue with $n$ elements, changes priorities in this pq at most $n^2$ times, removes from this priority queue at most $n$ times, and calls `reconstruct_path` $|S|$ times

    $\therefore T(n) = n^2 \log n + n \log n + n + ns = O((m + n^2) \log n + ns) = \Omega((m + n) \log n + ns) = \Theta((m + n) \log n + s)$

    #### $\text{some\_pairs\_shortest\_path}: \text{Graph} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \to \text{Map}[\text{Vertex}, \text{Map}[\text{Vertex}, \text{List}[\text{Vertex}]]]$

    For $G = (V, E)$ being the graph input, $n = |V|, m = |E|$, $S_0$ being the first set input, $s_0 = |S_0|$, and $S_1$ being the second set input, $s_1 = |S_1|$,

    Calls `dijkstra` $s_0$ times with $n = n, m = m, s = s_1 - 1$, then adds the return value to return value $s_0 (s_1 - 1)$ times

    $\therefore T(n) = s_0(n^2 \log n + n \log n + n + n(s_1 - 1) + s_1 - 1) = O(s_0((m + n^2) \log n + n s_1)) = \Omega(s_0((m + n) \log n + n s_1)) = \Theta(s_0((m + n) \log n + n s_1))$

    #### $\text{get\_path\_length}: \text{Graph} \times \text{List}[\text{Vertex}] \to \mathbb{Z}^+ \cup \{0\}$

    $P$ being the list input, $n = |P|$,

    Calls `get_edge_weight` $n$ times

    $\therefore T(n) = n = O(n) = \Omega(n) = \Theta(n)$

    #### $\text{get\_pairs\_path\_distances}: \text{Graph} \times \text{Map}[\text{Vertex}, \text{Map}[\text{Vertex}, \text{List}[\text{Vertex}]]] \to \text{Map}[\text{Vertex}, \text{Map}[\text{Vertex}, \mathbb{Z}^+ \cup \{0\}]]$

    For $G = (V, E)$ being the graph input, $n = |V|, m = |E|$,

    Calls `get_path_length` $n^2$ times with $n <= n$

    $\therefore T(n) = n^3 = O(n^3) = \Omega(n^3) = \Theta(n^3)$

    #### $\text{get\_set}: \text{Array} \to \text{Set}$

    For $A$ being the array input, $n = |A|$,

    Calls `add` $n$ times, $\therefore T(n) = n = O(n) = \Omega(n) = \Theta(n)$

    #### $\text{get\_unfound\_supplies}: \text{Set}[\text{Vertex}] \times \text{Map}[\text{Vertex}, \text{String or NULL}] \times \text{Set}[\text{String}] \times \text{Array}[\text{String}] \to \text{Set}[\text{Vertex}]$

    For $V_s$ being the first set input, $n = |V_s|$

    Calls `add` $n$ times, $\therefore T(n) = n = O(n) = \Omega(n) = \Theta(n)$

    #### $\text{get\_sublist}: \text{List} \times \mathbb{Z}^+ \to \text{List}[\text{List}]$

    For $L$ being the first list input, $n = |L|$,

    Calls `push` $n$ times, $\therefore T(n) = n = O(n) = \Omega(n) = \Theta(n)$

    #### $\text{generate\_permutations}: \text{List} \times \mathbb{Z}^+ \cup \{0\}$

    For $L$ being the first input list, $n = |L|$, and |i| being the number input,

    For $i = 0: T(i) = 1, i = 1: T(i) = n, i = i: T(i) = \prod_{k=\max(n-i, 1)}^{n} k = \frac{n!}{(n - i - 1)!}$

    $\therefore T(i) = O(\frac{n!}{(n - i - 1)!}) = \Omega(\frac{n!}{(n - i - 1)!}) = \Theta(\frac{n!}{(n - i - 1)!})$

    #### $\text{brute\_force}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Map}[\text{Vertex}, \text{Map}[\text{Vertex}, \text{List}[\text{Vertex}]]] \times \mathbb{Z}^+ \cup \{0\}$

    For $V_s$ being the first input set, $s = |V_s|$, $V_x$ being the second input set, $x = |V_x|$, $\max_s$ being the first input number,

    Calls `generate_permutations` with $n = s, i = \max_s$ then for each permutation:
    - calls `cost <- ...` operation for length of permutation ($\max_s$)
    - calls `if ... end if` block for each exit in $V_x$ ($x$)
    - calls `push` operation for length of permutation ($\text{max}_s$)
    - if permutation is empty ($\max_s = 0$), calls `if ... end if` block for each exit in $V_x$ ($x$)

    $\therefore T(n) = \max(x, (2 \max_s + x) \frac{s!}{(s - \max_s - 1)!}) = O((\max_s + x) \frac{n!}{(n - i - 1)!}) = \Omega((\max_s + x) \frac{n!}{(n - i - 1)!}} = \Theta(x + \frac{n!}{(n - i - 1)!})$

    #### get_not_null_length

    For $A$ being the first input, $n=|A|$, trivally $T(n) = n = O(n) = \Omega(n) = \Theta(n)$

    #### $\text{ember\_rescue}: \text{Graph} \times \text{Vertex} \times \text{Set}[\text{Vertex}] \times \text{Set}[\text{Vertex}] \times \text{Map}[\text{Vertex}, \text{String or NULL}] \times \text{Set}[\text{String}] \times \text{Array}[\text{String}, 5] \to \text{List}[\text{Vertex}] \times \text{Array}[\text{String}, 5]$

    For $G = (V, E)$ being the first Graph input, $v_e$ being the first vertex input, $V_s$ being the first set input, $V_x$ being the second set input, $M_s$ being the first map input, $S$ being the third set input, and $A$ being the first array input,

    Calls:
    - `get_unfound_supplies` with $n = |V_s|$,
    - `some_pairs_shortest_path` with $n = |V|, m = |E|, s_0 <= |V_s| + 1, s_1 <= |V_s| + |V_x| + 1$
    - `get_not_null_length` with $n <= |A| = 5$
    - `brute_force` with $x = |V_x|, \max_s <= |A| = 5$, letting $W_s$ be the return value of the function
    - For loop iterating $|W_s| <= |A| = 5$ times, call:
      - While loop running at most $|A|$ times
      - For loop iterating at most $|V|$ times

    $\therefore T(n) = |V_s| + (|V_s| + 1)((|V|^2 + |E|) \log |V| + |V| \log |V| + |V| + (|V| + 1)(|V_s| + |V_x|)) + |A| + \max(|V_s|, (2|A| + |V_s|) \frac{|V_s|!}{(|V_s| - |A| - 1)!}) + |A|(|A| + |V|)
    \\ = O(|V_s|(|V|(|V_x| + |V_s|) + (|V|^2 + |E|)\log|V|) + (2|A| + |V_s|)\frac{|V_s|!}{(|V_s| - |A| - 1)!} + |A|(|A| + |V|))
    \\ = \Omega(|V_s|(|V|(|V_x| + |V_s|) + ((|V| + |E|)\log|V|)) + (2|A| + |V_s|)\frac{|V_s|!}{(|V_s| - |A| - 1)!} + |A|(|A| + |V|))
    \\ = \Theta(|V_s|(|V|(|V_x| + |V_s|) + ((|V| + |E|)\log|V|)) + \frac{|V_s|!}{(|V_s| - |A| - 1)!} + |A|(|A| + |V|)$

    $\because$ The facility has a constant number of supplies, exits, and CRUDY-1's storage is also constant, we can simplify it to $O((|V|^2 + |E|)\log|V|) = \Omega((|V| + |E|)\log|V|) = \Theta((|V| + |E|)\log|V|)$

    ### Space complexity

    ### Correctness

    ### Optimality
    """)
    return


if __name__ == "__main__":
    app.run()
