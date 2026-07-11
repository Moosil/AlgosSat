import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from collections import deque
    import json
    import os
    import datetime
    import textwrap

    SAVE_FILE_ORIG = "responses.json"       # Memo 01 responses (read-only reference)
    SAVE_FILE_A01  = "responses_A01.json"   # Amendment A1 responses (written here)
    return (
        SAVE_FILE_A01,
        SAVE_FILE_ORIG,
        datetime,
        deque,
        json,
        mo,
        mpatches,
        nx,
        os,
        plt,
        random,
        textwrap,
    )


@app.cell
def header(mo):
    mo.md("""
    # Operation Emberlight -- Amendment Memo A1 Workbook

    | Field | Value |
    |---|---|
    | **Name** | *(your name)* |
    | **Student number** | *(your number)* |
    | **Facility seed** | *(enter below -- same as Memo 01)* |
    | **Teacher** | *(teacher name)* |

    > **New intelligence has been received.**
    > The Emberlight Complex is larger than initially assessed.
    > It is a network of **multiple connected research wings**.
    > This workbook revises your Memo 01 responses in light of Amendment Memo A1.

    > **Authentication note:** Use the **same seed** as your Memo 01 workbook.
    > Your multi-wing facility is uniquely generated from that seed.
    > Do not change it after your first submission.

    ---
    **How to use this workbook:**
    - Enter your seed below to generate your unique multi-wing facility.
    - Review your original Memo 01 responses in the reference section.
    - Complete the revision cells for Actions 1–4 (labelled `[A1-REVISED]` through `[A4-REVISED]`).
    - Save your responses using the Save button at the bottom.
    - Submit this notebook alongside your Memo 01 workbook at **Observation 4**.
    """)
    return


@app.cell
def seed_cell(mo):
    seed_input = mo.ui.number(
        value=12345,
        start=0,
        stop=99999999,
        step=1,
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
        n_wings   = 2 + (int_seed % 3)          # 2, 3, or 4 wings from seed
        wing_names = ['Alpha', 'Beta', 'Gamma', 'Delta'][:n_wings]

        # Build each wing from a deterministic derived seed
        wings = []
        for w in range(n_wings):
            wrng = random.Random(int_seed * 31 + w * 7919)
            wings.append(_build_wing(WING_COLS, WING_ROWS, wrng))

        # Inter-wing junctions: 2 corridors per adjacent wing pair
        # Each junction connects (w, WING_COLS-1, r) to (w+1, 0, r)
        junctions = []
        for w in range(n_wings - 1):
            jrng = random.Random(int_seed * 17 + w * 5003)
            rows_avail = list(range(2, WING_ROWS - 2))
            jrng.shuffle(rows_avail)
            r1, r2 = sorted(rows_avail[:2])
            junctions.append(((w, WING_COLS - 1, r1), (w + 1, 0, r1)))
            junctions.append(((w, WING_COLS - 1, r2), (w + 1, 0, r2)))

        # Fixed entry and exits
        entry  = (0, 0, 0)
        exit_a = (n_wings - 1, WING_COLS - 1, WING_ROWS - 1)
        exit_b = (n_wings - 1, WING_COLS - 1, 0)

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
    return (fac,)


@app.cell
def drawing_utils_multi(mpatches, plt):
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
    COL_JUNCTION = '#7A1E2C'
    _GAP = 3  # grid-unit gap between wings in the visualisation

    def draw_multi_wing(fac, highlight_path=None, node_colors=None,
                        supply_collected=None, title="Multi-Wing Facility"):
        wc = fac['wing_cols']
        wr = fac['wing_rows']
        nw = fac['n_wings']
        total_w = nw * wc + (nw - 1) * _GAP

        fig_w = max(10, total_w * 0.58)
        fig_h = max(5, wr * 0.58 + 1.2)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.set_facecolor(COL_BG)
        fig.patch.set_facecolor(COL_BG)

        def xoff(w):
            return w * (wc + _GAP)

        # Draw each wing
        for w, wing in enumerate(fac['wings']):
            ox = xoff(w)

            # Grid lines
            for c in range(wc + 1):
                ax.plot([ox + c, ox + c], [0, wr],
                        color=COL_GRID, lw=0.4, zorder=1)
            for r in range(wr + 1):
                ax.plot([ox, ox + wc], [r, r],
                        color=COL_GRID, lw=0.4, zorder=1)

            # Wing border
            ax.add_patch(plt.Rectangle(
                (ox, 0), wc, wr,
                fill=False, edgecolor=COL_WALL, lw=2.2, zorder=3))

            # Wing label
            ax.text(ox + wc / 2, wr + 0.38,
                    f"Wing {fac['wing_names'][w]}",
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold', color='#0B1F3B', zorder=8)

            # Internal walls (draw where no edge exists)
            for c in range(wc):
                for r in range(wr):
                    if c + 1 < wc and not wing.has_edge((c, r), (c + 1, r)):
                        ax.plot([ox + c + 1, ox + c + 1], [r, r + 1],
                                color=COL_WALL, lw=1.4, zorder=3)
                    if r + 1 < wr and not wing.has_edge((c, r), (c, r + 1)):
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
        for (w1, c1, r1), (w2, c2, r2) in fac['junctions']:
            x1, y1 = xoff(w1) + c1 + 0.5, r1 + 0.5
            x2, y2 = xoff(w2) + c2 + 0.5, r2 + 0.5
            ax.plot([x1, x2], [y1, y2],
                    color=COL_JUNCTION, lw=1.8,
                    linestyle='--', alpha=0.7, zorder=4)
            ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=5)
            ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=5)

        # Supply markers
        for i, (ws, cs, rs) in enumerate(fac['supplies']):
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
        we, ce, re = fac['entry']
        ox = xoff(we)
        ax.add_patch(plt.Circle(
            (ox + ce + 0.5, re + 0.5), 0.28,
            color=COL_ENTRY, zorder=6))
        ax.text(ox + ce + 0.5, re + 0.5, 'E',
                ha='center', va='center',
                fontsize=6, color='white', fontweight='bold', zorder=7)

        # Exit markers
        for lbl, (wx, cx, rx) in [('A', fac['exit_a']), ('B', fac['exit_b'])]:
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
            mpatches.Patch(color=COL_ENTRY,    label='Entry'),
            mpatches.Patch(color=COL_EXIT,     label='Exit A / B'),
            mpatches.Patch(color=COL_SUPPLY,   label='Supply unit'),
            mpatches.Patch(color=COL_JUNCTION, label='Inter-wing junction'),
        ]
        if node_colors:
            legend_items += [
                mpatches.Patch(color=COL_VISITED,  alpha=0.5, label='Visited'),
                mpatches.Patch(color=COL_FRONTIER, alpha=0.5, label='Frontier'),
                mpatches.Patch(color=COL_CURRENT,  alpha=0.7, label='Current'),
            ]
        ax.legend(handles=legend_items, loc='upper left',
                  fontsize=7, framealpha=0.9)

        ax.set_xlim(-0.5, total_w + 0.5)
        ax.set_ylim(-0.9, wr + 1.1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=11, fontweight='bold',
                     color='#0B1F3B', pad=10)
        plt.tight_layout()
        return fig

    return (draw_multi_wing,)


@app.cell
def visualiser_multi(draw_multi_wing, fac, mo, seed_input):
    _supply_info = []
    for _i, (_ws, _cs, _rs) in enumerate(fac['supplies']):
        _supply_info.append(
            f"**S{_i+1}** → Wing {fac['wing_names'][_ws]} ({_cs},{_rs})")

    _fig = draw_multi_wing(
        fac,
        title=(f"Multi-Wing Facility -- Seed {int(seed_input.value)} · "
               f"{fac['n_wings']} wings · "
               f"{fac['wing_cols']}×{fac['wing_rows']} sectors each")
    )
    mo.vstack([
        mo.md(
            f"**Facility loaded.** "
            f"Wings: {', '.join(fac['wing_names'])} · "
            f"{len(fac['junctions'])} inter-wing corridors · "
            f"{len(fac['supplies'])} supply units"
        ),
        _fig,
        mo.md("**Supply distribution:** " + " · ".join(_supply_info)),
    ])
    return


@app.cell
def wing_stats(fac, mo, nx):
    _rows = []
    for _w, _wing in enumerate(fac['wings']):
        _name = fac['wing_names'][_w]
        _deg  = dict(_wing.degree())
        _dead = sum(1 for d in _deg.values() if d == 1)
        _avg  = sum(_deg.values()) / len(_deg) if _deg else 0
        _nsup = sum(1 for s in fac['supplies'] if s[0] == _w)

        # Diameter of this wing
        try:
            _diam = nx.diameter(_wing)
        except Exception:
            _diam = "--"

        _rows.append({
            'Wing':         f"Wing {_name}",
            'Sectors':      _wing.number_of_nodes(),
            'Corridors':    _wing.number_of_edges(),
            'Dead ends':    _dead,
            'Avg degree':   f"{_avg:.2f}",
            'Diameter':     _diam,
            'Supplies':     _nsup,
            'Has Entry':    '✅' if _w == fac['entry'][0] else '--',
            'Has Exit A/B': '✅' if _w == fac['exit_a'][0] else '--',
        })

    _n_junc = len(fac['junctions'])
    _total_nodes = sum(w.number_of_nodes() for w in fac['wings'])
    _total_edges = sum(w.number_of_edges() for w in fac['wings']) + _n_junc

    # Build markdown table (mo.table not available in all Marimo versions)
    _headers = [
        'Wing', 'Sectors', 'Corridors', 'Dead ends',
        'Avg degree', 'Diameter', 'Supplies', 'Has Entry', 'Has Exit A/B'
    ]
    _tlines = [
        "| " + " | ".join(_headers) + " |",
        "| " + " | ".join(["---"] * len(_headers)) + " |",
    ]
    for _row in _rows:
        _tlines.append("| " + " | ".join(str(_row[h]) for h in _headers) + " |")
    _table_md = "\n".join(_tlines)

    mo.vstack([
        mo.md("## 📊 Multi-Wing Facility Statistics"),
        mo.callout(mo.md(
            "These statistics describe your unique multi-wing facility. "
            "Use them to inform your revised ADT design and traversal strategy."
        ), kind="info"),
        mo.md(_table_md),
        mo.hstack([
            mo.stat(label="Total sectors",         value=str(_total_nodes)),
            mo.stat(label="Total corridors",       value=str(_total_edges)),
            mo.stat(label="Inter-wing corridors",  value=str(_n_junc)),
            mo.stat(label="Wings",                 value=str(fac['n_wings'])),
            mo.stat(label="Total supply units",    value=str(len(fac['supplies']))),
        ], gap=1, wrap=True),
        mo.callout(mo.md("""
    **Inquiry questions -- think about these before writing your revision:**

    1. At least one wing may contain **no supply units**. Must CRUDY-1 still enter it?
       Under what conditions would it be necessary to transit through an empty wing?

    2. Each adjacent wing pair is connected by **exactly two** inter-wing corridors.
       How does the choice of which junction node to use affect total traversal cost?

    3. If you model the full facility as a **flat merged graph**, how many total nodes
       and edges does it have? Does this change the time complexity of your algorithm?

    4. If you model it as a **hierarchical graph** (wings as nodes in a meta-graph),
       what are the nodes, edges, and edge weights of that meta-graph?

    5. The diameter of each wing tells you the worst-case intra-wing traversal distance.
       How should this inform your wing traversal strategy?
        """), kind="neutral"),
    ])
    return


@app.cell
def wing_selector(fac, mo):
    _wing_options = {
        f"Wing {fac['wing_names'][w]}": w
        for w in range(fac['n_wings'])
    }
    wing_select = mo.ui.dropdown(
        options=_wing_options,
        value=f"Wing {fac['wing_names'][0]}",
        label="Select a wing to view in detail"
    )
    mo.vstack([
        mo.md("### 🔍 Individual Wing Viewer"),
        mo.callout(mo.md(
            "Select a wing below to inspect its internal layout in detail. "
            "This mirrors the single-wing view from your Memo 01 workbook."
        ), kind="info"),
        wing_select,
    ])
    return (wing_select,)


@app.cell
def wing_detail_view(fac, mo, mpatches, plt, wing_select):
    _COL_BG      = '#F5F7FA'
    _COL_GRID    = '#C8D0DC'
    _COL_WALL    = '#44546A'
    _COL_ENTRY   = '#0B6E6B'
    _COL_EXIT    = '#7A1E2C'
    _COL_SUPPLY  = '#4AA8A0'
    _COL_JUNC    = '#7A1E2C'

    _w     = wing_select.value
    _wing  = fac['wings'][_w]
    _wname = fac['wing_names'][_w]
    _wc    = fac['wing_cols']
    _wr    = fac['wing_rows']

    _fig, _ax = plt.subplots(figsize=(7, 7))
    _ax.set_facecolor(_COL_BG)
    _fig.patch.set_facecolor(_COL_BG)

    # Grid
    for _c in range(_wc + 1):
        _ax.plot([_c, _c], [0, _wr], color=_COL_GRID, lw=0.4, zorder=1)
    for _r in range(_wr + 1):
        _ax.plot([0, _wc], [_r, _r], color=_COL_GRID, lw=0.4, zorder=1)

    # Border
    for _x0, _y0, _x1, _y1 in [
        (0, 0, _wc, 0), (_wc, 0, _wc, _wr),
        (_wc, _wr, 0, _wr), (0, _wr, 0, 0)
    ]:
        _ax.plot([_x0, _x1], [_y0, _y1],
                 color=_COL_WALL, lw=2.2, zorder=3)

    # Internal walls
    for _c in range(_wc):
        for _r in range(_wr):
            if _c + 1 < _wc and not _wing.has_edge((_c, _r), (_c + 1, _r)):
                _ax.plot([_c + 1, _c + 1], [_r, _r + 1],
                         color=_COL_WALL, lw=1.6, zorder=3)
            if _r + 1 < _wr and not _wing.has_edge((_c, _r), (_c, _r + 1)):
                _ax.plot([_c, _c + 1], [_r + 1, _r + 1],
                         color=_COL_WALL, lw=1.6, zorder=3)

    # Junction nodes on this wing
    _junc_nodes_here = set()
    for (_wj1, _cj1, _rj1), (_wj2, _cj2, _rj2) in fac['junctions']:
        if _wj1 == _w:
            _junc_nodes_here.add((_cj1, _rj1))
        if _wj2 == _w:
            _junc_nodes_here.add((_cj2, _rj2))
    for (_cj, _rj) in _junc_nodes_here:
        _ax.plot(_cj + 0.5, _rj + 0.5,
                 'o', ms=12, color=_COL_JUNC, alpha=0.6, zorder=5)
        _ax.text(_cj + 0.5, _rj + 0.5, 'J',
                 ha='center', va='center',
                 fontsize=6, color='white', fontweight='bold', zorder=6)

    # Supplies in this wing
    for _i, (_ws, _cs, _rs) in enumerate(fac['supplies']):
        if _ws == _w:
            _ax.plot(_cs + 0.5, _rs + 0.5,
                     marker='*', markersize=16, color=_COL_SUPPLY,
                     markeredgecolor=_COL_ENTRY, markeredgewidth=0.8, zorder=5)
            _ax.text(_cs + 0.62, _rs + 0.58, f'S{_i + 1}',
                     fontsize=7, color=_COL_WALL, zorder=6)

    # Entry (only in Wing Alpha)
    _we, _ce, _re = fac['entry']
    if _we == _w:
        _ax.add_patch(plt.Circle(
            (_ce + 0.5, _re + 0.5), 0.25, color=_COL_ENTRY, zorder=6))
        _ax.text(_ce + 0.5, _re + 0.5, 'E',
                 ha='center', va='center',
                 fontsize=7, color='white', fontweight='bold', zorder=7)

    # Exits (only in last wing)
    for _lbl, (_wx, _cx, _rx) in [('A', fac['exit_a']), ('B', fac['exit_b'])]:
        if _wx == _w:
            _ax.add_patch(plt.Circle(
                (_cx + 0.5, _rx + 0.5), 0.25, color=_COL_EXIT, zorder=6))
            _ax.text(_cx + 0.5, _rx + 0.5, _lbl,
                     ha='center', va='center',
                     fontsize=7, color='white', fontweight='bold', zorder=7)

    _legend = [
        mpatches.Patch(color=_COL_SUPPLY, label='Supply unit'),
        mpatches.Patch(color=_COL_JUNC,   alpha=0.6, label='Inter-wing junction (J)'),
        mpatches.Patch(color=_COL_ENTRY,  label='Entry'),
        mpatches.Patch(color=_COL_EXIT,   label='Exit'),
    ]
    _ax.legend(handles=_legend, loc='upper left', fontsize=8, framealpha=0.9)
    _ax.set_xlim(0, _wc); _ax.set_ylim(0, _wr)
    _ax.set_aspect('equal'); _ax.axis('off')
    _ax.set_title(
        f"Wing {_wname} -- Detail View",
        fontsize=11, fontweight='bold', color='#0B1F3B', pad=10)
    plt.tight_layout()

    # Wing-specific stats
    _deg  = dict(_wing.degree())
    _dead = sum(1 for d in _deg.values() if d == 1)
    _nsup = sum(1 for s in fac['supplies'] if s[0] == _w)

    mo.vstack([
        mo.hstack([
            mo.stat(label="Sectors",       value=str(_wing.number_of_nodes())),
            mo.stat(label="Corridors",     value=str(_wing.number_of_edges())),
            mo.stat(label="Dead ends",     value=str(_dead)),
            mo.stat(label="Supplies here", value=str(_nsup)),
            mo.stat(label="Junction nodes",value=str(len(_junc_nodes_here))),
        ], gap=1),
        _fig,
    ])
    return


@app.cell
def original_responses_display(SAVE_FILE_ORIG, json, mo, os):
    _orig = {}
    if os.path.exists(SAVE_FILE_ORIG):
        with open(SAVE_FILE_ORIG, "r") as _f:
            try:
                _all = json.load(_f)
                if _all:
                    _orig = _all[-1]
            except Exception:
                pass

    def _show(key, label):
        val = _orig.get(key, "").strip()
        if val:
            # Indent each line for blockquote rendering
            indented = "\n".join("> " + line for line in val.splitlines())
            return mo.md(f"**{label}:**\n\n{indented}")
        return mo.md(f"*{label}: not yet saved in `responses.json`*")

    mo.vstack([
        mo.md("""
    ---
    ## 📋 Your Original Memo 01 Responses (Read-Only Reference)

    Your most recent responses from `responses.json` are shown below.
    **Do not edit these** -- your revisions go in the sections below.
    Both your original and revised work must remain visible in your notebook for marking.
        """),
        mo.accordion({
            "A1 -- Original problem specification":   _show("A1 response",   "A1"),
            "A2 -- Original salient features":        _show("A2 response",   "A2"),
            "A3 -- Original ADT design":              _show("A3 response",   "A3"),
            "B1 -- Original algorithm consideration": _show("B1 response",   "B1"),
            "B2 -- Original algorithm description":   _show("B2 response",   "B2"),
            "C1 -- Original pseudocode":              _show("C1 pseudocode", "C1"),
            "D1 -- Original justification":           _show("D1 response",   "D1"),
        }),
        mo.callout(mo.md(
            "If your original responses do not appear, ensure `responses.json` "
            "is in the **same folder** as this notebook, then re-open this workbook."
        ), kind="warn"),
    ])
    return


@app.cell
def amendment_section_header(mo):
    mo.md("""
    ---
    ## ✏️ Amendment Responses

    Complete each revision cell below. Your responses must **build directly on your
    Memo 01 work** while addressing the new multi-wing structure from Amendment Memo A1.

    Label conventions used in this workbook:

    | Label | Section |
    |---|---|
    | `[A1-REVISED]` | Action 1 Revision -- Data Model Redesign |
    | `[A2-REVISED]` | Action 2 Revision -- Algorithm Redesign |
    | `[A3-REVISED]` | Action 3 Revision -- Pseudocode Update |
    | `[A3b-REVISED]` | Action 3b -- Revised Implementation |
    | `[A4-REVISED]` | Action 4 Revision -- Justification Update |
    """)
    return


@app.cell
def action1_rev_header(mo):
    mo.md("""
    ---
    ### [A1-REVISED] Action 1 Revision -- Data Model Redesign
    *Criterion 1 · Observation 1 · Design artefact (no fixed word count)*

    > Revise your data model to represent the multi-wing facility.
    > Precision and justification are assessed, not length.

    **You must address all three parts:**

    **Part 1 -- Identify limitations of your Memo 01 model.**
    Which ADT structures and operations assumed a single connected graph?
    Why does that assumption break in a multi-wing setting?

    **Part 2 -- Evaluate two design approaches:**
    - *Flat graph*: merge all wings into one unified graph, tagging each node with
      its wing identifier (e.g. node = (wing_id, col, row)).
    - *Hierarchical graph*: a meta-graph where each wing is a node, connected by
      inter-wing edges, with the internal sector structure of each wing as a
      nested sub-graph.

    For each approach: specify what new or modified ADT operations are required,
    and state one advantage and one disadvantage relative to the mission objectives.

    **Part 3 -- Select, specify, and justify.**
    Provide updated ADT signatures (in Algorithmics metalanguage) for any new or
    modified operations. Justify your selection with reference to your algorithm design
    and the multi-wing mission constraints.

    *Example signature format:*
    ```
    get_wing(node: Node) → WingID
    inter_wing_neighbours(node: Node) → Set[Node]
    wings(facility: MultiWingFacility) → Set[WingID]
    ```

    ---
    """)
    return


@app.cell
def action1_rev_input(SAVE_FILE_A01, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_A01):
        try:
            with open(SAVE_FILE_A01, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("A1_REV", "")
        except Exception:
            pass

    rev_a1 = mo.ui.text_area(
        label="**[A1-REVISED] Your revised data model response**",
        value=_saved,
        rows=12,
        full_width=True,
        placeholder=(
            "Part 1 -- Limitations of my Memo 01 model:\n"
            "  My Memo 01 model assumed ... which breaks because ...\n\n"
            "Part 2 -- Flat graph approach:\n"
            "  New ADT operations: ...\n"
            "  Advantage: ...\n"
            "  Disadvantage: ...\n\n"
            "  Hierarchical graph approach:\n"
            "  New ADT operations: ...\n"
            "  Advantage: ...\n"
            "  Disadvantage: ...\n\n"
            "Part 3 -- My selected approach: [flat / hierarchical]\n"
            "  Justification: ...\n\n"
            "  Updated ADT signatures:\n"
            "  ..."
        )
    )
    rev_a1
    return (rev_a1,)


@app.cell
def action1_rev_display(mo, rev_a1):
    mo.callout(
        mo.md("**[A1-REVISED] Saved response:**\n\n" + rev_a1.value)
        if rev_a1.value.strip()
        else mo.md("*No response entered yet.*"),
        kind="success"
    )
    return


@app.cell
def action2_rev_header(mo):
    mo.md("""
    ---
    ### [A2-REVISED] Action 2 Revision -- Algorithm Redesign
    *Criterion 2 · Observation 2 · Word range: 400–600 words*

    > Redesign your algorithm to handle multi-wing traversal.

    **You must address all three parts:**

    **Part 1 -- Identify the new sub-problems.**
    How does CRUDY-1 decide which wing to enter next?
    How does it handle wings containing no supply units?
    How does it manage **multiple** inter-wing junction nodes when
    moving between two adjacent wings?

    **Part 2 -- Evaluate two wing-traversal strategies:**
    - *Exhaustive*: fully search (and collect all supplies from) one wing
      before moving to the next, committing to a wing order at the outset.
    - *Interleaved*: dynamically move between wings based on supply locations
      and traversal cost -- no predetermined order.

    For each, discuss suitability given the Memo 01 constraints applied to
    the multi-wing setting. Where does each strategy perform well? Where does it fail?

    **Part 3 -- Describe your revised algorithm in full.**
    Explain how inter-wing traversal is handled, how supply collection is tracked
    across wings, and how the algorithm determines which exit to target when
    exits exist only in the last wing.

    ---
    """)
    return


@app.cell
def action2_rev_input(SAVE_FILE_A01, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_A01):
        try:
            with open(SAVE_FILE_A01, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("A2_REV", "")
        except Exception:
            pass

    rev_a2 = mo.ui.text_area(
        label="**[A2-REVISED] Your revised algorithm design response**",
        value=_saved,
        rows=12,
        full_width=True,
        placeholder=(
            "Part 1 -- New sub-problems in the multi-wing setting:\n"
            "  Wing selection: CRUDY-1 decides which wing to enter next by ...\n"
            "  Empty wings: If a wing has no supplies, CRUDY-1 ...\n"
            "  Junction selection: When multiple junctions connect wings, CRUDY-1 ...\n\n"
            "Part 2 -- Exhaustive strategy:\n"
            "  How it works: ...\n"
            "  Suitability: ...\n"
            "  Limitations: ...\n\n"
            "  Interleaved strategy:\n"
            "  How it works: ...\n"
            "  Suitability: ...\n"
            "  Limitations: ...\n\n"
            "Part 3 -- My revised algorithm:\n"
            "  ..."
        )
    )
    rev_a2
    return (rev_a2,)


@app.cell
def action2_rev_display(mo, rev_a2):
    mo.callout(
        mo.md("**[A2-REVISED] Saved response:**\n\n" + rev_a2.value)
        if rev_a2.value.strip()
        else mo.md("*No response entered yet.*"),
        kind="success"
    )
    return


@app.cell
def action3_rev_header(mo):
    mo.md(r"""
    ---
    ### [A3-REVISED] Action 3 Revision -- Pseudocode Update
    *Criterion 3 · Observation 3*

    > Update your pseudocode to reflect the revised data model and algorithm.

    **Your revised pseudocode must:**
    - Use your **revised ADT operations** from Action 1 Revision by name.
    - Include a **wing-level traversal procedure** as a clearly defined abstraction,
      separate from the intra-wing traversal logic.
    - Correctly handle wings containing **no supply units**
      (CRUDY-1 may transit through them to reach another wing or an exit).
    - Show how **multiple inter-wing junction nodes** are evaluated when
      selecting which corridor to use between wings.

    *Use standard Algorithmics pseudocode conventions.*

    ```
    FUNCTION name(param: Type, ...) → ReturnType
    ...
    END FUNCTION

    PROCEDURE name(param: Type, ...)
    ...
    END PROCEDURE
    ```
    """)
    return


@app.cell
def action3_rev_pseudocode(SAVE_FILE_A01, json, mo, os):
    _saved_ps = ""
    if os.path.exists(SAVE_FILE_A01):
        try:
            with open(SAVE_FILE_A01, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved_ps = _d[-1].get("A3_REV_pseudo", "")
        except Exception:
            pass

    if not _saved_ps:
        _saved_ps = "\n".join([
            "// [A3-REVISED] Multi-wing pseudocode",
            "// Replace this skeleton with your complete revised algorithm.",
            "",
            "FUNCTION ember_rescue_multi(",
            "    facility: MultiWingFacility,",
            "    entry: Node,",
            "    exits: Set[Node],",
            "    supplies: Set[Node]",
            ") -> Path",
            "",
            "    collected    <- empty Set",
            "    path         <- [entry]",
            "    current_wing <- get_wing(entry)",
            "",
            "    // Main loop: continue until all supplies collected or at an exit",
            "    WHILE collected ≠ supplies AND current_node ∉ exits DO",
            "",
            "        // Decide: search current wing, or transit to another?",
            "        IF wing_has_uncollected_supplies(current_wing, collected) THEN",
            "            traverse_wing(current_wing, current_node, collected, path)",
            "        ELSE",
            "            // Choose next wing and junction to use",
            "            next_wing   <- choose_next_wing(facility, current_wing, collected)",
            "            junction    <- choose_junction(current_node, next_wing, facility)",
            "            path        <- path + path_to(current_node, junction)",
            "            path        <- path + [transit_to(next_wing, junction)]",
            "            current_wing <- next_wing",
            "        END IF",
            "",
            "    END WHILE",
            "",
            "    RETURN path",
            "",
            "END FUNCTION",
            "",
            "",
            "PROCEDURE traverse_wing(",
            "    wing: Graph,",
            "    entry_node: Node,",
            "    collected: Set[Node],",
            "    path: Path",
            ")",
            "    // Search within a single wing for uncollected supply units.",
            "    // Updates collected and path in place.",
            "    // ...",
            "END PROCEDURE",
            "",
            "",
            "FUNCTION choose_junction(",
            "    current: Node,",
            "    target_wing: WingID,",
            "    facility: MultiWingFacility",
            ") -> Node",
            "    // Select the inter-wing junction node that minimises",
            "    // the total path from current to the target wing.",
            "    // ...",
            "END FUNCTION",
            "",
            "",
            "FUNCTION choose_next_wing(",
            "    facility: MultiWingFacility,",
            "    current_wing: WingID,",
            "    collected: Set[Node]",
            ") -> WingID",
            "    // Decide which wing to visit next based on supply locations",
            "    // and reachability from current wing.",
            "    // ...",
            "END FUNCTION",
        ])

    rev_a3_pseudo = mo.ui.code_editor(
        value=_saved_ps,
        min_height=380,
    )
    rev_a3_pseudo
    return (rev_a3_pseudo,)


@app.cell
def action3b_rev_header(mo):
    mo.md(r"""
    ### [A3b-REVISED] Revised Algorithm Implementation -- Multi-Wing

    Implement your revised algorithm in Python below, then run it on your facility.

    **Your function signature:**
    ```python
    def my_multi_wing_algorithm(fac, deque):
    # fac keys:
    #   'wings'     -- list of nx.Graph objects (one per wing)
    #   'wing_cols' -- int, columns per wing
    #   'wing_rows' -- int, rows per wing
    #   'entry'     -- (wing_id, col, row)
    #   'exit_a'    -- (wing_id, col, row)
    #   'exit_b'    -- (wing_id, col, row)
    #   'supplies'  -- list of (wing_id, col, row) nodes
    #   'junctions' -- list of ((w1,c1,r1), (w2,c2,r2)) inter-wing corridor pairs
    #   'n_wings'   -- int
    # Returns: (path, collected)
    #   path      -- list of (wing_id, col, row) tuples
    #   collected -- list of supply nodes collected along the path
    ...
    ```

    The **helper function** `all_neighbours(node, fac)` below shows how to build a
    unified neighbour lookup across all wings and junctions -- use it as a starting point.
    """)
    return


@app.cell
def action3b_rev_code(SAVE_FILE_A01, json, mo, os):
    _saved_code = ""
    if os.path.exists(SAVE_FILE_A01):
        try:
            with open(SAVE_FILE_A01, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved_code = _d[-1].get("A3_REV_code", "")
        except Exception:
            pass

    if not _saved_code:
        _saved_code = "\n".join([
            "def my_multi_wing_algorithm(fac, deque):",
            "    wings     = fac['wings']",
            "    entry     = fac['entry']",
            "    exit_a    = fac['exit_a']",
            "    exit_b    = fac['exit_b']",
            "    supplies  = set(tuple(s) for s in fac['supplies'])",
            "    junctions = fac['junctions']",
            "",
            "    def all_neighbours(node):",
            "        \"\"\"Return all neighbours of a (wing_id, col, row) node.",
            "        Includes intra-wing corridor neighbours AND inter-wing junctions.\"\"\"",
            "        w, c, r = node",
            "        # Intra-wing neighbours",
            "        nbrs = [(w, nc, nr) for nc, nr in wings[w].neighbors((c, r))]",
            "        # Inter-wing junction neighbours",
            "        for n1, n2 in junctions:",
            "            if tuple(n1) == node:",
            "                nbrs.append(tuple(n2))",
            "            elif tuple(n2) == node:",
            "                nbrs.append(tuple(n1))",
            "        return nbrs",
            "",
            "    # -------------------------------------------------------",
            "    # Replace the BFS below with your revised algorithm.",
            "    # The starter BFS searches for exit_a only and does not",
            "    # explicitly plan for supply collection.",
            "    # -------------------------------------------------------",
            "",
            "    from collections import deque as dq",
            "    visited   = {entry}",
            "    queue     = dq([(entry, [entry])])",
            "    best_path = [entry]",
            "",
            "    while queue:",
            "        node, cur_path = queue.popleft()",
            "        if node == exit_a or node == exit_b:",
            "            best_path = cur_path",
            "            break",
            "        for nb in all_neighbours(node):",
            "            nb = tuple(nb)",
            "            if nb not in visited:",
            "                visited.add(nb)",
            "                queue.append((nb, cur_path + [nb]))",
            "",
            "    # Collect supplies along the path",
            "    collected = [n for n in best_path if n in supplies]",
            "",
            "    return best_path, collected",
        ])

    rev_a3_code = mo.ui.code_editor(
        value=_saved_code,
        language="python",
        min_height=480,
    )
    rev_a3_code
    return (rev_a3_code,)


@app.cell
def action3b_rev_runner(
    deque,
    draw_multi_wing,
    fac,
    mo,
    rev_a3_code,
    textwrap,
):
    _code = textwrap.dedent(rev_a3_code.value)
    _ns   = {"deque": deque}

    try:
        exec(_code, _ns)
        _fn = _ns["my_multi_wing_algorithm"]
        _path_raw, _collected_raw = _fn(fac, deque)
        if _path_raw is None:
            raise ValueError("Algorithm returned None for path.")
        _path_r      = [tuple(n) for n in _path_raw]
        _collected_r = [tuple(n) for n in _collected_raw]
        _status      = ("ok", _path_r, _collected_r)
    except Exception as _e:
        _status = ("error", str(_e), [])

    _stype, _sdata, _scollected = _status

    if _stype == "error":
        _out = mo.callout(
            mo.md(f"**Error in your algorithm:** `{_sdata}`\n\nCheck your code above."),
            kind="danger"
        )
    else:
        _path_res = _sdata
        _supplies_set = set(tuple(s) for s in fac['supplies'])

        # Check if path ends at an exit
        _at_exit = bool(
            _path_res and
            (tuple(_path_res[-1]) == tuple(fac['exit_a']) or
             tuple(_path_res[-1]) == tuple(fac['exit_b']))
        )

        # Validate all moves
        _valid_edges = True
        for _i in range(len(_path_res) - 1):
            _n1 = tuple(_path_res[_i])
            _n2 = tuple(_path_res[_i + 1])
            _w1, _c1, _r1 = _n1
            _w2, _c2, _r2 = _n2
            if _w1 == _w2:
                if not fac['wings'][_w1].has_edge((_c1, _r1), (_c2, _r2)):
                    _valid_edges = False
                    break
            else:
                _junc_set = {
                    (tuple(j[0]), tuple(j[1])) for j in fac['junctions']
                }
                if (_n1, _n2) not in _junc_set and (_n2, _n1) not in _junc_set:
                    _valid_edges = False
                    break

        _fig = draw_multi_wing(
            fac,
            highlight_path=_path_res,
            supply_collected=set(_scollected),
            title=(f"Revised Algorithm -- Path: {len(_path_res)-1} steps · "
                   f"Supplies: {len(_scollected)}/{len(fac['supplies'])}")
        )

        _supply_labels = ", ".join(
            f"S{fac['supplies'].index(list(s))+1}"
            for s in _scollected
            if list(s) in fac['supplies']
        ) if _scollected else "None"

        # Wings visited
        _wings_visited = sorted(set(n[0] for n in _path_res))
        _wing_label = ", ".join(
            f"Wing {fac['wing_names'][w]}" for w in _wings_visited)

        _out = mo.vstack([
            mo.md("#### [A3b-REVISED] Algorithm test results"),
            mo.hstack([
                mo.stat(label="Path length",
                        value=f"{len(_path_res)-1} steps"),
                mo.stat(label="Supplies collected",
                        value=f"{len(_scollected)}/{len(fac['supplies'])}"),
                mo.stat(label="Ends at exit",
                        value="✅ Yes" if _at_exit else "❌ No"),
                mo.stat(label="All moves valid",
                        value="✅ Yes" if _valid_edges else "❌ No"),
                mo.stat(label="Wings visited",
                        value=str(len(_wings_visited))),
            ], gap=1, wrap=True),
            _fig,
            mo.md(
                f"**Collected:** {_supply_labels}  \n"
                f"**Wings traversed:** {_wing_label}"
            ),
            mo.callout(mo.md("""
    **Reflect on your revised result:**
    - Does your algorithm correctly navigate inter-wing corridors (junction nodes)?
    - Were any wings visited purely for transit (no supplies collected there)?
      Was this necessary, or could your algorithm avoid it?
    - How does the total path length compare to what your Memo 01 algorithm
      would produce on a single wing of the same size?
    - Does your algorithm collect all 5 supplies before reaching the exit?
      If not, is this by design or a limitation?
            """), kind="info"),
        ])

    _out
    return


@app.cell
def action4_rev_header(mo):
    mo.md("""
    ---
    ### [A4-REVISED] Action 4 Revision -- Justification Update
    *Criterion 4 · Observation 4 · Word range: 200–400 words*

    > Revise your justification to account for the multi-wing architecture.
    > A strong justification engages honestly with new tensions -- not just new strengths.

    **You must address all three dimensions:**

    **1. Suitability**
    Does your revised algorithm remain appropriate for the Emberlight problem?
    What new assumptions does it rely on that were not present in your Memo 01 solution?
    Are those assumptions justified given the mission constraints?

    **2. Coherence**
    Does your revised data model support your revised algorithm without contradiction?
    Identify at least one tension between the two (e.g. an operation your algorithm
    needs that isn't in your ADT signature) and explain how you resolved it.

    **3. Fitness for purpose -- stress test**
    Consider this scenario: one inter-wing access corridor is blocked
    (its junction node is sealed and cannot be used). Does your solution handle
    this gracefully, or does it fail? What does this reveal about the robustness
    of your model? Would your algorithm detect the blockage, reroute, or simply halt?

    ---
    """)
    return


@app.cell
def action4_rev_input(SAVE_FILE_A01, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE_A01):
        try:
            with open(SAVE_FILE_A01, "r") as _f:
                _d = json.load(_f)
            if _d:
                _saved = _d[-1].get("A4_REV", "")
        except Exception:
            pass

    rev_a4 = mo.ui.text_area(
        label="**[A4-REVISED] Your revised justification**",
        value=_saved,
        rows=12,
        full_width=True,
        placeholder=(
            "1. Suitability:\n"
            "   My revised algorithm is appropriate for Emberlight because ...\n"
            "   New assumptions it relies on: ...\n"
            "   These are justified because ...\n\n"
            "2. Coherence:\n"
            "   My revised data model and algorithm work together because ...\n"
            "   One tension I identified: ...\n"
            "   I resolved it by ...\n\n"
            "3. Fitness for purpose -- blocked junction scenario:\n"
            "   If a junction node were sealed, my algorithm would ...\n"
            "   This reveals that my model is [robust / brittle] because ...\n"
            "   To handle this more gracefully I would need to ..."
        )
    )
    rev_a4
    return (rev_a4,)


@app.cell
def action4_rev_display(mo, rev_a4):
    mo.callout(
        mo.md("**[A4-REVISED] Saved response:**\n\n" + rev_a4.value)
        if rev_a4.value.strip()
        else mo.md("*No response entered yet.*"),
        kind="success"
    )
    return


@app.cell
def save_controls(mo):
    save_btn = mo.ui.button(
        value=0,
        label="💾 Save All Revision Responses",
        on_click=lambda v: v + 1
    )
    mo.vstack([
        mo.md("---\n### 💾 Save your responses"),
        mo.callout(mo.md(
            "Click **Save** to write all revision responses to `responses_A01.json`. "
            "Each save appends a new timestamped entry -- earlier saves are preserved. "
            "Save regularly during class."
        ), kind="info"),
        save_btn,
    ])
    return (save_btn,)


@app.cell
def save_responses(
    SAVE_FILE_A01,
    datetime,
    json,
    mo,
    os,
    rev_a1,
    rev_a2,
    rev_a3_code,
    rev_a3_pseudo,
    rev_a4,
    save_btn,
):
    if save_btn.value > 0:
        if os.path.exists(SAVE_FILE_A01):
            try:
                with open(SAVE_FILE_A01, "r") as _f:
                    _all = json.load(_f)
            except Exception:
                _all = []
        else:
            _all = []

        _all.append({
            "timestamp":      datetime.datetime.now().isoformat(),
            "A1_REV":         rev_a1.value,
            "A2_REV":         rev_a2.value,
            "A3_REV_pseudo":  rev_a3_pseudo.value,
            "A3_REV_code":    rev_a3_code.value,
            "A4_REV":         rev_a4.value,
        })

        with open(SAVE_FILE_A01, "w") as _f:
            json.dump(_all, _f, indent=2)

        _result = mo.callout(
            mo.md(
                f"✅ **Saved** at "
                f"{datetime.datetime.now().strftime('%H:%M:%S')} "
                f"-- `{SAVE_FILE_A01}`"
            ),
            kind="success"
        )
    else:
        _result = mo.md("*Press Save above to record your responses.*")

    _result
    return


@app.cell
def footer(mo):
    mo.md("""
    ---
    *End of Amendment Memo A1 workbook -- submit alongside your Memo 01 notebook at **Observation 4**.*

    **Before submitting, check:**
    - [ ] Your seed matches your Memo 01 cover sheet
    - [ ] Your original Memo 01 responses are visible in the reference section above
    - [ ] **[A1-REVISED]** -- data model revision addresses flat vs. hierarchical design
    - [ ] **[A2-REVISED]** -- algorithm revision addresses wing traversal strategy
    - [ ] **[A3-REVISED]** -- revised pseudocode includes a wing-level traversal abstraction
    - [ ] **[A3b-REVISED]** -- revised implementation runs without errors on your facility
    - [ ] **[A4-REVISED]** -- justification revision addresses the blocked-junction scenario
    - [ ] All responses have been saved to `responses_A01.json`

    *Your Memo 02 workbook will be released separately when Memo 02 begins.*
    """)
    return


if __name__ == "__main__":
    app.run()
