import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import random
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.colors as mcolors
    from collections import deque
    import json
    import os
    import datetime
    import textwrap
    import heapq

    SAVE_FILE_A01 = "responses_A01.json"   # A01 responses (read-only reference)
    SAVE_FILE_A02 = "responses_A02.json"   # A02 responses (written here)
    return (
        SAVE_FILE_A01,
        SAVE_FILE_A02,
        datetime,
        json,
        mcolors,
        mo,
        mpatches,
        nx,
        os,
        plt,
        random,
    )


@app.cell
def header(mo):
    mo.md("""
    # Operation Emberlight -- Amendment Memo A02 Workbook

    | Field | Value |
    |---|---|
    | **Name** | *(your name)* |
    | **Student number** | *(your number)* |
    | **Facility seed** | *(enter below -- same as Memo 01)* |
    | **Teacher** | *(teacher name)* |

    > **New intelligence has been received.**
    > Corridor traversal costs across the facility are **non-uniform**.
    > Each wing operates under a different cost model.
    > Your algorithm must be capable of finding minimum-cost paths through a weighted graph.

    > **Authentication note:** Use the **same seed** as your Memo 01 and A01 workbooks.

    ---
    **How to use this workbook:**
    - Enter your seed below to generate your weighted facility.
    - Review your A01 responses in the reference section.
    - Complete revision cells for Actions A2-1 through A2-4.
    - Save responses and submit at **Observation 5**.
    """)
    return


@app.cell
def seed_cell(mo):
    seed_input = mo.ui.number(
        value=12345,
        start=0,
        stop=99999999,
        step=1,
        label="Your facility seed (same as Memo 01 and A01)"
    )
    mo.vstack([
        mo.md("### Enter your seed, then press Tab to rebuild the facility."),
        seed_input
    ])
    return (seed_input,)


@app.cell
def multi_wing_generator(nx, random, seed_input):
    """Build the multi-wing maze (same as A01)."""
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
        n_wings = 2 + (int_seed % 3)
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
            reserved.add(n1); reserved.add(n2)
        per_wing_cands = []
        for w, wg in enumerate(wings):
            de = [(w, c, r) for (c, r) in wg.nodes()
                  if wg.degree((c, r)) == 1 and (w, c, r) not in reserved]
            srng.shuffle(de)
            per_wing_cands.append(de)
        supplies = []
        for _ in range(2):
            for wl in per_wing_cands:
                if len(supplies) >= 5: break
                for n in wl:
                    if n not in supplies:
                        supplies.append(n); break
            if len(supplies) >= 5: break
        return {
            'n_wings': n_wings, 'wing_names': wing_names,
            'wings': wings, 'wing_cols': WING_COLS, 'wing_rows': WING_ROWS,
            'entry': entry, 'exit_a': exit_a, 'exit_b': exit_b,
            'supplies': supplies[:5], 'junctions': junctions,
        }

    fac = get_multi_wing_facility(seed_input.value)
    return (fac,)


@app.cell
def cost_model(fac, random, seed_input):
    """Apply per-wing cost models to the facility edges.

    Wing 0 (Alpha) : uniform  -- cost = 1
    Wing 1 (Beta)  : depth    -- cost = 1 + floor(max(c1,c2) / 3)
    Wing 2+ (Gamma+): seeded  -- cost = randint(1, 5) per corridor
    Inter-wing junctions: cost = 1
    """
    import copy
    int_seed = int(seed_input.value)

    # Deep-copy wings so we don't mutate the base facility
    weighted_wings = [g.copy() for g in fac['wings']]

    def _alpha_cost(c1, r1, c2, r2):
        return 1

    def _beta_cost(c1, r1, c2, r2):
        return 1 + max(c1, c2) // 3

    def _seeded_rng(wing_idx):
        return random.Random(int_seed * 41 + wing_idx * 3331)

    cost_models = []
    for w, wg in enumerate(weighted_wings):
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
    junction_costs = {(n1, n2): 1 for n1, n2 in fac['junctions']}

    weighted_fac = dict(fac)
    weighted_fac['wings'] = weighted_wings
    weighted_fac['junction_costs'] = junction_costs
    weighted_fac['cost_models'] = cost_models
    return (weighted_fac,)


@app.cell
def drawing_utils_weighted(mcolors, mpatches, plt):
    """Drawing utilities for the weighted multi-wing facility."""

    COL_BG      = '#F5F7FA'
    COL_WALL    = '#44546A'
    COL_BORDER  = '#2C3E50'
    COL_ENTRY   = '#0B6E6B'
    COL_EXIT    = '#7A1E2C'
    COL_SUPPLY  = '#4AA8A0'
    COL_JUNC    = '#7A1E2C'
    COL_GRID    = '#C8D0DC'

    # Weight colour scale: 1=lightest, 5=darkest
    WEIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
        'wcost', ['#B8E0DE', '#F4C97A', '#E88A4A', '#C84A30', '#7A1E2C']
    )

    def _weight_colour(w, wmin=1, wmax=5):
        t = (w - wmin) / max(wmax - wmin, 1)
        return WEIGHT_CMAP(t)

    _GAP = 3

    def draw_weighted_facility(wfac, highlight_path=None, title="Weighted Multi-Wing Facility"):
        nw = wfac['n_wings']
        wc = wfac['wing_cols']
        wr = wfac['wing_rows']
        total_w = nw * wc + (nw - 1) * _GAP

        fig, ax = plt.subplots(figsize=(min(3.8 * nw, 14), 5))
        ax.set_xlim(-0.5, total_w + 0.5)
        ax.set_ylim(-0.8, wr + 0.6)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_facecolor(COL_BG)
        fig.patch.set_facecolor(COL_BG)

        def wing_x(w):
            return w * (wc + _GAP)

        for w, wg in enumerate(wfac['wings']):
            ox = wing_x(w)

            # Background
            ax.add_patch(plt.Rectangle((ox, 0), wc, wr,
                facecolor=COL_BG, edgecolor='none', zorder=0))

            # Draw each corridor coloured by weight
            for (c1, r1), (c2, r2) in wg.edges():
                cost = wg[(c1, r1)][(c2, r2)].get('weight', 1)
                col = _weight_colour(cost)
                x1, y1 = ox + c1 + 0.5, r1 + 0.5
                x2, y2 = ox + c2 + 0.5, r2 + 0.5
                ax.plot([x1, x2], [y1, y2], color=col, lw=3.5,
                        solid_capstyle='round', zorder=1, alpha=0.85)

            # Draw walls (cell boundary segments where no edge exists)
            for c in range(wc):
                for r in range(wr):
                    # right neighbour
                    if c + 1 < wc and not wg.has_edge((c, r), (c + 1, r)):
                        ax.plot([ox + c + 1, ox + c + 1], [r, r + 1],
                                color=COL_WALL, lw=1.3, zorder=2)
                    # top neighbour
                    if r + 1 < wr and not wg.has_edge((c, r), (c, r + 1)):
                        ax.plot([ox + c, ox + c + 1], [r + 1, r + 1],
                                color=COL_WALL, lw=1.3, zorder=2)

            # Outer border
            ax.add_patch(plt.Rectangle((ox, 0), wc, wr,
                fill=False, edgecolor=COL_BORDER, lw=2.0, zorder=3))

            # Wing label
            ax.text(ox + wc / 2, wr + 0.3,
                    f"Wing {wfac['wing_names'][w]}",
                    ha='center', va='bottom', fontsize=9,
                    fontweight='bold', color='#0B1F3B', zorder=8)

            # Cost model label
            ax.text(ox + wc / 2, -0.55,
                    wfac['cost_models'][w],
                    ha='center', va='top', fontsize=6,
                    color='#44546A', style='italic', zorder=8)

        # Inter-wing corridors + junctions
        for (w1, c1, r1), (w2, c2, r2) in wfac['junctions']:
            x1 = wing_x(w1) + c1 + 0.5
            x2 = wing_x(w2) + c2 + 0.5
            y1, y2 = r1 + 0.5, r2 + 0.5
            ax.plot([x1, x2], [y1, y2], color=COL_JUNC, lw=1.6,
                    linestyle='--', zorder=4, alpha=0.8)
            ax.plot(x1, y1, 'o', ms=6, color=COL_JUNC, zorder=5)
            ax.plot(x2, y2, 'o', ms=6, color=COL_JUNC, zorder=5)

        # Supply units
        for (ws, cs, rs) in wfac['supplies']:
            ox = wing_x(ws)
            ax.plot(ox + cs + 0.5, rs + 0.5, marker='*', ms=11,
                    color=COL_SUPPLY, markeredgecolor=COL_ENTRY, lw=0.8, zorder=6)

        # Entry
        we, ce, re = wfac['entry']
        ox = wing_x(we)
        ax.add_patch(plt.Circle((ox + ce + 0.5, re + 0.5), 0.38,
            color=COL_ENTRY, zorder=6))
        ax.text(ox + ce + 0.5, re + 0.5, 'E', ha='center', va='center',
                fontsize=6, color='white', fontweight='bold', zorder=7)

        # Exits
        for lbl, (wx, cx, rx) in [('A', wfac['exit_a']), ('B', wfac['exit_b'])]:
            ox = wing_x(wx)
            ax.add_patch(plt.Circle((ox + cx + 0.5, rx + 0.5), 0.38,
                color=COL_EXIT, zorder=6))
            ax.text(ox + cx + 0.5, rx + 0.5, lbl, ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=7)

        # Highlight path if provided
        if highlight_path and len(highlight_path) > 1:
            for i in range(len(highlight_path) - 1):
                n1, n2 = highlight_path[i], highlight_path[i + 1]
                w1, c1, r1 = n1
                w2, c2, r2 = n2
                x1 = wing_x(w1) + c1 + 0.5
                x2 = wing_x(w2) + c2 + 0.5
                ax.plot([x1, x2], [r1 + 0.5, r2 + 0.5],
                        color='#FFD700', lw=2.8, alpha=0.9,
                        solid_capstyle='round', zorder=9)

        # Colour bar legend for weights
        sm = plt.cm.ScalarMappable(
            cmap=WEIGHT_CMAP,
            norm=mcolors.Normalize(vmin=1, vmax=5)
        )
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, orientation='horizontal',
                            fraction=0.03, pad=0.14, aspect=40)
        cbar.set_label('Corridor cost (weight)', fontsize=7, color='#44546A')
        cbar.set_ticks([1, 2, 3, 4, 5])
        cbar.ax.tick_params(labelsize=6, colors='#44546A')

        # Patch legend
        legend_elements = [
            mpatches.Patch(color=COL_ENTRY, label='Entry'),
            mpatches.Patch(color=COL_EXIT, label='Exit A / B'),
            mpatches.Patch(color=COL_SUPPLY, label='Supply unit'),
            mpatches.Patch(color=COL_JUNC, label='Inter-wing junction'),
        ]
        if highlight_path:
            legend_elements.append(
                mpatches.Patch(color='#FFD700', label='Optimal route'))
        ax.legend(handles=legend_elements, loc='upper right',
                  fontsize=6.5, framealpha=0.9,
                  bbox_to_anchor=(1.0, 1.0))

        ax.set_title(title, fontsize=10, color='#0B1F3B', pad=8)
        plt.tight_layout()
        return fig

    return (draw_weighted_facility,)


@app.cell
def visualiser_weighted(draw_weighted_facility, mo, seed_input, weighted_fac):
    _fig = draw_weighted_facility(
        weighted_fac,
        title=f"Weighted Multi-Wing Facility — Seed {int(seed_input.value)}"
    )
    mo.vstack([
        mo.as_html(_fig),
        mo.md(
            f"**{weighted_fac['n_wings']} wings** · "
            f"{len(weighted_fac['junctions'])} inter-wing corridors · "
            f"{len(weighted_fac['supplies'])} supply units"
        ),
    ])
    return


@app.cell
def cost_model_summary(mo, weighted_fac):
    _rows = ""
    for _w, (_name, _model) in enumerate(
            zip(weighted_fac['wing_names'], weighted_fac['cost_models'])):
        _rows += f"| Wing {_name} | {_model} |\n"
    _rows += "| Inter-wing corridors | Fixed (cost = 1) |\n"

    mo.md(f"""
    ### Cost Models for Your Facility

    | Wing | Cost Model |
    |------|------------|
    {_rows}

    > **Wing Beta reminder:** cost = 1 + floor(max column index / 3).
    > Columns 0–2 cost 1, columns 3–5 cost 2, columns 6–8 cost 3, column 9 costs 4.

    > **Wing Gamma+ reminder:** corridor weights are fixed per your seed —
    > they are shown in the visualisation above (colour scale).
    """)
    return


@app.cell
def original_responses_display(SAVE_FILE_A01, json, mo, os):
    """Show A01 responses as read-only reference."""

    _keys = [
        ("A1_REV",        "A1 — Data model revision"),
        ("A2_REV",        "A2 — Traversal algorithm revision"),
        ("A3_REV_pseudo",  "A3 — Revised pseudocode"),
        ("A3_REV_code",    "A3b — Revised implementation"),
        ("A4_REV",        "A4 — Justification revision"),
    ]
    if os.path.exists(SAVE_FILE_A01):
        with open(SAVE_FILE_A01, 'r') as _f:
            _a01 = json.load(_f)
        _items = {}
        for _k, _label in _keys:
            _val = _a01.get(_k, "*(not saved)*")
            _items[_label] = mo.md(f"```\n{_val}\n```")
    else:
        _items = {"Note": mo.md("*`responses_A01.json` not found — run your A01 workbook first.*")}

    mo.accordion({"📋 Your Amendment A01 Responses (read-only reference)": mo.vstack(
        [mo.vstack([mo.md(f"**{lbl}**"), val]) for lbl, val in _items.items()]
    )})
    return


@app.cell
def action_a21_header(mo):
    mo.md("""
    ---
    ## Action A2-1 — Revise Data Model for Weighted Edges
    *Criterion 3 · 150–300 words*

    Revise your data model to represent non-uniform corridor costs.

    Address each of the following:
    - Which ADT definitions from your A01 model need to change to support weighted edges?
    - How are edge weights stored and retrieved?
      (Property of the edge? Separate lookup? Computed on demand?)
    - How is the **per-wing cost model** represented — does your ADT treat
      Wing Beta and Wing Gamma differently, or does it store all weights uniformly
      computed at construction time?
    - Justify your design choice.
    """)
    return


@app.cell
def action_a21_input(mo):
    a21_input = mo.ui.text_area(
        label="[A2-1-REVISED] Data model revision",
        placeholder="Describe your revised data model for weighted edges...",
        rows=10,
        full_width=True,
    )
    a21_input
    return (a21_input,)


@app.cell
def action_a21_display(a21_input, mo):
    if a21_input.value.strip():
        mo.callout(
            mo.md(f"**[A2-1-REVISED]** {a21_input.value}"),
            kind="info"
        )
    else:
        mo.callout(mo.md("*No response yet.*"), kind="warn")
    return


@app.cell
def action_a22_header(mo):
    mo.md("""
    ---
    ## Action A2-2 — Revise Algorithm for Weighted Traversal
    *Criterion 4 · 150–300 words*

    Select and justify a traversal algorithm capable of finding
    minimum-cost paths in your weighted multi-wing facility.

    Your response must:
    - Name and briefly describe your chosen algorithm.
    - Explain why it is **correct** for this problem
      (i.e. why it guarantees minimum-cost paths given the cost models above).
    - Identify the key structural difference from your Memo 01 algorithm.
    - Discuss one limitation or trade-off in this specific context.
    """)
    return


@app.cell
def action_a22_input(mo):
    a22_input = mo.ui.text_area(
        label="[A2-2-REVISED] Algorithm revision",
        placeholder="Name your algorithm, justify correctness, discuss trade-offs...",
        rows=10,
        full_width=True,
    )
    a22_input
    return (a22_input,)


@app.cell
def action_a22_display(a22_input, mo):
    if a22_input.value.strip():
        mo.callout(
            mo.md(f"**[A2-2-REVISED]** {a22_input.value}"),
            kind="info"
        )
    else:
        mo.callout(mo.md("*No response yet.*"), kind="warn")
    return


@app.cell
def action_a23_header(mo):
    mo.md("""
    ---
    ## Action A2-3 — Revised Pseudocode
    *Criterion 4*

    Write revised pseudocode for your weighted traversal algorithm.
    Your pseudocode must clearly show:
    - how edge weights are retrieved during traversal,
    - the priority or ordering mechanism that distinguishes this algorithm from BFS,
    - how the algorithm terminates and returns the optimal route.
    """)
    return


@app.cell
def action_a23_pseudocode(mo):
    a23_pseudo = mo.ui.text_area(
        label="[A2-3-REVISED] Pseudocode",
        placeholder=(
            "function weighted_traverse(graph, entry, exits):\n"
            "    ...\n"
        ),
        rows=16,
        full_width=True,
    )
    a23_pseudo
    return (a23_pseudo,)


@app.cell
def action_a23_display(a23_pseudo, mo):
    if a23_pseudo.value.strip():
        mo.callout(
            mo.md(f"**[A2-3-REVISED]**\n```\n{a23_pseudo.value}\n```"),
            kind="info"
        )
    else:
        mo.callout(mo.md("*No pseudocode yet.*"), kind="warn")
    return


@app.cell
def action_a23b_header(mo):
    mo.md("""
    ---
    ## Action A2-3b — Revised Implementation
    *Criterion 4 · runnable code*

    Implement your weighted traversal algorithm below.
    Run it on your facility and display:
    - the sequence of cells in the optimal route,
    - the cumulative cost at each wing transition,
    - the total route cost.

    The `weighted_fac` variable contains your facility with edge weights applied.
    Use `weighted_fac['wings'][w]` to access wing `w`'s weighted graph.
    Edge weights are stored as `graph[n1][n2]['weight']`.
    """)
    return


@app.cell
def action_a23b_code(mo):
    _starter = """\
    # weighted_fac is available — weighted_fac['wings'][w] is wing w's NetworkX graph
    # Edge weight: weighted_fac['wings'][w][(c1,r1)][(c2,r2)]['weight']
    # Junctions: weighted_fac['junctions']  (list of ((w1,c1,r1),(w2,c2,r2)) pairs, cost=1)
    # Entry: weighted_fac['entry']   Exit A: weighted_fac['exit_a']   Exit B: weighted_fac['exit_b']

    def find_min_cost_route(wfac):
    \"\"\"Return (route, total_cost) for the minimum-cost path from entry to any exit.\"\"\"
    # TODO: implement your weighted traversal algorithm here
    pass

    route, cost = find_min_cost_route(weighted_fac)
    print(f"Route: {route}")
    print(f"Total cost: {cost}")
    """
    a23b_code = mo.ui.code_editor(
        value=_starter,
        language="python",
        label="[A2-3b-REVISED] Implementation",
    )
    a23b_code
    return (a23b_code,)


@app.cell
def action_a23b_runner(mo):
    run_btn = mo.ui.run_button(label="▶ Run implementation")
    run_btn
    return (run_btn,)


@app.cell
def action_a23b_output(
    a23b_code,
    draw_weighted_facility,
    mo,
    run_btn,
    weighted_fac,
):
    mo.stop(not run_btn.value, mo.md("*Press Run to execute your implementation.*"))
    _g = {
        'weighted_fac': weighted_fac,
        'draw_weighted_facility': draw_weighted_facility,
    }
    try:
        exec(a23b_code.value, _g)
        _route = _g.get('route')
        _cost  = _g.get('cost')
        if _route is not None:
            _fig = draw_weighted_facility(
                weighted_fac,
                highlight_path=_route,
                title=f"Optimal Route — Total Cost: {_cost}"
            )
            mo.vstack([
                mo.as_html(_fig),
                mo.callout(
                    mo.md(f"**Route length:** {len(_route)} nodes  |  **Total cost:** {_cost}"),
                    kind="success"
                )
            ])
        else:
            mo.callout(mo.md("Code ran but no `route` variable was set."), kind="warn")
    except Exception as _e:
        mo.callout(mo.md(f"**Error:** `{_e}`"), kind="danger")
    return


@app.cell
def action_a24_header(mo):
    mo.md("""
    ---
    ## Action A2-4 — Evaluate Solution Quality
    *Criterion 5 · 100–200 words*

    Evaluate the quality of your revised solution:
    - Is your algorithm guaranteed to find the **globally optimal** path
      across all wings, given that each wing uses a different cost model?
    - How does Wing Beta's depth-based cost affect whether CRUDY-1 traverses
      it directly versus routing through other wings?
    - Identify one scenario (based on your seed) where the minimum-cost route
      is **not** the shortest-hop route, and explain why.
    """)
    return


@app.cell
def action_a24_input(mo):
    a24_input = mo.ui.text_area(
        label="[A2-4-REVISED] Solution quality evaluation",
        placeholder="Discuss optimality guarantees, Wing Beta depth bias, and a concrete example...",
        rows=10,
        full_width=True,
    )
    a24_input
    return (a24_input,)


@app.cell
def action_a24_display(a24_input, mo):
    if a24_input.value.strip():
        mo.callout(
            mo.md(f"**[A2-4-REVISED]** {a24_input.value}"),
            kind="info"
        )
    else:
        mo.callout(mo.md("*No response yet.*"), kind="warn")
    return


@app.cell
def save_controls(mo):
    save_btn = mo.ui.run_button(label="💾 Save responses to responses_A02.json")
    save_btn
    return (save_btn,)


@app.cell
def save_responses(
    SAVE_FILE_A02,
    a21_input,
    a22_input,
    a23_pseudo,
    a23b_code,
    a24_input,
    datetime,
    json,
    mo,
    save_btn,
    seed_input,
):
    mo.stop(not save_btn.value)
    _data = {
        "seed":           int(seed_input.value),
        "saved_at":       datetime.datetime.now().isoformat(),
        "A21_REV":        a21_input.value,
        "A22_REV":        a22_input.value,
        "A23_REV_pseudo": a23_pseudo.value,
        "A23_REV_code":   a23b_code.value,
        "A24_REV":        a24_input.value,
    }
    with open(SAVE_FILE_A02, 'w') as _f:
        json.dump(_data, _f, indent=2)
    mo.callout(
        mo.md(f"✅ Saved to `{SAVE_FILE_A02}` at {_data['saved_at'][:19]}"),
        kind="success"
    )
    return


@app.cell
def footer(mo):
    mo.md("""
    ---

    *End of Amendment Memo A02 workbook — submit at **Observation 5**.*

    **Before submitting, check:**
    - [ ] Your seed matches your Memo 01 cover sheet
    - [ ] Your A01 responses are visible in the reference section above
    - [ ] **[A2-1-REVISED]** — data model supports weighted edges with per-wing cost model
    - [ ] **[A2-2-REVISED]** — algorithm handles weighted traversal; choice is justified
    - [ ] **[A2-3-REVISED]** — pseudocode shows priority mechanism and weight retrieval
    - [ ] **[A2-3b-REVISED]** — implementation runs and displays route + total cost
    - [ ] **[A2-4-REVISED]** — quality evaluation addresses optimality and a concrete example
    - [ ] All responses saved to `responses_A02.json`

    *Your Memo 02 workbook will be released separately when Memo 02 begins.*
    """)
    return


if __name__ == "__main__":
    app.run()
