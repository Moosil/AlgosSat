import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import random
    import math
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.colors as mcolors
    from collections import deque
    import json
    import os
    import datetime

    SAVE_FILE_ORIG = "responses.json"           # Memo 01 responses (read-only)
    SAVE_FILE_SUPP = "responses_M02_supp.json"  # supplementary responses (written here)
    return (
        SAVE_FILE_ORIG,
        SAVE_FILE_SUPP,
        LinearSegmentedColormap,
        datetime,
        deque,
        json,
        math,
        mcolors,
        mo,
        nx,
        os,
        plt,
        random,
    )


@app.cell
def header(mo):
    mo.md("""
    # Operation Emberlight -- Memo 02 Supplementary Workbook
    ## Best Case · Average Case · Space Complexity

    | Field | Value |
    |---|---|
    | **Name** | *(your name)* |
    | **Student number** | *(your number)* |
    | **Facility seed** | *(enter below -- same as Memo 01 / 02)* |
    | **Teacher** | *(teacher name)* |

    > **Why these supplements?**
    > Your Memo 02 analysis gave a **tight upper bound** -- the *worst case*. A complete
    > complexity picture also needs the **best case** (Ω), the **average case** (the
    > expected behaviour CRUDY-1 actually experiences), and the **space** the algorithm
    > consumes -- which matters because the drone has limited on-board memory. Each
    > section below has a live demo run on **your own facility**.

    > **Authentication note:** use the **same seed** as your Memo 01 / 02 workbooks.

    ---
    **What this workbook contains**

    | Label | Section | Focus |
    |---|---|---|
    | `[S2-A]` | Best-Case Time Complexity (Ω) | early termination · best target placement |
    | `[S2-B]` | Average-Case Time Complexity (Θ) | expected expansions over random targets |
    | `[S2-C]` | Space Complexity | frontier/stack memory · BFS vs DFS · drone RAM |

    Each section: read the briefing → explore the demo on your facility → write your
    response → Save at the bottom.
    """)
    return


@app.cell
def seed_cell(mo):
    seed_input = mo.ui.number(
        value=12345, start=0, stop=99999999, step=1,
        label="Your facility seed (from your Memo 01 cover sheet)"
    )
    mo.vstack([
        mo.md("### Enter your seed, then press Tab to rebuild the facility."),
        seed_input
    ])
    return (seed_input,)


@app.cell
def multi_wing_generator(nx, random, seed_input):

    WING_COLS, WING_ROWS = 10, 10

    def _neighbours(cols, rows, c, r):
        for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nc, nr = c + dc, r + dr
            if 0 <= nc < cols and 0 <= nr < rows:
                yield nc, nr

    def _build_wing(cols, rows, rng):
        visited = [[False] * rows for _ in range(cols)]
        g = nx.Graph()
        for c in range(cols):
            for r in range(rows):
                g.add_node((c, r))

        def carve(c, r):
            visited[c][r] = True
            dirs = list(_neighbours(cols, rows, c, r))
            rng.shuffle(dirs)
            for nc, nr in dirs:
                if not visited[nc][nr]:
                    g.add_edge((c, r), (nc, nr), weight=1)
                    carve(nc, nr)

        carve(0, 0)
        return g

    def get_multi_wing_facility(seed):
        int_seed = int(seed)
        n_wings   = 2 + (int_seed % 3)
        wing_names = ['Alpha', 'Beta', 'Gamma', 'Delta'][:n_wings]
        wings = [
            _build_wing(WING_COLS, WING_ROWS, random.Random(int_seed * 31 + w * 7919))
            for w in range(n_wings)
        ]
        junctions = []
        for w in range(n_wings - 1):
            jrng = random.Random(int_seed * 17 + w * 5003)
            rows_avail = list(range(2, WING_ROWS - 2))
            jrng.shuffle(rows_avail)
            r1, r2 = sorted(rows_avail[:2])
            junctions.append(((w, WING_COLS - 1, r1), (w + 1, 0, r1)))
            junctions.append(((w, WING_COLS - 1, r2), (w + 1, 0, r2)))
        entry  = (0, 0, 0)
        exit_a = (n_wings - 1, WING_COLS - 1, WING_ROWS - 1)
        exit_b = (n_wings - 1, WING_COLS - 1, 0)

        # Supply placement -- must match marimo_memo02v01.py exactly so the
        # supplementary map is seed-for-seed identical to the Memo 02 facility.
        srng = random.Random(int_seed * 13 + 42)
        reserved = {entry, exit_a, exit_b}
        for n1, n2 in junctions:
            reserved.add(n1)
            reserved.add(n2)

        per_wing_cands = []
        for w, wg in enumerate(wings):
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
        empty_wing = srng.choice(range(1, n_wings)) if n_wings >= 3 else None
        supply_wings = [w for w in range(n_wings) if w != empty_wing]

        # Deal supplies round-robin across the supplied wings until we have 5
        # (or the dead-end candidates run out). Looping rather than a fixed 2
        # passes matters on 2-wing seeds, which would otherwise yield only 4.
        supplies = []
        while len(supplies) < 5:
            added = False
            for w in supply_wings:
                if len(supplies) >= 5:
                    break
                for n in per_wing_cands[w]:
                    if n not in supplies:
                        supplies.append(n)
                        added = True
                        break
            if not added:
                break

        return {
            'n_wings': n_wings, 'wing_names': wing_names, 'wings': wings,
            'wing_cols': WING_COLS, 'wing_rows': WING_ROWS,
            'entry': entry, 'exit_a': exit_a, 'exit_b': exit_b,
            'supplies': supplies[:5], 'junctions': junctions,
        }

    fac = get_multi_wing_facility(seed_input.value)
    return (fac,)


@app.cell
def cost_model(fac, random, seed_input):
    """Apply the Amendment A2 cost models to the facility corridors (for display).

    Wing Alpha (w=0): Uniform cost = 1.
    Wing Beta  (w=1): Depth-based cost = 1 + max(col1, col2) // 3.
    Wing Gamma / Delta (w>=2): Seed-randomised cost in [1, 5].
    Inter-wing junctions: cost = 1.
    The complexity demos below use the unweighted structure (V, E); the costs are
    shown only so this workbook's map matches your Memo 02 facility.
    """
    import copy

    int_seed = int(seed_input.value)
    weighted_wings = [copy.deepcopy(_w) for _w in fac['wings']]

    for _w, _wg in enumerate(weighted_wings):
        if _w == 0:
            pass
        elif _w == 1:
            for (_c1, _r1), (_c2, _r2) in list(_wg.edges()):
                _wg[_c1, _r1][_c2, _r2]['weight'] = 1 + max(_c1, _c2) // 3
        else:
            _crng = random.Random(int_seed * 41 + _w * 3331)
            for (_c1, _r1), (_c2, _r2) in list(_wg.edges()):
                _wg[_c1, _r1][_c2, _r2]['weight'] = _crng.randint(1, 5)

    fac_weighted = dict(fac)
    fac_weighted['wings'] = weighted_wings

    wing_cost_summary = []
    for _w, _wg in enumerate(weighted_wings):
        _costs = [d['weight'] for _, _, d in _wg.edges(data=True)]
        if _costs:
            wing_cost_summary.append({
                'wing':  fac['wing_names'][_w],
                'model': ['Uniform', 'Depth-based', 'Randomised', 'Randomised'][_w],
                'min':   min(_costs),
                'max':   max(_costs),
                'avg':   round(sum(_costs) / len(_costs), 2),
                'total': sum(_costs),
            })

    return (fac_weighted, wing_cost_summary)


@app.cell
def drawing_utils_weighted(LinearSegmentedColormap, mcolors, plt):
    """Weighted multi-wing facility renderer (matches the Memo 02 main workbook)."""

    COL_BG       = '#F5F7FA'
    COL_GRID     = '#C8D0DC'
    COL_WALL     = '#44546A'
    COL_ENTRY    = '#0B6E6B'
    COL_EXIT     = '#7A1E2C'
    COL_SUPPLY   = '#4AA8A0'
    COL_JUNCTION = '#7A1E2C'
    COL_ROUTE    = '#6D28D9'   # bold purple
    _GAP = 3

    _WEIGHT_CMAP = LinearSegmentedColormap.from_list(
        'emberweight', ['#B8E0DE', '#F4C97A', '#7A1E2C'], N=256
    )

    def _cost_color(weight, min_w=1, max_w=5):
        norm = (weight - min_w) / max(max_w - min_w, 1)
        return _WEIGHT_CMAP(norm)

    def draw_weighted_facility(fac_w, highlight_path=None,
                               title="Weighted Multi-Wing Facility"):
        wc = fac_w['wing_cols']
        wr = fac_w['wing_rows']
        nw = fac_w['n_wings']
        total_w = nw * wc + (nw - 1) * _GAP

        fig_w = max(12, total_w * 0.62)
        fig_h = max(6, wr * 0.62 + 2.0)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_facecolor(COL_BG)
        fig.patch.set_facecolor(COL_BG)

        def xoff(w):
            return w * (wc + _GAP)

        for w, wing in enumerate(fac_w['wings']):
            ox = xoff(w)
            for c in range(wc + 1):
                ax.plot([ox + c, ox + c], [0, wr], color=COL_GRID, lw=0.3, zorder=1)
            for r in range(wr + 1):
                ax.plot([ox, ox + wc], [r, r], color=COL_GRID, lw=0.3, zorder=1)

            for (c1, r1), (c2, r2), data in wing.edges(data=True):
                col = _cost_color(data.get('weight', 1))
                ax.plot([ox + c1 + 0.5, ox + c2 + 0.5], [r1 + 0.5, r2 + 0.5],
                        color=col, lw=4.5, solid_capstyle='round', zorder=2)

            for c in range(wc):
                for r in range(wr):
                    if c + 1 < wc and not wing.has_edge((c, r), (c + 1, r)):
                        ax.plot([ox + c + 1, ox + c + 1], [r, r + 1],
                                color=COL_WALL, lw=1.4, zorder=3)
                    if r + 1 < wr and not wing.has_edge((c, r), (c, r + 1)):
                        ax.plot([ox + c, ox + c + 1], [r + 1, r + 1],
                                color=COL_WALL, lw=1.4, zorder=3)

            ax.add_patch(plt.Rectangle((ox, 0), wc, wr, fill=False,
                                       edgecolor=COL_WALL, lw=2.2, zorder=4))
            model_names = ['Uniform', 'Depth-based', 'Randomised', 'Randomised']
            model_lbl = model_names[w] if w < len(model_names) else 'Randomised'
            ax.text(ox + wc / 2, wr + 0.55, f"Wing {fac_w['wing_names'][w]}",
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    color='#0B1F3B', zorder=8)
            ax.text(ox + wc / 2, wr + 0.15, f"({model_lbl})", ha='center',
                    va='bottom', fontsize=7, color='#44546A', zorder=8)

        for (w1, c1, r1), (w2, c2, r2) in fac_w['junctions']:
            x1, y1 = xoff(w1) + c1 + 0.5, r1 + 0.5
            x2, y2 = xoff(w2) + c2 + 0.5, r2 + 0.5
            ax.plot([x1, x2], [y1, y2], color=COL_JUNCTION, lw=2.0,
                    linestyle='--', alpha=0.8, zorder=5)
            ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=6)
            ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=6)

        for i, (ws, cs, rs) in enumerate(fac_w.get('supplies', [])):
            ox = xoff(ws)
            ax.plot(ox + cs + 0.5, rs + 0.5, marker='*', markersize=13,
                    color=COL_SUPPLY, markeredgecolor=COL_ENTRY,
                    markeredgewidth=0.7, zorder=7)
            ax.text(ox + cs + 0.62, rs + 0.58, f'S{i+1}', fontsize=6,
                    color=COL_WALL, zorder=8)

        we, ce, re = fac_w['entry']
        ox = xoff(we)
        ax.add_patch(plt.Circle((ox + ce + 0.5, re + 0.5), 0.3,
                                color=COL_ENTRY, zorder=9))
        ax.text(ox + ce + 0.5, re + 0.5, 'E', ha='center', va='center',
                fontsize=6, color='white', fontweight='bold', zorder=10)

        for lbl, (wx, cx, rx) in [('A', fac_w['exit_a']), ('B', fac_w['exit_b'])]:
            ox = xoff(wx)
            ax.add_patch(plt.Circle((ox + cx + 0.5, rx + 0.5), 0.3,
                                    color=COL_EXIT, zorder=9))
            ax.text(ox + cx + 0.5, rx + 0.5, lbl, ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=10)

        if highlight_path and len(highlight_path) > 1:
            for i in range(len(highlight_path) - 1):
                w1, c1, r1 = highlight_path[i]
                w2, c2, r2 = highlight_path[i + 1]
                ax.plot([xoff(w1) + c1 + 0.5, xoff(w2) + c2 + 0.5],
                        [r1 + 0.5, r2 + 0.5], color=COL_ROUTE, lw=5.0,
                        linestyle='-', alpha=1.0, zorder=8, solid_capstyle='round')

        sm = plt.cm.ScalarMappable(cmap=_WEIGHT_CMAP,
                                   norm=mcolors.Normalize(vmin=1, vmax=5))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.018, pad=0.02)
        cbar.set_label('Corridor cost', fontsize=8, color='#0B1F3B')
        cbar.set_ticks([1, 2, 3, 4, 5])
        cbar.ax.tick_params(labelsize=7)

        ax.set_xlim(-0.5, total_w + 0.5)
        ax.set_ylim(-1.0, wr + 1.4)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=11, fontweight='bold',
                     color='#0B1F3B', pad=10)
        plt.tight_layout()
        return fig

    return (COL_ROUTE, draw_weighted_facility)


@app.cell
def analysis_engine(deque, fac, nx):
    """Build the flat facility graph and run instrumented BFS / DFS from the entry.

    Everything the three demos need is precomputed here from YOUR facility:
      - bfs_rank[node]   = number of sector-expansions before this node is dequeued
                           (= "work to reach this target" if the algorithm stops on it)
      - bfs_frontier     = queue length over time (for space analysis)
      - dfs_stack_sizes  = explicit-stack length over time (for space analysis)
      - dfs_max_depth    = deepest recursion level (recursive DFS stack depth)
    """
    # Flat graph: nodes are (wing, col, row)
    G = nx.Graph()
    for _w, _wing in enumerate(fac['wings']):
        for (_c1, _r1), (_c2, _r2) in _wing.edges():
            G.add_edge((_w, _c1, _r1), (_w, _c2, _r2))
    for (_w1, _c1, _r1), (_w2, _c2, _r2) in fac['junctions']:
        G.add_edge((_w1, _c1, _r1), (_w2, _c2, _r2))

    entry = fac['entry']
    V = G.number_of_nodes()
    E = G.number_of_edges()

    def bfs_instrumented(graph, start):
        visited = {start}
        q = deque([start])
        order, frontier = [], []
        ops = 0
        while q:
            frontier.append(len(q))      # queue size BEFORE this pop
            u = q.popleft()
            order.append(u)
            ops += 1                       # one expansion
            for v in graph.neighbors(u):
                ops += 1                   # one corridor examined
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        return order, frontier, ops

    def dfs_instrumented(graph, start):
        visited = set()
        stack = [(start, 1)]
        order, sizes = [], []
        max_depth = 0
        while stack:
            sizes.append(len(stack))       # explicit stack size BEFORE this pop
            u, d = stack.pop()
            if u in visited:
                continue
            visited.add(u)
            order.append(u)
            max_depth = max(max_depth, d)
            for v in graph.neighbors(u):
                if v not in visited:
                    stack.append((v, d + 1))
        return order, sizes, max_depth

    _border, bfs_frontier, _bops = bfs_instrumented(G, entry)
    # rank = expansions needed before node is dequeued (1-indexed): first pop = 1
    bfs_rank = {node: i + 1 for i, node in enumerate(_border)}
    _dorder, dfs_stack_sizes, dfs_max_depth = dfs_instrumented(G, entry)

    # all reachable expansion counts (every node is a possible target)
    expansions_all = sorted(bfs_rank.values())

    return (
        G,
        V,
        E,
        entry,
        bfs_rank,
        bfs_frontier,
        dfs_stack_sizes,
        dfs_max_depth,
        expansions_all,
    )


@app.cell
def facility_size(V, E, dfs_max_depth, mo, seed_input):
    mo.vstack([
        mo.md(f"## 📐 Your Facility -- Seed {int(seed_input.value)}"),
        mo.md(
            f"| Quantity | Value |\n|---|---|\n"
            f"| **V -- sectors (nodes)** | **{V}** |\n"
            f"| **E -- corridors (edges)** | **{E}** |\n"
            f"| V + E | {V + E} |\n"
            f"| Deepest DFS branch from entry | {dfs_max_depth} sectors |"
        ),
        mo.callout(mo.md(
            "All three demos below run on **this** facility. Worst-case work for a full "
            "traversal is **O(V + E)**; these supplements ask how the *best*, *average*, "
            "and *space* behaviour compare."
        ), kind="info"),
    ])
    return


@app.cell
def facility_visualiser(draw_weighted_facility, fac_weighted, mo, seed_input, wing_cost_summary):
    _fig = draw_weighted_facility(
        fac_weighted,
        title=(f"Your Facility -- Seed {int(seed_input.value)} · "
               f"{fac_weighted['n_wings']} wings · Variable corridor costs")
    )

    _headers = ['Wing', 'Cost model', 'Min cost', 'Max cost', 'Avg cost', 'Total cost']
    _tlines = [
        "| " + " | ".join(_headers) + " |",
        "| " + " | ".join(["---"] * len(_headers)) + " |",
    ]
    for _r in wing_cost_summary:
        _tlines.append(
            f"| Wing {_r['wing']} | {_r['model']} | {_r['min']} | "
            f"{_r['max']} | {_r['avg']} | {_r['total']} |"
        )
    _table_md = "\n".join(_tlines)

    mo.vstack([
        mo.md("## 🗺️ Your Facility Map"),
        mo.callout(mo.md(
            "The graph your traversal runs on: **E** = entry, **A/B** = exits, dashed "
            "lines = inter-wing junctions. Corridor colour shows cost (**teal** = 1, "
            "**gold** = medium, **maroon** = 5; junctions always 1). Sectors are the **V** "
            "nodes, open corridors the **E** edges. The best-case demo below overlays the "
            "route to a chosen target in **bold purple** on this map."
        ), kind="info"),
        _fig,
        mo.md("### Cost Model Summary"),
        mo.md(_table_md),
    ])
    return


# ======================================================================
# SECTION A -- BEST CASE
# ======================================================================
@app.cell
def s2a_header(mo):
    mo.md("""
---
## [S2-A] Best-Case Time Complexity (Ω)
*Criterion 5 deepener · Written response (approx. 80--150 words)*

> The **best case** is the smallest amount of work the algorithm can do on an input of a
> given size. We describe it with **big-Omega**, Ω. The key question for a traversal is:
> **can the algorithm stop early?**

**Address all three parts:**

**Part 1 -- When does best case occur?**
For your Memo 01 algorithm, describe the input that triggers the least work.
- If it **searches for a single target** (entry → an exit) and stops when found, the best
  case is the target sitting **next to the entry** → Ω(1) expansions.
- If it must **visit every sector** (full exploration / collect all supplies) regardless
  of layout, then it *cannot* stop early, so **best = worst = Θ(V + E)**. State which of
  these is true for *your* algorithm.

**Part 2 -- Use the demo.**
The demo shows, for *your* facility, how many sector-expansions BFS needs to reach **each
possible target**. Read off the **minimum** (best case), and the values for **Exit A**
and **Exit B**. Quote these numbers.

**Part 3 -- Why best case is a weak guarantee.**
Explain why CRUDY-1's mission planning should **not** rely on the best case. (Hint: the
field cannot guarantee the survivor is next to the entrance.)

---
    """)
    return


@app.cell
def s2a_controls(bfs_rank, fac, mo):
    _opts = {f"Exit A {fac['exit_a']}": fac['exit_a'],
             f"Exit B {fac['exit_b']}": fac['exit_b']}
    # add the best and worst nodes as named options
    _best_node = min(bfs_rank, key=bfs_rank.get)
    _worst_node = max(bfs_rank, key=bfs_rank.get)
    _opts[f"Best-case target {_best_node}"] = _best_node
    _opts[f"Worst-case target {_worst_node}"] = _worst_node

    target_pick = mo.ui.dropdown(
        options=_opts, value=f"Exit A {fac['exit_a']}",
        label="Highlight a target's cost on the curve",
    )
    mo.vstack([mo.md("#### 🎛️ Best-case explorer"), target_pick])
    return (target_pick,)


@app.cell
def s2a_demo(bfs_rank, expansions_all, fac, mo, plt, target_pick):
    _best = expansions_all[0]
    _worst = expansions_all[-1]
    _mean = sum(expansions_all) / len(expansions_all)
    _ea = bfs_rank[fac['exit_a']]
    _eb = bfs_rank[fac['exit_b']]
    _pick_val = bfs_rank[target_pick.value]

    _xs = list(range(1, len(expansions_all) + 1))
    _fig, _ax = plt.subplots(figsize=(9, 4.6))
    _fig.patch.set_facecolor("#F5F7FA")
    _ax.set_facecolor("#F5F7FA")
    _ax.fill_between(_xs, expansions_all, color="#B8E0DE", alpha=0.7, zorder=2)
    _ax.plot(_xs, expansions_all, color="#0B6E6B", lw=1.6, zorder=3)

    for _y, _c, _lbl in [(_best, "#0B6E6B", f"best Ω = {_best}"),
                         (_mean, "#B7791F", f"mean ≈ {_mean:.0f}"),
                         (_worst, "#7A1E2C", f"worst O = {_worst}")]:
        _ax.axhline(_y, color=_c, ls="--", lw=1.2, zorder=4)
        _ax.text(len(_xs) * 0.01, _y, _lbl, fontsize=8, color=_c,
                 va="bottom", ha="left")

    _ax.axhline(_pick_val, color="#F0B429", lw=2.4, zorder=5)
    _ax.text(len(_xs) * 0.5, _pick_val,
             f"selected target = {_pick_val} expansions",
             fontsize=8, color="#8a5a00", va="bottom", ha="center")

    _ax.set_xlabel("Targets, sorted from nearest to farthest", fontsize=9)
    _ax.set_ylabel("Sector-expansions to reach target", fontsize=9)
    _ax.set_title("Best case = the nearest possible target", fontsize=11,
                  fontweight="bold", color="#0B1F3B")
    _ax.grid(True, color="#C8D0DC", lw=0.4, alpha=0.7)
    plt.tight_layout()

    mo.vstack([
        mo.callout(mo.md(
            f"On your facility: **best case Ω = {_best}** expansion(s) (a sector next to "
            f"the entry), **worst = {_worst}**, **mean ≈ {_mean:.0f}**. "
            f"Exit A costs **{_ea}**, Exit B costs **{_eb}**."
        ), kind="info"),
        _fig,
        mo.callout(mo.md(
            "If your algorithm must visit **every** sector (e.g. collect all supplies), "
            "early termination is impossible and the best case equals the worst case at "
            f"**{_worst} = Θ(V + E)** -- the curve above would not apply. Say which case is "
            "yours."
        ), kind="neutral"),
    ])
    return


@app.cell
def s2a_map(G, draw_weighted_facility, entry, fac_weighted, mo, nx, target_pick):
    """Overlay the shortest route from entry to the selected target on the map."""
    _t = target_pick.value
    try:
        _path = nx.shortest_path(G, entry, _t)
        _hops = len(_path) - 1
    except Exception:
        _path, _hops = None, None

    _fig = draw_weighted_facility(
        fac_weighted, highlight_path=_path,
        title=f"Route from Entry to selected target {_t}"
    )
    mo.vstack([
        mo.callout(mo.md(
            f"The **bold purple** route is the **fewest-corridor path** BFS would follow "
            f"to the selected target ({_hops} corridors). A target close to **E** is a "
            f"small-work (best-case) input; one far across the wings is closer to the "
            f"worst case. Change the dropdown above to see how placement drives the cost."
            if _path else
            "No path to the selected target (unexpected -- the facility should be "
            "fully connected)."
        ), kind="info"),
        _fig,
    ])
    return


@app.cell
def s2a_input(SAVE_FILE_SUPP, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_SUPP):
        try:
            with open(SAVE_FILE_SUPP, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("S2A_best", "")
        except Exception:
            pass
    resp_s2a = mo.ui.text_area(
        label="**[S2-A] Your best-case analysis**", value=_saved, rows=9,
        full_width=True,
        placeholder=(
            "Part 1 -- My algorithm <stops when it finds an exit / must visit every\n"
            "  sector>, so its best case is <Ω(1) / Θ(V+E)> because ...\n\n"
            "Part 2 -- From the demo: best = ... expansions, Exit A = ..., Exit B = ...\n\n"
            "Part 3 -- Planning must not rely on the best case because the field cannot\n"
            "  guarantee ..."
        )
    )
    resp_s2a
    return (resp_s2a,)


@app.cell
def s2a_display(mo, resp_s2a):
    mo.callout(
        mo.md("**[S2-A] Saved:**\n\n" + resp_s2a.value) if resp_s2a.value.strip()
        else mo.md("*No response entered yet.*"), kind="success")
    return


# ======================================================================
# SECTION B -- AVERAGE CASE
# ======================================================================
@app.cell
def s2b_header(mo):
    mo.md("""
---
## [S2-B] Average-Case Time Complexity (Θ)
*Criterion 5 deepener · Written response (approx. 100--180 words)*

> The **average case** is the *expected* work over a realistic distribution of inputs.
> If CRUDY-1's target is **equally likely to be any sector**, the expected number of
> expansions is the **mean over all targets**. The demo estimates this with a
> **Monte-Carlo simulation** on your facility.

**Address all three parts:**

**Part 1 -- Model the input distribution.**
State your assumption about where the target is (e.g. *"uniformly random across all V
sectors"*). A different assumption (targets cluster near exits) would change the average --
note this.

**Part 2 -- Run the simulation.**
Use the trials slider to run many random searches. Quote the **empirical mean**
expansions and compare it to the theoretical mean for a uniform target,
which is about **(V + 1) / 2**. Note that average and worst case are both **Θ(V)** here --
the average is a *constant factor* smaller, not a different growth class.

**Part 3 -- Consequence.**
Explain what the average case tells CRUDY-1's planners that the worst case does not, and
why both numbers are worth reporting.

---
    """)
    return


@app.cell
def s2b_controls(mo):
    n_trials = mo.ui.slider(start=100, stop=8000, step=100, value=2000,
                            label="Number of random searches (Monte-Carlo trials)",
                            show_value=True)
    sim_seed = mo.ui.number(value=7, start=0, stop=9999, step=1,
                            label="Simulation RNG seed (for reproducibility)")
    mo.vstack([mo.md("#### 🎛️ Average-case simulator"),
               mo.hstack([n_trials, sim_seed], justify="start")])
    return (n_trials, sim_seed)


@app.cell
def s2b_demo(V, expansions_all, mo, n_trials, plt, random, sim_seed):
    _rng = random.Random(int(sim_seed.value))
    _samples = [_rng.choice(expansions_all) for _ in range(int(n_trials.value))]
    _emp_mean = sum(_samples) / len(_samples)
    _theory = (V + 1) / 2
    _true_mean = sum(expansions_all) / len(expansions_all)

    _fig, _ax = plt.subplots(figsize=(9, 4.6))
    _fig.patch.set_facecolor("#F5F7FA")
    _ax.set_facecolor("#F5F7FA")
    _ax.hist(_samples, bins=30, color="#4AA8A0", edgecolor="#0B6E6B", alpha=0.85)
    _ax.axvline(_emp_mean, color="#F0B429", lw=2.6,
                label=f"empirical mean = {_emp_mean:.0f}")
    _ax.axvline(_true_mean, color="#7A1E2C", ls="--", lw=1.8,
                label=f"true mean over all targets = {_true_mean:.0f}")
    _ax.axvline(_theory, color="#2B6CB0", ls=":", lw=1.8,
                label=f"(V+1)/2 = {_theory:.0f}")
    _ax.axvline(expansions_all[-1], color="#9AA5B1", ls="-", lw=1.2,
                label=f"worst case = {expansions_all[-1]}")
    _ax.set_xlabel("Sector-expansions to reach a random target", fontsize=9)
    _ax.set_ylabel("Frequency", fontsize=9)
    _ax.set_title(f"Average case over {int(n_trials.value):,} random searches",
                  fontsize=11, fontweight="bold", color="#0B1F3B")
    _ax.legend(fontsize=8, framealpha=0.9)
    _ax.grid(True, color="#C8D0DC", lw=0.4, alpha=0.7)
    plt.tight_layout()

    _frac = 100 * _true_mean / V
    mo.vstack([
        mo.callout(mo.md(
            f"**Empirical mean ≈ {_emp_mean:.0f} expansions** over "
            f"{int(n_trials.value):,} trials (true mean over all targets = "
            f"{_true_mean:.0f}; (V+1)/2 = {_theory:.0f}). On average a search explores "
            f"about **{_frac:.0f}% of the {V} sectors** before reaching the target. "
            f"Increase the trials and watch the empirical mean settle onto the true mean."
        ), kind="info"),
        _fig,
        mo.callout(mo.md(
            "Both the average and the worst case grow as **Θ(V)** here -- same growth "
            "class, different constant. That is the point to make in Part 2: averaging "
            "changes the *constant*, not the *order*."
        ), kind="neutral"),
    ])
    return


@app.cell
def s2b_input(SAVE_FILE_SUPP, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_SUPP):
        try:
            with open(SAVE_FILE_SUPP, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("S2B_avg", "")
        except Exception:
            pass
    resp_s2b = mo.ui.text_area(
        label="**[S2-B] Your average-case analysis**", value=_saved, rows=9,
        full_width=True,
        placeholder=(
            "Part 1 -- I assume the target is uniformly random across all V sectors\n"
            "  because ... (a clustered assumption would ...).\n\n"
            "Part 2 -- Empirical mean = ... expansions; (V+1)/2 = ...; worst = ... .\n"
            "  Average and worst are both Θ(V); averaging only changes the constant.\n\n"
            "Part 3 -- The average tells planners the *expected* response time, whereas\n"
            "  the worst case bounds the *guarantee*; both matter because ..."
        )
    )
    resp_s2b
    return (resp_s2b,)


@app.cell
def s2b_display(mo, resp_s2b):
    mo.callout(
        mo.md("**[S2-B] Saved:**\n\n" + resp_s2b.value) if resp_s2b.value.strip()
        else mo.md("*No response entered yet.*"), kind="success")
    return


# ======================================================================
# SECTION C -- SPACE COMPLEXITY
# ======================================================================
@app.cell
def s2c_header(mo):
    mo.md("""
---
## [S2-C] Space Complexity
*Criterion 5 / 6 deepener · Written response (approx. 100--180 words)*

> Time is not the only cost. CRUDY-1 has **limited on-board memory**, so the **space
> complexity** of your traversal matters. Space is the memory your algorithm holds at
> once -- usually some combination of the **visited** record, any **stored paths**, and a
> **frontier** (the sectors waiting to be explored).
>
> **BFS and DFS below are examples, not the expected answer.** Not every algorithm keeps
> an explicit frontier: a **recursive** traversal hides it in the call stack, and some
> designs keep **no frontier at all** (e.g. scanning a fixed grid/matrix, or marking
> cells in place). If your Memo 01 algorithm has no frontier model, your space complexity
> will **evolve differently** -- analyse *your own* structures rather than copying BFS/DFS.

**Address all four parts:**

**Part 1 -- Account for the structures *you actually use*.**
- `visited` / marking: a separate set is **O(V)**; marking cells **in place** can be
  **O(1)** extra.
- Frontier *(if any)*: an explicit BFS **queue** or DFS **stack** is **O(V)** worst case;
  a **recursive** DFS instead costs call-stack depth, **O(longest branch)**; an algorithm
  with **no frontier** has no such term at all.
- Stored paths: keeping a path *per frontier entry* (`path + [neighbour]`) is **O(V) per
  entry → O(V²)**. State whether your code does this.

**Part 2 -- Combine for *your* algorithm.**
Give the overall space bound. It may be **O(V)**, **O(V²)** if you copy paths, or as low
as **O(1) auxiliary** if you mark in place and hold no frontier -- whichever matches *your*
implementation.

**Part 3 -- Use the demo as a worked example.**
The demo plots frontier size over time for **BFS and DFS** as illustrations. Quote the
peak for each and explain them by *shape*: the BFS queue holds the current **ring** (peak
≈ maximum width), while the DFS stack holds the **unexplored branches along the current
deep path** (peak grows with depth). Then state **which model matches your algorithm** --
explicit queue, explicit stack, recursion depth, or none -- and what *its* peak memory
would be. On a sparse maze either BFS or DFS can win, so read the numbers, don't assume.

**Part 4 -- Real-world consequence.**
Use the memory estimator to state how much RAM *your* design needs at a city-scale site,
and whether that fits a small drone. This is a **Criterion 6** consequence in the space
dimension, not time.

---
    """)
    return


@app.cell
def s2c_controls(mo):
    bytes_per_node = mo.ui.slider(start=8, stop=256, step=8, value=64,
                                  label="Bytes stored per sector (node record)",
                                  show_value=True)
    big_V = mo.ui.slider(start=1000, stop=500000, step=1000, value=200000,
                         label="City-scale facility size V (for the RAM estimate)",
                         show_value=True)
    mo.vstack([mo.md("#### 🎛️ Space explorer"),
               mo.hstack([bytes_per_node, big_V], justify="start")])
    return (big_V, bytes_per_node)


@app.cell
def s2c_demo(V, big_V, bytes_per_node, bfs_frontier, dfs_max_depth,
             dfs_stack_sizes, mo, plt):
    _bfs_peak = max(bfs_frontier)
    _dfs_peak = max(dfs_stack_sizes)

    _fig, _ax = plt.subplots(figsize=(9, 4.6))
    _fig.patch.set_facecolor("#F5F7FA")
    _ax.set_facecolor("#F5F7FA")
    _ax.plot(range(len(bfs_frontier)), bfs_frontier, color="#2B6CB0", lw=1.8,
             label=f"BFS queue (peak {_bfs_peak})")
    _ax.plot(range(len(dfs_stack_sizes)), dfs_stack_sizes, color="#7A1E2C", lw=1.8,
             label=f"DFS stack (peak {_dfs_peak})")
    _ax.axhline(_bfs_peak, color="#2B6CB0", ls=":", lw=1.0)
    _ax.axhline(_dfs_peak, color="#7A1E2C", ls=":", lw=1.0)
    _ax.set_xlabel("Steps (sectors expanded)", fontsize=9)
    _ax.set_ylabel("Frontier size (sectors held in memory)", fontsize=9)
    _ax.set_title("Memory in use over time: BFS frontier vs DFS stack",
                  fontsize=11, fontweight="bold", color="#0B1F3B")
    _ax.legend(fontsize=8, framealpha=0.9)
    _ax.grid(True, color="#C8D0DC", lw=0.4, alpha=0.7)
    plt.tight_layout()

    # RAM estimate at city scale: O(V) visited + frontier dominates
    _bpn = int(bytes_per_node.value)
    _bigV = int(big_V.value)

    def _fmt_bytes(_b):
        for _u in ["B", "KB", "MB", "GB"]:
            if _b < 1024:
                return f"{_b:.1f} {_u}"
            _b /= 1024
        return f"{_b:.1f} TB"

    _linear = _fmt_bytes(_bpn * _bigV)          # O(V) implementation
    _quad = _fmt_bytes(_bpn * _bigV * _bigV)    # O(V^2) if paths copied

    mo.vstack([
        mo.callout(mo.md(
            f"**BFS and DFS as examples** (frontier-based traversals on your facility, "
            f"V = {V}): **BFS peak frontier = {_bfs_peak}** sectors, **DFS peak stack = "
            f"{_dfs_peak}**, deepest DFS branch = {dfs_max_depth}. Both are O(V) here. "
            f"If *your* algorithm uses **recursion**, compare against the deepest branch "
            f"(**{dfs_max_depth}**); if it keeps **no frontier**, neither curve applies "
            f"and your auxiliary space may be far smaller."
        ), kind="info"),
        _fig,
        mo.md(
            f"**RAM estimate at V = {_bigV:,} sectors, {_bpn} bytes/sector "
            f"(your model may match any row):**\n\n"
            f"| Space model | Class | Estimated memory |\n|---|---|---|\n"
            f"| Mark in place, no stored frontier | O(1) auxiliary | **a few bytes** |\n"
            f"| visited + frontier (queue / stack / recursion depth) | O(V) | **{_linear}** |\n"
            f"| A stored path per frontier entry | O(V²) | **{_quad}** |"
        ),
        mo.callout(mo.md(
            "Pick the row that matches *your* algorithm. A no-frontier / in-place design "
            "is tiny; an O(V) frontier design still fits; the O(V²) path-copying design "
            "explodes into **gigabytes-to-terabytes** at city scale and would never fit a "
            "drone. Whichever is yours, that scaling is your Part 4 consequence."
        ), kind="warn"),
    ])
    return


@app.cell
def s2c_input(SAVE_FILE_SUPP, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_SUPP):
        try:
            with open(SAVE_FILE_SUPP, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("S2C_space", "")
        except Exception:
            pass
    resp_s2c = mo.ui.text_area(
        label="**[S2-C] Your space-complexity analysis**", value=_saved, rows=10,
        full_width=True,
        placeholder=(
            "Part 1 -- Structures I actually use:\n"
            "  visited/marking: <O(V) set / O(1) in-place>; frontier: <explicit queue|stack\n"
            "  O(V) / recursion depth O(longest branch) / NONE>; path storage: <O(V^2) if I\n"
            "  copy paths / none>.\n\n"
            "Part 2 -- Overall space for MY algorithm: O(______).\n\n"
            "Part 3 -- Demo (BFS/DFS as examples): BFS peak = ..., DFS peak = ...,\n"
            "  deepest branch = ... . My algorithm's model is <queue / stack / recursion /\n"
            "  none>, so its peak memory is ... .\n\n"
            "Part 4 -- At V=200,000 my design needs ~... which <fits / does not fit> a small\n"
            "  drone; a path-copying O(V^2) design would need ~... ."
        )
    )
    resp_s2c
    return (resp_s2c,)


@app.cell
def s2c_display(mo, resp_s2c):
    mo.callout(
        mo.md("**[S2-C] Saved:**\n\n" + resp_s2c.value) if resp_s2c.value.strip()
        else mo.md("*No response entered yet.*"), kind="success")
    return


# ======================================================================
# SAVE + FOOTER
# ======================================================================
@app.cell
def save_controls(mo):
    save_btn = mo.ui.button(value=0, label="💾 Save All Supplementary Responses",
                            on_click=lambda v: v + 1)
    mo.vstack([
        mo.md("---\n### 💾 Save your responses"),
        mo.callout(mo.md(
            "Writes [S2-A], [S2-B] and [S2-C] to `responses_M02_supp.json`. "
            "Each save appends a timestamped entry."), kind="info"),
        save_btn,
    ])
    return (save_btn,)


@app.cell
def save_responses(SAVE_FILE_SUPP, datetime, json, mo, os,
                   resp_s2a, resp_s2b, resp_s2c, save_btn):
    if save_btn.value > 0:
        if os.path.exists(SAVE_FILE_SUPP):
            try:
                with open(SAVE_FILE_SUPP, "r") as _f:
                    _all = json.load(_f)
            except Exception:
                _all = []
        else:
            _all = []
        _all.append({
            "timestamp":  datetime.datetime.now().isoformat(),
            "S2A_best":   resp_s2a.value,
            "S2B_avg":    resp_s2b.value,
            "S2C_space":  resp_s2c.value,
        })
        with open(SAVE_FILE_SUPP, "w") as _f:
            json.dump(_all, _f, indent=2)
        _result = mo.callout(mo.md(
            f"✅ **Saved** at {datetime.datetime.now().strftime('%H:%M:%S')} "
            f"-- `{SAVE_FILE_SUPP}`"), kind="success")
    else:
        _result = mo.md("*Press Save above to record your responses.*")
    _result
    return


@app.cell
def footer(mo):
    mo.md("""
---
*End of Memo 02 supplementary workbook -- submit alongside your Memo 02 notebook.*

**Before submitting, check:**
- [ ] Same seed as your Memo 01 / 02 cover sheets.
- [ ] **[S2-A]** states whether your algorithm can terminate early, gives the Ω best case,
      and quotes the demo's best / Exit A / Exit B numbers.
- [ ] **[S2-B]** states the input distribution, quotes the empirical mean vs (V+1)/2, and
      notes that average and worst case share the same growth class.
- [ ] **[S2-C]** accounts for the structures *your* algorithm uses (visited, any
      frontier or recursion, path storage), states which model matches yours (explicit
      queue/stack, recursion depth, or none), gives an overall space bound, uses the
      BFS/DFS peaks as illustration, and gives a city-scale RAM consequence.
- [ ] All three responses saved to `responses_M02_supp.json`.

*Together with Memo 02 (worst case + consequences) these complete the full
best / average / worst / space complexity picture for your initial solution.*
    """)
    return


if __name__ == "__main__":
    app.run()
