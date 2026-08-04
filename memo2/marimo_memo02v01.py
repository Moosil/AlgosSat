import marimo

__generated_with = "0.21.0"
app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import random
    import math
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    from collections import deque
    import json
    import os
    import datetime

    SAVE_FILE_ORIG = "responses.json"      # Memo 01 responses (read-only reference)
    SAVE_FILE_M02  = "responses_M02.json"  # Memo 02 responses (written here)
    return (
        LinearSegmentedColormap,
        SAVE_FILE_M02,
        SAVE_FILE_ORIG,
        datetime,
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
    # Operation Emberlight -- Memo 02 Workbook
    ## Time Complexity of Your Initial Solution

    | Field | Value |
    |---|---|
    | **Name** | *(your name)* |
    | **Student number** | *(your number)* |
    | **Facility seed** | 19900811|
    | **Teacher** | *(teacher name)* |

    > **Field update -- corridors are becoming unstable.**
    > Post-seismic modelling shows corridors are **no longer equally traversable** --
    > each carries a structural-integrity cost (the same model introduced in Amendment
    > A2). The Rescue Authority needs to know **how long CRUDY-1's traversal will take**
    > as the Emberlight Complex grows, and whether these variable costs change the
    > picture. Before scaling up, we must analyse the **time complexity of the initial
    > traversal solution you designed in Memo 01** and its real-world consequences.

    > **Authentication note:** use the **same seed** as your Memo 01 workbook so your
    > facility, sector count (V) and corridor count (E) match your own.

    ---
    **What this memo assesses**

    | Label | Section | Criterion |
    |---|---|---|
    | `[M2-1]` | Action 2-1 -- Complexity Annotation of the Initial Solution | **Criterion 5a** |
    | `[M2-2]` | Action 2-2 -- Consequences & Growth Curve | **Criterion 6** |
    | `[M2-RUN]` | Implementation runner -- empirical operation count | *(supports M2-1)* |

    **How to use this workbook:**
    - Enter your seed to generate your unique **weighted** facility and its V / E counts.
    - Review your Memo 01 initial pseudocode in the read-only reference panel.
    - Complete the complexity annotation (Action 2-1) and consequences write-up (Action 2-2).
    - Use the runner to measure how many operations your traversal really performs.
    - Save your responses and submit at **Observation 5 / 6**.
    - For best / average / space complexity, complete `marimo_memo02_supp.py`.
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
        """Build a single-wing maze as a spanning tree of the grid."""
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

        wings = []
        for w in range(n_wings):
            wrng = random.Random(int_seed * 31 + w * 7919)
            wings.append(_build_wing(WING_COLS, WING_ROWS, wrng))

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
            'n_wings':    n_wings,
            'wing_names': wing_names,
            'wings':      wings,
            'wing_cols':  WING_COLS,
            'wing_rows':  WING_ROWS,
            'entry':      entry,
            'exit_a':     exit_a,
            'exit_b':     exit_b,
            'supplies':   supplies[:5],
            'junctions':  junctions,
        }

    fac = get_multi_wing_facility(seed_input.value)
    return fac, get_multi_wing_facility


@app.cell
def cost_model(fac, random, seed_input):
    """Apply the Amendment A2 cost models to the facility corridors.

    Wing Alpha (w=0): Uniform cost = 1.
    Wing Beta  (w=1): Depth-based cost = 1 + max(col1, col2) // 3.
    Wing Gamma / Delta (w>=2): Seed-randomised cost in [1, 5].
    Inter-wing junctions: cost = 1.
    """
    import copy

    def apply_cost_models(fac_in, int_seed):
        """Return a copy of fac_in with the A2 cost models applied to every corridor."""
        _wings = [copy.deepcopy(_w) for _w in fac_in['wings']]
        for _w, _wg in enumerate(_wings):
            if _w == 0:
                pass
            elif _w == 1:
                for (c1, r1), (c2, r2) in list(_wg.edges()):
                    _wg[c1, r1][c2, r2]['weight'] = 1 + max(c1, c2) // 3
            else:
                _crng = random.Random(int_seed * 41 + _w * 3331)
                for (c1, r1), (c2, r2) in list(_wg.edges()):
                    _wg[c1, r1][c2, r2]['weight'] = _crng.randint(1, 5)
        _out = dict(fac_in)
        _out['wings'] = _wings
        return _out

    int_seed = int(seed_input.value)
    n_wings  = fac['n_wings']
    fac_weighted = apply_cost_models(fac, int_seed)
    weighted_wings = fac_weighted['wings']

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
    return apply_cost_models, fac_weighted, wing_cost_summary


@app.cell
def drawing_utils_weighted(LinearSegmentedColormap, mcolors, plt):
    """Drawing utilities for the weighted multi-wing facility (from Amendment A2)."""

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

    return (draw_weighted_facility,)


@app.cell
def visualiser_weighted(
    draw_weighted_facility,
    fac_weighted,
    mo,
    seed_input,
    wing_cost_summary,
):
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
            "The graph your initial algorithm traverses. **E** = entry, **A/B** = exits, "
            "dashed lines = inter-wing junctions, stars = supplies. Corridor colour shows "
            "cost: **teal** = 1, **gold** = medium, **maroon** = 5 (junctions always 1). "
            "The sectors are the **V** nodes and the corridors are the **E** edges in your "
            "complexity analysis below."
        ), kind="info"),
        _fig,
        mo.md("### Cost Model Summary"),
        mo.md(_table_md),
    ])
    return


@app.cell
def facility_size(fac, mo, seed_input):
    """Compute V (sectors) and E (corridors) for the student's own facility."""
    _V = sum(wg.number_of_nodes() for wg in fac['wings'])
    _E = sum(wg.number_of_edges() for wg in fac['wings']) + len(fac['junctions'])
    _n_wings = fac['n_wings']

    fac_V = _V
    fac_E = _E

    _rows = [
        ("Wings in your facility", _n_wings),
        ("Sectors per wing (grid)", f"{fac['wing_cols']} x {fac['wing_rows']} = "
                                    f"{fac['wing_cols']*fac['wing_rows']}"),
        ("**V -- total sectors (nodes)**", f"**{_V}**"),
        ("Intra-wing corridors", sum(wg.number_of_edges() for wg in fac['wings'])),
        ("Inter-wing junction corridors", len(fac['junctions'])),
        ("**E -- total corridors (edges)**", f"**{_E}**"),
        ("**V + E (size of the graph)**", f"**{_V + _E}**"),
    ]
    _table = "| Quantity | Value |\n|---|---|\n" + "\n".join(
        f"| {k} | {v} |" for k, v in _rows
    )

    mo.vstack([
        mo.md(f"## 📐 Your Facility's Size -- Seed {int(seed_input.value)}"),
        mo.callout(mo.md(
            "Time complexity is expressed in terms of **V** (sectors / nodes) and "
            "**E** (corridors / edges) -- the input-size variables for your traversal. "
            "Use **your own numbers** below."
        ), kind="info"),
        mo.md(_table),
        mo.callout(mo.md(
            "Each wing is a **spanning tree** of a 10x10 grid, so every wing has 100 "
            "sectors and 99 corridors: **E ≈ V**, a **sparse** graph. The corridor "
            "*costs* (Amendment A2) change which path is cheapest, but they do **not** "
            "change how many sectors and corridors a plain BFS/DFS visits -- that is the "
            "subtlety Action 2-1 asks you to pin down."
        ), kind="warn"),
    ])
    return fac_E, fac_V


@app.cell
def original_responses_display(SAVE_FILE_ORIG, json, mo, os):
    """Show the Memo 01 initial pseudocode + algorithm as a read-only reference panel."""
    _keys = [
        ("C1 pseudocode", "Initial traversal pseudocode (Memo 01)"),
        ("C2 algorithm",  "Initial algorithm description (Memo 01)"),
    ]
    _items = {}
    if os.path.exists(SAVE_FILE_ORIG):
        try:
            with open(SAVE_FILE_ORIG, "r") as _f:
                _orig = json.load(_f)
            _latest = _orig[-1] if isinstance(_orig, list) and _orig else _orig
            for _k, _label in _keys:
                _val = _latest.get(_k, "*(not saved)*")
                _items[_label] = mo.md(f"```\n{_val}\n```")
        except Exception as _e:
            _items = {"Error": mo.md(f"*Could not load `{SAVE_FILE_ORIG}`: {_e}*")}
    else:
        _items = {
            "Note": mo.md(
                f"*`{SAVE_FILE_ORIG}` not found -- run your Memo 01 workbook and save "
                "your responses first, or paste your initial pseudocode into Action 2-1.*"
            )
        }

    mo.vstack([
        mo.md("""
    ---
    ## 📋 Your Memo 01 Initial Solution (Read-Only Reference)

    This is the algorithm whose **time complexity you must now analyse**.
    Do not edit it here -- your analysis goes in Action 2-1 below.
        """),
        mo.accordion(
            {"📋 Memo 01 initial pseudocode & algorithm (read-only)": mo.vstack(
                [mo.vstack([mo.md(f"**{lbl}**"), val]) for lbl, val in _items.items()]
            )}
        ),
        mo.callout(mo.md(
            f"If nothing appears, ensure `{SAVE_FILE_ORIG}` is in the **same folder** as "
            "this notebook, then re-open the workbook."
        ), kind="warn"),
    ])
    return


@app.cell
def exemplar_header(mo):
    mo.md("""
    ---
    ## 🧭 [M2-0] Worked Exemplars -- Two Algorithms, Two Complexity Classes

    Before analysing your own algorithm, work through the two exemplars below. They are run on a
    **fixed demonstration facility (seed 20260000)** -- *not* your facility -- so their operation
    counts are **not** the numbers you quote in Part 5 of your own analysis.

    Both exemplars solve *a* problem on the same facility. **Exemplar A** ignores the supply units
    and routes straight to the nearest exit. **Exemplar B** collects all five supply units first.
    They differ by a single design decision, and that decision changes the **complexity class** --
    not just the running time.

    > **Why two?** The most common error in this analysis is to *add* the cost of a repeated
    > search instead of *multiplying* by the number of repetitions. Reading A and B side by side
    > makes the difference visible: B runs the same kind of search **k + 1 times**, so its
    > k appears as a **factor**, not a term.
    """)
    return


@app.cell
def exemplar_facility(apply_cost_models, get_multi_wing_facility):
    """Fixed demonstration facility -- deliberately NOT a student seed."""
    DEMO_SEED = 20260000

    demo_fac = apply_cost_models(get_multi_wing_facility(DEMO_SEED), DEMO_SEED)

    demo_adj = {}
    for _w, _wing in enumerate(demo_fac['wings']):
        for (_c1, _r1), (_c2, _r2), _d in _wing.edges(data=True):
            _wt = _d.get('weight', 1)
            demo_adj.setdefault((_w, _c1, _r1), []).append(((_w, _c2, _r2), _wt))
            demo_adj.setdefault((_w, _c2, _r2), []).append(((_w, _c1, _r1), _wt))
    for (_w1, _c1, _r1), (_w2, _c2, _r2) in demo_fac['junctions']:
        demo_adj.setdefault((_w1, _c1, _r1), []).append(((_w2, _c2, _r2), 1))
        demo_adj.setdefault((_w2, _c2, _r2), []).append(((_w1, _c1, _r1), 1))

    demo_V = sum(_w.number_of_nodes() for _w in demo_fac['wings'])
    demo_E = (sum(_w.number_of_edges() for _w in demo_fac['wings'])
              + len(demo_fac['junctions']))
    demo_k = len(demo_fac['supplies'])
    return DEMO_SEED, demo_E, demo_V, demo_adj, demo_fac, demo_k


@app.cell
def exemplar_algorithms(demo_adj, demo_fac):
    """Both exemplars use the SAME operation-counting convention as the runner below:
    +1 per sector expanded (removed from the queue), +1 per corridor examined.
    """
    import heapq as _heapq
    from collections import deque as _deque

    def exemplar_a_bfs(fac_w, adj):
        """A -- breadth-first search, entry to nearest exit. Supplies ignored."""
        _start = fac_w['entry']
        _goals = {fac_w['exit_a'], fac_w['exit_b']}
        _ops, _seen, _prev = 0, {_start}, {_start: None}
        _q, _found = _deque([_start]), None
        while _q:
            _u = _q.popleft()
            _ops += 1                              # sector expanded
            if _u in _goals:
                _found = _u
                break
            for _v, _ in adj.get(_u, []):
                _ops += 1                          # corridor examined
                if _v not in _seen:
                    _seen.add(_v)
                    _prev[_v] = _u
                    _q.append(_v)
        _path, _cur = [], _found
        while _cur is not None:
            _path.append(_cur)
            _cur = _prev[_cur]
        return _path[::-1], _ops

    def _dijkstra_to_nearest(adj, src, targets):
        """One Dijkstra run, stopping at whichever target is reached first."""
        _dist, _prev, _done = {src: 0}, {src: None}, set()
        _pq, _ops = [(0, src)], 0
        while _pq:
            _d, _u = _heapq.heappop(_pq)
            if _u in _done:
                continue
            _done.add(_u)
            _ops += 1                              # sector expanded
            if _u in targets:
                return _u, _prev, _ops
            for _v, _wt in adj.get(_u, []):
                _ops += 1                          # corridor examined
                _nd = _d + _wt
                if _nd < _dist.get(_v, float('inf')):
                    _dist[_v] = _nd
                    _prev[_v] = _u
                    _heapq.heappush(_pq, (_nd, _v))
        return None, _prev, _ops

    def _trace(prev, target):
        _p, _cur = [], target
        while _cur is not None:
            _p.append(_cur)
            _cur = prev[_cur]
        return _p[::-1]

    def exemplar_b_greedy(fac_w, adj):
        """B -- repeatedly Dijkstra to the nearest uncollected supply, then to an exit."""
        _cur = fac_w['entry']
        _remaining = set(fac_w['supplies'])
        _route, _ops, _runs = [_cur], 0, 0
        while _remaining:
            _t, _prev, _o = _dijkstra_to_nearest(adj, _cur, _remaining)
            _ops += _o
            _runs += 1
            if _t is None:
                break
            _route += _trace(_prev, _t)[1:]
            _remaining.discard(_t)
            _cur = _t
        _t, _prev, _o = _dijkstra_to_nearest(
            adj, _cur, {fac_w['exit_a'], fac_w['exit_b']})
        _ops += _o
        _runs += 1
        if _t is not None:
            _route += _trace(_prev, _t)[1:]
        return _route, _ops, _runs

    path_a, ops_a = exemplar_a_bfs(demo_fac, demo_adj)
    path_b, ops_b, runs_b = exemplar_b_greedy(demo_fac, demo_adj)

    collected_a = len(set(path_a) & set(demo_fac['supplies']))
    collected_b = len(set(path_b) & set(demo_fac['supplies']))
    return (collected_a, collected_b, ops_a, ops_b, path_a, path_b, runs_b)


@app.cell
def exemplar_pseudocode(mo):
    mo.md(r"""
    ### The two algorithms in VCAA pseudocode

    **Exemplar A -- Nearest Exit (supplies ignored)**

    ```
    ExitOnlyBFS(graph: Graph, entry: Vertex, exits: Set) -> Path:
    1  frontier ← Queue containing entry              O(1)
    2  seen     ← Set containing entry                O(1)
    3  While frontier is not empty Do                 loop runs at most V times
    4      current ← frontier.dequeue()               O(1) (V times)
    5      If current in exits Do                     O(1)
    6          Return ReconstructPath(current)        O(V) (once)
    7      Foreach neighbour of current Do            2E times in total
    8          If neighbour not in seen Do            O(1)
    9              seen.add(neighbour)                O(1)
    10             frontier.enqueue(neighbour)        O(1)
    11 Return empty                                   O(1)
    ```

    Line 3 contributes **V**, line 7 contributes **2E** across the whole run, and the two are
    **added** because the neighbour loop is bounded by the total number of corridors, not
    re-run from scratch per sector. Tight upper bound: **O(V + E)**.

    ---

    **Exemplar B -- Greedy Nearest Supply (collects all k, then exits)**

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

    Line 5 is a **complete search** that costs O((V + E) log V), and line 4 runs it **k times**.
    A loop that repeats a search **multiplies**; it does not add. With the final run to an exit
    that is k + 1 searches, so the tight upper bound is **O(k(V + E) log V)**.

    > **The trap.** Writing "O(V + E) for the search, plus O(k) for the supply loop, so
    > O(V + E + k)" is the single most common error in this task. Check every loop: is the work
    > *inside* it a constant-time step, or a whole search?
    """)
    return


@app.cell
def exemplar_results(
    collected_a,
    collected_b,
    demo_E,
    demo_V,
    demo_fac,
    demo_k,
    draw_weighted_facility,
    mo,
    ops_a,
    ops_b,
    path_a,
    path_b,
    runs_b,
):
    _env = demo_V + 2 * demo_E
    _env_b = (demo_k + 1) * _env

    _fig_a = draw_weighted_facility(
        demo_fac, highlight_path=path_a,
        title=f"Exemplar A -- nearest exit · {ops_a} operations · {collected_a}/{demo_k} supplies")
    _fig_b = draw_weighted_facility(
        demo_fac, highlight_path=path_b,
        title=f"Exemplar B -- greedy collection · {ops_b} operations · {collected_b}/{demo_k} supplies")

    _table = mo.md(f"""
    | | **A -- nearest exit** | **B -- greedy collection** |
    |---|---|---|
    | Supplies collected | **{collected_a} of {demo_k}** | **{collected_b} of {demo_k}** |
    | Searches performed | 1 | {runs_b} (= k + 1) |
    | Operations measured | **{ops_a}** | **{ops_b}** |
    | Tight upper bound | **O(V + E)** | **O(k(V + E) log V)** |
    | Envelope for that bound | V + 2E = {_env} | (k+1)(V + 2E) = {_env_b} |
    | Inside its own envelope? | {'yes' if ops_a <= _env else 'no'} | {'yes' if ops_b <= _env_b else 'no'} |

    Demonstration facility: **V = {demo_V}**, **E = {demo_E}**, **k = {demo_k}** supply units
    across {demo_fac['n_wings']} wings.
    """)

    _read = mo.callout(mo.md(f"""
    **Three things to notice.**

    1. **B is only about {ops_b / max(ops_a, 1):.1f}x A, not {demo_k + 1}x.** Each Dijkstra run
       *stops early* at the nearest target instead of exploring the whole facility, so the true
       count sits well under the bound. That is exactly what "upper bound" means -- and why
       quoting a bound is not the same as predicting a measurement.

    2. **B is above A's envelope ({ops_b} > {_env}) and that is correct, not a bug.** An
       algorithm in a larger complexity class *should* exceed the smaller class's envelope. When
       you compare your own measurement in Part 5, compare it against the envelope for **your**
       bound.

    3. **A is faster and useless.** It reaches an exit having collected nothing, so it does not
       solve the Memo 01 problem at all. Speed is only meaningful once the algorithm is correct
       -- a point worth making in Action 2-2.
    """), kind="info")

    mo.vstack([_table, _fig_a, _fig_b, _read])
    return


@app.cell
def exemplar_contrast_input(SAVE_FILE_M02, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_M02):
        try:
            with open(SAVE_FILE_M02, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("M20_contrast", "")
        except Exception:
            pass

    resp_m20 = mo.ui.text_area(
        label="**[M2-0] Your algorithm against the exemplars** (approx. 60--100 words)",
        value=_saved, rows=7, full_width=True,
        placeholder=(
            "Which exemplar is my algorithm closer to, and why:\n"
            "  ...\n\n"
            "One way MY bound differs from that exemplar's, and the line of MY pseudocode\n"
            "that causes the difference:\n"
            "  ..."
        )
    )
    mo.vstack([
        mo.md("**Required before Action 2-1.** Answering this from the exemplars alone is not "
              "possible -- you must name a line of *your own* pseudocode."),
        resp_m20,
    ])
    return (resp_m20,)


@app.cell
def exemplar_contrast_display(mo, resp_m20):
    mo.callout(
        mo.md("**[M2-0] Saved response:**\n\n" + resp_m20.value)
        if resp_m20.value.strip() else mo.md("*No response entered yet.*"),
        kind="success"
    )
    return


@app.cell
def section_header(mo):
    mo.md("""
    ---
    ## ✏️ Memo 02 Responses
    Complete both actions below. Your analysis must refer to **your own facility's V and E**
    (shown above) and to **your own Memo 01 algorithm**.
    """)
    return


@app.cell
def action_m21_header(mo):
    mo.md("""
    ---
    ### [M2-1] Action 2-1 -- Complexity Annotation of the Initial Solution
    *Criterion 5a · Written response (approx. 100--200 words)*

    > Determine the **time complexity of your initial Memo 01 traversal algorithm** and
    > express it as a **tight upper bound** in terms of V and E. The bound is whatever *your*
    > implementation produces -- it is **not** guaranteed to be O(V + E); the marks reward
    > *precision in identifying the complexity of each pseudocode element and combining
    > these logically*, not reciting a standard result.

    **Address all five parts:**

    **Part 1 -- Annotate the elements.**
    State the time complexity of each major element of your pseudocode: the outer queue/stack
    loop, the inner neighbour loop, and each operation (enqueue/dequeue/push/pop, `visited`
    lookup, marking visited). Give each in terms of V, E, or O(1).

    **Part 2 -- Handle abstraction and recursion.**
    If your algorithm calls a **sub-procedure** (`traverse_wing`, `expand`, `neighbours`) or
    uses **recursion**, state that unit's complexity and how many times it is invoked, making
    clear you are not double-counting.

    **Part 3 -- Combine to a tight upper bound** for *your* algorithm as *you* implemented it.
    There is no single answer to copy.

    **Part 4 -- Do the variable costs change the class?**
    The Amendment A2 corridor **costs** are now on the map. Explain whether introducing
    variable edge weights changes your algorithm's time-complexity **class**. (For BFS/DFS
    *reachability* it does not -- weights are just data attached to edges. Finding the
    minimum-**cost** path, however, needs Dijkstra at **O((V + E) log V)** -- a real change.)

    **Part 5 -- Substitute your numbers.**
    Using your facility's V and E above, state the approximate number of basic operations
    *your* bound implies, and check it against the runner's measured count below.

    ---
    """)
    return


@app.cell
def action_m21_input(SAVE_FILE_M02, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_M02):
        try:
            with open(SAVE_FILE_M02, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("M21_complexity", "")
        except Exception:
            pass

    resp_m21 = mo.ui.text_area(
        label="**[M2-1] Your complexity annotation (tight upper bound)**",
        value=_saved, rows=15, full_width=True,
        placeholder=(
            "Part 1 -- Element-by-element (use YOUR pseudocode):\n"
            "  Outer queue/stack loop: each of the V sectors processed once -> O(V).\n"
            "  ...\n"
            "  ...\n\n"
            "Part 2 -- Abstraction / recursion:\n"
            "  traverse_wing(...) invoked once per ...\n\n"
            "Part 3 -- Combine to MY tight upper bound:\n"
            "  Because I used ...\n"
            "  ... the loops <sum/multiply> -> O(______).\n\n"
            "Part 4 -- Variable costs:\n"
            "  Adding weights does NOT change ... because\n"
            "  weights are ....\n\n"
            "Part 5 -- My numbers:\n"
            "  V=..., E=..., so my bound implies ~... ops; runner measured ... ."
        )
    )
    resp_m21
    return (resp_m21,)


@app.cell
def action_m21_display(mo, resp_m21):
    mo.callout(
        mo.md("**[M2-1] Saved response:**\n\n" + resp_m21.value)
        if resp_m21.value.strip() else mo.md("*No response entered yet.*"),
        kind="success"
    )
    return


@app.cell
def runner_header(mo):
    mo.md("""
    ---
    ### [M2-RUN] Implementation Runner -- Measure Your Operation Count
    *Supports Criterion 5a -- empirical check of your analysis*

    > Run a traversal on **your** facility. The runner counts the basic operations
    > (sector-expansions + corridor-examinations) and overlays the path on the map, so you
    > can compare the **measured** count with the **predicted** O(V + E) from Action 2-1.

    The default below is an instrumented BFS that stops at the nearest exit. **Replace it with
    your own Memo 01 algorithm** to measure *its* behaviour. Your code must define
    `solution_path` (a list of `(wing, col, row)` tuples) and `op_count` (an integer).

    Available variable: `fac_weighted` -- `['wings']` (weighted graphs), `['entry']`,
    `['exit_a']`, `['exit_b']`, `['junctions']` (each junction edge has cost 1), and
    `['supplies']` -- the list of `(wing, col, row)` supply units **S1-S5**. If your algorithm
    collects supplies, use `fac_weighted['supplies']`; the default BFS below ignores them,
    which is exactly the difference between Exemplar A and Exemplar B above.
    """)
    return


@app.cell
def runner_editor(SAVE_FILE_M02, json, mo, os):
    _saved_code = ""
    if os.path.exists(SAVE_FILE_M02):
        try:
            with open(SAVE_FILE_M02, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved_code = _d[-1].get("M2_run_code", "")
        except Exception:
            pass

    run_code = mo.ui.code_editor(
        value=_saved_code or (
            "from collections import deque\n\n"
            "# Build flat adjacency (initial BFS treats every corridor uniformly --\n"
            "# the A2 costs are ignored here because plain reachability does not use them).\n"
            "adj = {}\n"
            "for w, wing in enumerate(fac_weighted['wings']):\n"
            "    for (c1, r1), (c2, r2) in wing.edges():\n"
            "        adj.setdefault((w, c1, r1), []).append((w, c2, r2))\n"
            "        adj.setdefault((w, c2, r2), []).append((w, c1, r1))\n"
            "for (w1, c1, r1), (w2, c2, r2) in fac_weighted['junctions']:\n"
            "    adj.setdefault((w1, c1, r1), []).append((w2, c2, r2))\n"
            "    adj.setdefault((w2, c2, r2), []).append((w1, c1, r1))\n\n"
            "start = fac_weighted['entry']\n"
            "goals = {fac_weighted['exit_a'], fac_weighted['exit_b']}\n\n"
            "# Instrumented BFS -- counts operations\n"
            "op_count = 0\n"
            "visited = {start}\n"
            "prev = {start: None}\n"
            "q = deque([start])\n"
            "found = None\n"
            "while q:\n"
            "    u = q.popleft()\n"
            "    op_count += 1            # one sector expanded\n"
            "    if u in goals:\n"
            "        found = u\n"
            "        break\n"
            "    for v in adj.get(u, []):\n"
            "        op_count += 1        # one corridor examined\n"
            "        if v not in visited:\n"
            "            visited.add(v)\n"
            "            prev[v] = u\n"
            "            q.append(v)\n\n"
            "# Reconstruct the path\n"
            "solution_path = []\n"
            "cur = found\n"
            "while cur is not None:\n"
            "    solution_path.append(cur)\n"
            "    cur = prev[cur]\n"
            "solution_path.reverse()\n"
        ),
        language="python",
        min_height=300,
    )
    run_btn = mo.ui.run_button(label="▶ Run my traversal and count operations")
    mo.vstack([
        mo.md("**Write your implementation below, then click Run:**"),
        run_code,
        run_btn,
    ])
    return run_btn, run_code


@app.cell
def runner_output(
    draw_weighted_facility,
    fac_E,
    fac_V,
    fac_weighted,
    mo,
    run_btn,
    run_code,
    seed_input,
):
    if run_btn.value:
        _ns = {'fac_weighted': fac_weighted, 'solution_path': None, 'op_count': None}
        try:
            exec(run_code.value, _ns)
            _path = _ns.get('solution_path')
            _ops = _ns.get('op_count')
            if _path and len(_path) > 1:
                _fig = draw_weighted_facility(
                    fac_weighted, highlight_path=_path,
                    title=(f"Traversal -- Seed {int(seed_input.value)} · "
                           f"{_ops} operations measured")
                )
                _vpe = fac_V + fac_E
                _env = fac_V + 2 * fac_E   # each undirected corridor examined from both ends

                # Which envelope applies depends on what the algorithm actually did.
                # A single-search algorithm belongs in O(V + E); one that collects supplies
                # runs a search per supply and belongs in O(k(V + E)) -- comparing the second
                # against the first would wrongly flag a correct solution as broken.
                _supplies = fac_weighted.get('supplies', [])
                _hit = len(set(_path) & set(_supplies))
                _k = len(_supplies)
                _collects = _hit > 0
                _env_used = (_k + 1) * _env if _collects else _env
                _class_used = "O(k(V + E))" if _collects else "O(V + E)"
                _within = (_ops is not None and _ops <= _env_used)

                if _collects:
                    _scope = (
                        f"Your path reaches **{_hit} of the {_k}** supply units, so this is a "
                        f"**collecting** traversal: it runs a search per supply, which puts it "
                        f"in **O(k(V + E))**, not O(V + E). The envelope for that class is "
                        f"**(k + 1)(V + 2E) = {_env_used}**."
                    )
                else:
                    _scope = (
                        f"Your path reaches **no supply units**, so this is an "
                        f"**exit-only** traversal in **O(V + E)** -- like Exemplar A. The "
                        f"envelope is **V + 2E = {_env}**. If your Memo 01 algorithm was "
                        f"*meant* to collect supplies, that objective is currently unmet: "
                        f"a fast measurement here is not evidence of a correct solution."
                    )
                _verdict = (f"inside the {_class_used} envelope" if _within
                            else f"ABOVE the {_class_used} envelope -- check your algorithm")
                _result = mo.vstack([
                    mo.callout(mo.md(
                        f"✅ **Done.** Measured **{_ops}** basic operations · "
                        f"{len(_path)} nodes on the path · "
                        f"**{_hit}/{_k}** supply units collected.\n\n"
                        f"Your facility has **V + E = {_vpe}**. A full BFS/DFS examines "
                        f"each corridor from **both** ends, so a single search scales as "
                        f"**V + 2E = {_env}** -- still **O(V + E)**, just with a larger "
                        f"constant.\n\n{_scope}\n\n"
                        f"Your measured **{_ops}** is {_verdict}. "
                        f"(A count well below the envelope means your search **stopped early** "
                        f"rather than exploring the whole facility -- an upper bound is not a "
                        f"prediction of the exact count.)"
                    ), kind="success"),
                    _fig,
                    mo.md(
                        "**Compare with Action 2-1:** does your predicted operation count "
                        "match this measurement? Quote both numbers in Part 5."
                    ),
                ])
            elif _path is not None:
                _result = mo.callout(mo.md(
                    "⚠️ `solution_path` is empty or has one node. Check your algorithm."),
                    kind="warn")
            else:
                _result = mo.callout(mo.md(
                    "⚠️ `solution_path` was not defined. Assign it before the end."),
                    kind="warn")
        except Exception:
            import traceback as _tb
            _result = mo.callout(mo.md(
                f"❌ **Error in your code:**\n\n```\n{_tb.format_exc()}\n```"),
                kind="danger")
    else:
        _result = mo.callout(mo.md(
            "Click **▶ Run** above to execute your traversal and measure its operations."),
            kind="neutral")
    _result
    return


@app.cell
def action_m22_header(mo):
    mo.md("""
    ---
    ### [M2-2] Action 2-2 -- Consequences for the Real-World Mission
    *Criterion 6 · Written response (approx. 100--200 words)*

    > Explain the **real-world consequences** of *your* algorithm's time complexity (the
    > bound you derived in Action 2-1) for CRUDY-1's mission. Use the **growth-curve plot
    > below** -- set the "your algorithm" dropdown to your own class -- to support your
    > argument with concrete input sizes.

    **Address all three parts:**

    **Part 1 -- How running time grows.**
    Describe how *your* algorithm's running time grows as the facility (input size) increases.
    Contrast your class with a worse one (e.g. O(V²) or O(2^V)) using the plot -- state what
    happens to each at a **large** facility (e.g. a city-scale disaster site with hundreds of
    thousands of sectors).

    **Part 2 -- Practical input sizes.**
    Identify the **practical input sizes** CRUDY-1 must handle (your small facility now vs a
    realistic full-scale rescue site). Using the runtime estimate in the plot, state roughly
    how long your algorithm would take at each scale and whether that is acceptable for a
    **time-critical extraction**.

    **Part 3 -- Suitability to the problem's requirements.**
    Conclude whether your initial solution is **suitable** for the mission, and under what
    conditions it would stop being suitable (e.g. if the cost model forced a more expensive
    algorithm like Dijkstra, or if the facility grew beyond some size).

    ---
    """)
    return


@app.cell
def growth_curve_controls(mo):
    _all_classes = ["O(1)", "O(log V)", "O(V)", "O(V + E)", "O(V log V)",
                    "O(k(V + E))", "O(V^2)", "O(2^V)"]
    my_class = mo.ui.dropdown(
        options=_all_classes, value="O(V + E)",
        label="Which class is YOUR algorithm? (the bound you derived in Action 2-1)",
    )
    classes = mo.ui.multiselect(
        options=_all_classes, value=["O(V + E)", "O(V^2)", "O(2^V)"],
        label="Other classes to compare against",
    )
    max_v = mo.ui.slider(start=10, stop=200000, step=10, value=2000,
                         label="Maximum facility size (V) on the x-axis", show_value=True)
    log_y = mo.ui.checkbox(value=True, label="Logarithmic y-axis (recommended)")
    k_targets = mo.ui.slider(start=1, stop=20, step=1, value=5,
                             label="k = number of supplies/targets (only O(k(V + E)))",
                             show_value=True)
    ops_per_sec = mo.ui.dropdown(
        options={"1 million ops/sec (1e6)": 1e6, "100 million ops/sec (1e8)": 1e8,
                 "1 billion ops/sec (1e9)": 1e9},
        value="100 million ops/sec (1e8)",
        label="Assumed machine speed (for the runtime estimate)")
    mo.vstack([
        mo.md("#### 🎛️ Growth-curve controls"),
        mo.callout(mo.md(
            "Set **YOUR algorithm's class** to whatever you derived in Action 2-1 -- it is "
            "highlighted in gold below. If you are unsure, that is a sign Action 2-1 is "
            "not finished yet."), kind="warn"),
        my_class,
        mo.hstack([classes, log_y], justify="start"),
        max_v,
        k_targets,
        ops_per_sec,
    ])
    return classes, k_targets, log_y, max_v, my_class, ops_per_sec


@app.cell
def growth_curve_plot(
    classes,
    fac_E,
    fac_V,
    k_targets,
    log_y,
    math,
    max_v,
    mo,
    my_class,
    ops_per_sec,
    plt,
):
    _maxv = int(max_v.value)
    _k = int(k_targets.value)
    _n = 60
    _xs = [max(1, int(_maxv * i / _n)) for i in range(1, _n + 1)]

    def _Eapprox(v):
        return v

    _funcs = {
        "O(1)":         lambda v: 1.0,
        "O(log V)":     lambda v: math.log2(max(v, 2)),
        "O(V)":         lambda v: float(v),
        "O(V + E)":     lambda v: float(v + _Eapprox(v)),
        "O(V log V)":   lambda v: v * math.log2(max(v, 2)),
        "O(k(V + E))":  lambda v: float(_k * (v + _Eapprox(v))),
        "O(V^2)":       lambda v: float(v) ** 2,
        "O(2^V)":       lambda v: 2.0 ** min(v, 60),
    }
    _colors = {
        "O(1)": "#9AA5B1", "O(log V)": "#4AA8A0", "O(V)": "#0B6E6B",
        "O(V + E)": "#3182CE", "O(V log V)": "#2B6CB0", "O(k(V + E))": "#0B6E6B",
        "O(V^2)": "#B7791F", "O(2^V)": "#7A1E2C",
    }
    _GOLD = "#F0B429"
    _mine = my_class.value
    _to_plot = [_mine] + [c for c in classes.value if c != _mine]

    _fig, _ax = plt.subplots(figsize=(9, 5.2))
    _fig.patch.set_facecolor("#F5F7FA")
    _ax.set_facecolor("#F5F7FA")
    for _name in _to_plot:
        _ys = [_funcs[_name](v) for v in _xs]
        _is_mine = (_name == _mine)
        _ax.plot(_xs, _ys,
                 label=(_name + "  [your algorithm]") if _is_mine else _name,
                 color=_GOLD if _is_mine else _colors[_name],
                 lw=3.6 if _is_mine else 1.8, zorder=5 if _is_mine else 3,
                 solid_capstyle="round")

    _ystar = _funcs[_mine](fac_V)
    _ax.scatter([fac_V], [_ystar], color=_GOLD, edgecolor="#7A1E2C", zorder=6, s=80)
    _ax.annotate(f"your facility\nV={fac_V}, E={fac_E}\n{_mine} ≈ {_ystar:.0f} ops",
                 xy=(fac_V, _ystar), xytext=(12, 14), textcoords="offset points",
                 fontsize=8, color="#0B1F3B",
                 arrowprops=dict(arrowstyle="->", color="#7A1E2C", lw=1.0))

    if log_y.value:
        _ax.set_yscale("log")
        _ax.set_ylabel("Basic operations (log scale)", fontsize=9)
    else:
        _ax.set_ylabel("Basic operations", fontsize=9)
    _ax.set_xlabel("Facility size V (number of sectors)", fontsize=9)
    _ax.set_title("How running time grows with facility size", fontsize=11,
                  fontweight="bold", color="#0B1F3B")
    _ax.grid(True, which="both", color="#C8D0DC", lw=0.4, alpha=0.7)
    _ax.legend(fontsize=8, framealpha=0.9, loc="upper left")
    plt.tight_layout()

    _speed = ops_per_sec.value

    def _fmt_time(_secs):
        if _secs < 1e-3:
            return f"{_secs*1e6:.1f} µs"
        if _secs < 1:
            return f"{_secs*1e3:.1f} ms"
        if _secs < 60:
            return f"{_secs:.2f} s"
        if _secs < 3600:
            return f"{_secs/60:.1f} min"
        if _secs < 86400:
            return f"{_secs/3600:.1f} hours"
        if _secs < 3.15e7:
            return f"{_secs/86400:.1f} days"
        _yrs = _secs / 3.15e7
        if _yrs > 1e9:
            return f"{_yrs:.1e} years (longer than the age of the universe)"
        return f"{_yrs:.1e} years"

    _rows = []
    for _name in _to_plot:
        _ops = _funcs[_name](_maxv)
        _tag = " **(yours)**" if _name == _mine else ""
        _rows.append(f"| {_name}{_tag} | {_ops:.3g} | {_fmt_time(_ops / _speed)} |")
    _rt_table = (
        f"**Estimated time at V = {_maxv:,} sectors, {int(_speed):,} ops/sec:**\n\n"
        "| Complexity | Basic operations | Estimated time |\n|---|---|---|\n"
        + "\n".join(_rows)
    )

    mo.vstack([
        mo.callout(mo.md(
            f"**Gold = your algorithm ({_mine}).** Set this with the dropdown above to "
            "match Action 2-1. On a log y-axis a near-straight line scales gracefully, "
            "while curves that bend upward (O(V²), O(2^V)) become infeasible -- that gap "
            "*is* the real-world consequence."), kind="info"),
        _fig,
        mo.md(_rt_table),
        mo.callout(mo.md(
            "Use specific numbers from this table in Action 2-2, comparing "
            f"**your {_mine}** against a worse class."), kind="neutral"),
    ])
    return


@app.cell
def action_m22_input(SAVE_FILE_M02, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_M02):
        try:
            with open(SAVE_FILE_M02, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("M22_consequences", "")
        except Exception:
            pass

    resp_m22 = mo.ui.text_area(
        label="**[M2-2] Your consequences & suitability discussion**",
        value=_saved, rows=12, full_width=True,
        placeholder=(
            "Part 1 -- Growth (use YOUR class from Action 2-1):\n\n"

            "Part 2 -- Practical input sizes:\n\n"

            "Part 3 -- Suitability:\n\n"

        )
    )
    resp_m22
    return (resp_m22,)


@app.cell
def action_m22_display(mo, resp_m22):
    mo.callout(
        mo.md("**[M2-2] Saved response:**\n\n" + resp_m22.value)
        if resp_m22.value.strip() else mo.md("*No response entered yet.*"),
        kind="success"
    )
    return


@app.cell
def save_controls(mo):
    save_btn = mo.ui.button(value=0, label="💾 Save All Memo 02 Responses",
                            on_click=lambda v: v + 1)
    mo.vstack([
        mo.md("---\n### 💾 Save your responses"),
        mo.callout(mo.md(
            "Writes [M2-1], [M2-2] and your runner code to `responses_M02.json`. "
            "Each save appends a timestamped entry."), kind="info"),
        save_btn,
    ])
    return (save_btn,)


@app.cell
def save_responses(
    SAVE_FILE_M02,
    datetime,
    json,
    mo,
    os,
    resp_m20,
    resp_m21,
    resp_m22,
    run_code,
    save_btn,
):
    if save_btn.value > 0:
        if os.path.exists(SAVE_FILE_M02):
            try:
                with open(SAVE_FILE_M02, "r") as _f:
                    _all = json.load(_f)
            except Exception:
                _all = []
        else:
            _all = []

        _all.append({
            "timestamp":        datetime.datetime.now().isoformat(),
            "M20_contrast":     resp_m20.value,
            "M21_complexity":   resp_m21.value,
            "M22_consequences": resp_m22.value,
            "M2_run_code":      run_code.value,
        })

        with open(SAVE_FILE_M02, "w") as _f:
            json.dump(_all, _f, indent=2)

        _result = mo.callout(mo.md(
            f"✅ **Saved** at {datetime.datetime.now().strftime('%H:%M:%S')} "
            f"-- `{SAVE_FILE_M02}`"), kind="success")
    else:
        _result = mo.md("*Press Save above to record your responses.*")
    _result
    return


@app.cell
def footer(mo):
    mo.md("""
    ---
    *End of Memo 02 workbook -- submit alongside your Memo 01 notebook at **Observation 5 / 6**.*

    **Before submitting, check:**
    - [ ] Your seed matches your Memo 01 cover sheet (so V and E are your own).
    - [ ] **[M2-1]** identifies the complexity of each pseudocode element, handles any
      sub-procedure / recursion without double-counting, combines to a **tight upper
      bound for your implementation**, addresses whether variable costs change the class,
      and substitutes your numbers.
    - [ ] **[M2-RUN]** runs without errors and the measured operation count is consistent
      with your predicted bound.
    - [ ] **[M2-2]** discusses growth, **practical input sizes** with concrete runtime
      estimates, and **suitability** to a time-critical extraction.
    - [ ] All responses saved to `responses_M02.json`.

    *Best / average / space complexity are covered in `marimo_memo02_supp.py`.
    Memo 03 will introduce load-sensitive corridor costs, requiring an improved algorithm.*
    """)
    return


if __name__ == "__main__":
    app.run()
