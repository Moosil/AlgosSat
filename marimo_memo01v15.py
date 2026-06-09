import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
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

    SAVE_FILE = "responses.json"
    return (
        SAVE_FILE,
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


@app.cell(hide_code=True)
def header(mo):
    mo.md("""
    # Operation Emberlight — My SAT Workbook

    | Field | Value |
    |---|---|
    | **Name** | *Rowan Critchett* |
    | **Student number** | *(your number)* |
    | **Facility seed** | *28122007* |
    | **Teacher** | *Kodie Nielsen* |

    > **Authentication note:** This seed identifies your unique facility.
    > It must match your cover sheet. Do not change it after your first submission.

    ---
    **How to use this workbook:**
    - Fill all prompts with your actual responses.
    - Use the interactive tools (graph explorer, algorithm tracer, implementation cell) to
      explore your facility — they are learning tools, not assessed directly.
    - Your written responses in Parts A–D are what is assessed.
    """)
    return


@app.cell(hide_code=True)
def seed_cell(mo):
    seed_input = mo.ui.number(
        value=28122007,
        start=0,
        stop=99999999,
        step=1,
        label="Your facility seed (from your cover sheet)"
    )
    mo.vstack([
        mo.md("### Enter your seed, then press Tab to rebuild the facility."),
        seed_input
    ])
    return (seed_input,)


@app.cell(hide_code=True)
def maze_loader(nx, random, seed_input):
    def _neighbours(cols, rows, c, r):
        for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            nc, nr = c+dc, r+dr
            if 0 <= nc < cols and 0 <= nr < rows:
                yield nc, nr

    def _build_graph(cols, rows, rng):
        visited = [[False] * rows for _ in range(cols)]
        graph = nx.Graph()
        for c in range(cols):
            for r in range(rows):
                graph.add_node((c, r), pos=(c + 0.5, r + 0.5))

        def carve(c, r):
            visited[c][r] = True
            dirs = list(_neighbours(cols, rows, c, r))
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

    def _place_supplies(graph, cols, rows, rng, reserved):
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

    def get_facility(seed):
        COLS, ROWS = 12, 12
        rng = random.Random(int(seed))
        graph = _build_graph(COLS, ROWS, rng)
        entry  = (0, 0)
        exit_a = (COLS-1, ROWS-1)
        exit_b = (COLS-1, 0)
        reserved = {entry, exit_a, exit_b}
        rng2 = random.Random(int(seed))
        supplies = _place_supplies(graph, COLS, ROWS, rng2, reserved)
        return graph, entry, exit_a, exit_b, supplies

    fac_graph, fac_entry, fac_exit_a, fac_exit_b, fac_supplies = \
        get_facility(seed_input.value)
    return fac_entry, fac_exit_a, fac_exit_b, fac_graph, fac_supplies


@app.cell(hide_code=True)
def drawing_utils(mpatches, plt):
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

    def draw_facility(graph, entry, exit_a, exit_b, supplies,
                      highlight_path=None, title="Facility Layout",
                      node_colors=None, supply_collected=None,
                      figsize=(8, 8)):
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

    return COL_CURRENT, COL_FRONTIER, COL_VISITED, draw_facility


@app.cell(hide_code=True)
def visualiser(
    draw_facility,
    fac_entry,
    fac_exit_a,
    fac_exit_b,
    fac_graph,
    fac_supplies,
    mo,
    seed_input,
):
    facility_fig = draw_facility(
        fac_graph, fac_entry, fac_exit_a, fac_exit_b, fac_supplies,
        title=f"Facility Layout — Seed {int(seed_input.value)}"
    )
    mo.vstack([
        mo.md(f"**Facility loaded.** "
              f"{fac_graph.number_of_nodes()} sectors · "
              f"{fac_graph.number_of_edges()} corridors · "
              f"5 supply units"),
        facility_fig
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    # --- Highlight selector ---
    highlight_mode = mo.ui.dropdown(
        options={
            "None (baseline view)": "none",
            "Dead ends (degree 1)": "dead_ends",
            "Junctions (degree 3)": "junctions",
            "Crossroads (degree 4)": "crossroads",
            "Shortest path to Exit A": "path_a",
            "Shortest path to Exit B": "path_b",
        },
        value="None (baseline view)",
        label="Highlight on map"
    )
    return (highlight_mode,)


@app.cell(hide_code=True)
def _(
    COL_CURRENT,
    COL_FRONTIER,
    COL_VISITED,
    draw_facility,
    fac_entry,
    fac_exit_a,
    fac_exit_b,
    fac_graph,
    fac_supplies,
    highlight_mode,
    mo,
    nx,
):
    # --- Compute graph properties ---
    degrees = dict(fac_graph.degree())
    dead_ends   = [node for node, d in degrees.items() if d == 1
                   and node not in {fac_entry, fac_exit_a, fac_exit_b}]
    junctions   = [node for node, d in degrees.items() if d == 3]
    crossroads  = [node for node, d in degrees.items() if d == 4]
    avg_degree  = sum(degrees.values()) / len(degrees)

    sp_to_a = nx.shortest_path_length(fac_graph, fac_entry, fac_exit_a)
    sp_to_b = nx.shortest_path_length(fac_graph, fac_entry, fac_exit_b)
    supply_dists = {
        f"S{i+1}": nx.shortest_path_length(fac_graph, fac_entry, s)
        for i, s in enumerate(fac_supplies)
    }

    all_lengths = dict(nx.all_pairs_shortest_path_length(fac_graph))
    diameter = max(max(lengths.values()) for lengths in all_lengths.values())



    # --- Build explorer_colors based on selection ---
    explorer_colors = {}
    explorer_path = None
    mode = highlight_mode.value

    if mode == "dead_ends":
        for node in dead_ends:
            explorer_colors[node] = COL_FRONTIER
    elif mode == "junctions":
        for node in junctions:
            explorer_colors[node] = COL_VISITED
    elif mode == "crossroads":
        for node in crossroads:
            explorer_colors[node] = COL_CURRENT
    elif mode == "path_a":
        explorer_path = nx.shortest_path(fac_graph, fac_entry, fac_exit_a)
        for node in explorer_path:
            explorer_colors[node] = COL_VISITED
    elif mode == "path_b":
        explorer_path = nx.shortest_path(fac_graph, fac_entry, fac_exit_b)
        for node in explorer_path:
            explorer_colors[node] = COL_VISITED

    explorer_fig = draw_facility(
        fac_graph, fac_entry, fac_exit_a, fac_exit_b, fac_supplies,
        highlight_path=explorer_path,
        node_colors=explorer_colors if explorer_colors else None,
        title=f"Graph Explorer — {highlight_mode.value}"
    )

    supply_dist_str = " · ".join(f"{k}: {v} steps" for k, v in supply_dists.items())

    mo.vstack([
        mo.md("## 🔍 Graph Property Explorer"),
        mo.callout(mo.md(
            "Use this tool to understand your facility **before** you write your response. "
            "The properties below are real data about your graph — they should inform your ADT design and algorithm choice."
        ), kind="info"),
        mo.hstack([
            mo.stat(label="Sectors (nodes)",    value=str(fac_graph.number_of_nodes())),
            mo.stat(label="Corridors (edges)",  value=str(fac_graph.number_of_edges())),
            mo.stat(label="Dead ends",          value=str(len(dead_ends))),
            mo.stat(label="Junctions (deg 3)",  value=str(len(junctions))),
            mo.stat(label="Crossroads (deg 4)", value=str(len(crossroads))),
            mo.stat(label="Avg degree",         value=f"{avg_degree:.2f}"),
            mo.stat(label="Diameter",           value=str(diameter)),
        ], gap=1, wrap=True),
        mo.md(f"""
    **Shortest paths from Entry:**
    - To Exit A: **{sp_to_a} steps**
    - To Exit B: **{sp_to_b} steps**
    - {supply_dist_str}
        """),
        mo.md("**Highlight a node type or path on the map:**"),
        highlight_mode,
        explorer_fig,
        mo.callout(mo.md("""
    **Inquiry questions — think about these before writing Part A:**

    1. Your facility is a **tree** (exactly one path between any two nodes). How does this
       affect which ADT you choose, and how does it affect the difficulty of the routing problem?
    2. The **diameter** of a graph is the longest shortest path between any two nodes.
       What does a large diameter tell you about how hard the facility is to navigate?
    3. Dead-end sectors have degree 1. Why might supply units being placed at dead ends
       make the navigation problem harder?
    4. If you added more corridors (increasing average degree), how would that affect
       the number of possible routes CRUDY-1 could take?
    5. **Research:** Look up the difference between an *adjacency list* and an *adjacency matrix*.
       Which one does NetworkX use internally, and which would be more efficient for a sparse graph like this?
        """), kind="neutral"),
    ])
    return


@app.cell(hide_code=True)
def part_a_header(mo):
    mo.md("""
    ---
    ## Part A — Problem Specification
    *Criterion 1 · Observation 1 · Design artefact (no fixed word count)*

    > Your task here is **precision**, not length. A single well-defined ADT operation
    > signature is worth more than two paragraphs of vague description.
    > Use the Graph Explorer above to help you understand what you are modelling.
    """)
    return


@app.cell(hide_code=True)
def part_a1(mo):
    mo.md("""
    ### A1. Algorithmic problem statement

    Formulate the algorithmic problem precisely. A strong problem statement has three parts:
    **inputs**, **outputs**, and **constraints** — stated formally, not in narrative form.

    **Guiding questions:**
    - What data does the algorithm receive? (Not "the facility" — be specific: what type, what structure?)
    - What does a *correct* output look like? Is it a path? A sequence of decisions? A cost?
    - Which of the mission constraints from Memo 01 must appear in the problem specification?
    - Can you state a constraint as a mathematical inequality or a set membership condition?

    > **Tip:** Try writing your problem statement in the form:
    > *"Given [inputs], find [output] such that [constraints are satisfied]."*
    """)
    return


@app.cell(hide_code=True)
def _(SAVE_FILE, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as _f:
            _all = json.load(_f)
        if _all:
            _saved = _all[-1].get("A1 response", "")

    response_input1 = mo.ui.text_area(
        label="**Enter your response**",
        value=_saved,  # ← Loads saved text
        rows=8, full_width=True
    )

    save_button = mo.ui.button(value=1, label="💾 Save", on_click= lambda value:value+1)  # No-op; we track clicks via value changes)

    mo.vstack([
        response_input1,
        save_button
    ])
    return response_input1, save_button


@app.cell
def _(mo, response_input1):


    mo.vstack([
        mo.callout(
            mo.md(f"**Your saved response:** " + response_input1.value if response_input1.value else "*No response yet*"),
            kind="success"
        ),
    ])
    return


@app.cell
def _(
    SAVE_FILE,
    code_editor,
    datetime,
    json,
    os,
    pseudocode_editor,
    response_input1,
    response_input2,
    response_input3,
    response_input4,
    response_input5,
    response_input6,
    save_button,
):


    if save_button.value > 0:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                all_responses = json.load(f)
        else:
            all_responses = []

        all_responses.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "A1 response": response_input1.value,
            "A2 response": response_input2.value,
            "A3 response": response_input3.value,
            "B1 response": response_input4.value,
            "B2 response": response_input5.value,
            "C1 pseudocode": pseudocode_editor.value,
            "C2 algorithm": code_editor.value,
            "D1 response": response_input6.value,
        })

        with open(SAVE_FILE, "w") as f:
            json.dump(all_responses, f, indent=2)
    return


@app.cell
def part_a2(mo):
    mo.md("""
    ### A2. Salient features

    Identify which features of the real-world scenario must be captured in the model,
    and which can be safely abstracted away.

    **Guiding questions:**
    - A "salient feature" is one that, if omitted, would make your solution incorrect or
      incomplete. What makes a feature salient here?
    - The corridors are physical tunnels, but in your model they become graph edges.
      What properties of the tunnels are salient? What can be ignored?
    - CRUDY-1 has a physical position in the facility. How is "current position" represented
      in your model?
    - Time is not modelled explicitly in Memo 01. Is that a safe abstraction? Why or why not?
    - The supply units have a physical mass, but in Memo 01 they are treated as uniform.
      Is this a salient simplification? What might break if mass were introduced later?
      *(Hint: look ahead to Memo 03.)*

    **Format:** For each salient feature, state (a) what it is, (b) how it is modelled,
    and (c) what is deliberately abstracted away and why.

    ---
    """)
    return


@app.cell(hide_code=True)
def _(SAVE_FILE, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as _f:
            _all = json.load(_f)
        if _all:
            _saved = _all[-1].get("A2 response", "")

    response_input2 = mo.ui.text_area(
        label="**Enter your response**",
        value=_saved,  # ← Loads saved text
        rows=8, full_width=True
    )

    save_button1 = mo.ui.button(value=0, label="💾 Save", on_click= lambda value:value+1)  # No-op; we track clicks via value changes)

    mo.vstack([
        response_input2,
        save_button1
    ])
    return (response_input2,)


@app.cell
def _(mo, response_input2):


    mo.vstack([
        mo.callout(
            mo.md(f"**Your saved response:** " + response_input2.value if response_input2.value else "*No response yet*"),
            kind="success"
        ),
    ])
    return


@app.cell
def part_a3(mo):
    mo.md(r"""
    ### A3. Data model — ADT selection and signatures

    Describe the Abstract Data Types you will use to model the Emberlight facility.
    For each ADT, state: **(1) what real-world entity it models**, **(2) why it is the
    most appropriate ADT for that entity**, and **(3) the signatures of its key operations**.

    **Signature format used in Algorithmics:**
    ```
    operation_name(param: Type, ...) → ReturnType
    ```

    **Example — for a Graph ADT:**
    ```
    add_vertex(v: Vertex) → None
    add_edge(u: Vertex, v: Vertex) → None
    neighbours(v: Vertex) → Set[Vertex]
    has_edge(u: Vertex, v: Vertex) → Boolean
    vertices() → Set[Vertex]
    ```

    **Guiding questions:**
    - Which ADT models the facility layout? Which models the drone's route?
      Are these the same ADT or different ones?
    - A Queue and a Stack are both linear ADTs. What is the key behavioural difference,
      and does that difference matter for your algorithm?
    - Do you need an ADT to track which supply units have been collected?
      What operations would it need?
    - Is there an ADT that tracks the drone's "path so far"? What operations does it need
      that a plain list might not provide cleanly?
    - For each operation you define: what is the precondition (when is it valid to call it)?
      What is the postcondition (what is guaranteed after it runs)?

    ---
    """)
    return


@app.cell
def _(SAVE_FILE, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as _f:
            _all = json.load(_f)
        if _all:
            _saved = _all[-1].get("A3 response", "")

    response_input3 = mo.ui.text_area(
        label="**Enter your response**",
        value=_saved,  # ← Loads saved text
        rows=8, full_width=True
    )

    save_button2 = mo.ui.button(value=0, label="💾 Save", on_click= lambda value:value+1)  # No-op; we track clicks via value changes)

    mo.vstack([
        response_input3,
        save_button2
    ])
    return (response_input3,)


@app.cell
def _(mo, response_input3):


    mo.vstack([
        mo.callout(
            mo.md(f"**Your saved response:** " + response_input3.value if response_input3.value else "*No response yet*"),
            kind="success"
        ),
    ])
    return


@app.cell
def part_a_research(mo):
    mo.callout(mo.md("""
    ### 🔬 Research & Inquiry — Part A

    The questions below go beyond the assessed response. They are here to
    deepen your understanding and push your thinking further.
    You are not required to answer them in your workbook — but engaging with
    them will make your assessed response stronger.

    **Graph theory:**
    - Your facility is a **spanning tree** of the grid — every node is connected,
      and there are no cycles. How does the absence of cycles affect the uniqueness of
      paths between nodes?
    - Look up the term **graph isomorphism**. Two facilities generated from different seeds
      may be structurally identical even if they look different. What would it mean for two
      facilities to be isomorphic?

    **ADTs and data structures:**
    - In real implementations, a Graph ADT can be backed by an *adjacency list* or
      an *adjacency matrix*. For a 12×12 grid with ~143 edges, which representation
      uses less memory? Calculate it.
    - The Python `networkx` library (used in this workbook) is itself an implementation
      of a Graph ADT. Look at the [NetworkX documentation](https://networkx.org/documentation/stable/)
      and find three operations you used (or could use) that correspond to operations
      in your ADT definition.

    **Real-world connections:**
    - Autonomous robots in warehouses (e.g. Amazon Robotics) navigate using graph models
      of their environment. Research "topological maps in robotics" — how do they differ
      from the grid-graph model you are using?
    - The formal study of ADTs comes from a branch of computer science called
      *abstract algebra* and *type theory*. Look up "algebraic specification of data types"
      and see if you can recognise the connection to how you wrote your signatures.
    """), kind="neutral")
    return


@app.cell
def part_b_header(mo):
    mo.md("""
    ---
    ## Part B — Algorithm Design
    *Criterion 2 · Observation 2 · Word range: 600–800 words*

    > Before you write your response, use the **Algorithm Tracer** below to step through
    > BFS and DFS on your actual facility. Watch how the frontier behaves differently.
    > This direct observation should inform your comparison in B1.
    """)
    return


@app.cell
def algorithm_tracer_controls(fac_graph, mo):
    _n = fac_graph.number_of_nodes()

    algoo = mo.ui.dropdown(
        options={
            "BFS — Breadth-First Search": "BFS",
            "DFS — Depth-First Search":   "DFS",
            "My Algorithm": "CRUDY-1-NPV-1"
        },
        value="BFS — Breadth-First Search",
        label="Algorithm"
    )
    target = mo.ui.dropdown(
        options={"Exit A (top-right corner)": "a", "Exit B (bottom-right corner)": "b"},
        value="Exit A (top-right corner)",
        label="Target"
    )
    step = mo.ui.slider(0, _n - 1, value=0, label="Step (drag to walk through the trace)")
    show_path = mo.ui.checkbox(value=True, label="Show path from Entry to current node")

    mo.vstack([
        mo.md("### 🤖 Algorithm Tracer — step through BFS and DFS on your facility"),
        mo.callout(mo.md(
            "Select an algorithm and drag the slider to walk through each step. "
            "Watch how the **frontier** (yellow) expands differently for BFS vs DFS. "
            "Visited sectors are shown in teal; the current sector in orange."
        ), kind="info"),
        mo.hstack([algoo, target], gap=2),
        step,
        show_path,
    ])
    return algoo, show_path, step, target


@app.cell
def algorithm_tracer(
    COL_CURRENT,
    COL_FRONTIER,
    COL_VISITED,
    algoo,
    deque,
    draw_facility,
    fac_entry,
    fac_exit_a,
    fac_exit_b,
    fac_graph,
    fac_supplies,
    mo,
    show_path,
    step,
    target,
):
    algo   = algoo.value
    target1 = fac_exit_a if target.value == "a" else fac_exit_b

    # --- Compute full trace ---
    steps = []

    if algo == "BFS":
        visited   = set()
        frontier  = deque([fac_entry])
        came_from = {fac_entry: None}
        seen      = {fac_entry}

        while frontier:
            current = frontier.popleft()
            if current in visited:
                continue
            visited.add(current)
            steps.append({
                "current":   current,
                "visited":   frozenset(visited),
                "frontier":  list(frontier),
                "came_from": dict(came_from),
                "done":      current == target,
            })
            if current == target:
                break
            for nb in sorted(fac_graph.neighbors(current)):
                if nb not in seen:
                    seen.add(nb)
                    came_from[nb] = current
                    frontier.append(nb)

    elif algoo == "DFS":  # DFS
        visited   = set()
        stack     = [fac_entry]
        came_from = {fac_entry: None}
        seen      = {fac_entry}

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            steps.append({
                "current":   current,
                "visited":   frozenset(visited),
                "frontier":  list(stack),
                "came_from": dict(came_from),
                "done":      current == target,
            })
            if current == target:
                break
            for nb in sorted(fac_graph.neighbors(current), reverse=True):
                if nb not in seen:
                    seen.add(nb)
                    came_from[nb] = current
                    stack.append(nb)

    total  = len(steps)
    idx    = min(int(step.value), total - 1) if total > 0 else 0
    s      = steps[idx] if steps else None

    if s:
        tracer_colors = {}
        for node1 in s["visited"]:
            tracer_colors[node1] = COL_VISITED
        for node1 in s["frontier"]:
            tracer_colors[node1] = COL_FRONTIER
        tracer_colors[s["current"]] = COL_CURRENT

        tracer_path = []
        if show_path.value:
            node1 = s["current"]
            cf   = s["came_from"]
            while node1 is not None:
                tracer_path.append(node1)
                node1 = cf.get(node1)
            tracer_path.reverse()

        frontier_name = "Queue" if algo == "BFS" else "Stack"
        status_icon   = "✅" if s["done"] else "🔍"
        status_msg    = (f"{status_icon} **Target reached** at step {idx+1}!"
                         if s["done"]
                         else f"{status_icon} Exploring — {frontier_name} size: {len(s['frontier'])}")

        tracer_fig = draw_facility(
            fac_graph, fac_entry, fac_exit_a, fac_exit_b, fac_supplies,
            highlight_path=tracer_path,
            node_colors=tracer_colors,
            title=f"{algo}  ·  Step {idx+1} / {total}  ·  Current: {s['current']}  ·  Visited: {len(s['visited'])}",
        )

        result = mo.vstack([
            mo.md(status_msg),
            tracer_fig,
            mo.md(f"*Path length from Entry: **{len(tracer_path)-1} steps** · "
                  f"{len(s['visited'])} sectors visited · "
                  f"{frontier_name} holds {len(s['frontier'])} nodes*"),
        ])
    else:
        result = mo.md("*No trace available — check that your facility loaded correctly.*")

    result
    return


@app.cell
def part_b1(mo):
    mo.md("""
    ### B1. Consideration of approaches

    Consider **at least two** algorithm design approaches. For each, explain the
    design pattern, assess its suitability for this problem, and identify its limitations.
    Then clearly justify the approach you selected.

    **Approaches to consider (you are not limited to these):**
    - Uninformed search: BFS, DFS
    - Informed search: Greedy best-first, A\*
    - Greedy strategies: nearest-unvisited, nearest-supply-first

    **Guiding questions for each approach:**
    - What is the *strategy* of this algorithm — what decision rule does it use at each step?
    - Does it guarantee finding a path? Does it guarantee finding the *shortest* path?
    - What data structure drives it (queue, stack, priority queue)?
    - How well does it handle the dual objective: collect supplies *and* reach an exit?
    - Does using BFS or DFS on your specific facility (from the tracer above) produce a
      sensible path? Describe what you observed.

    **For your selected approach:**
    - Why is it more appropriate than the alternatives for *this specific problem*?
    - What are its known weaknesses, and are those weaknesses acceptable here?

    ---
    """)
    return


@app.cell
def _(SAVE_FILE, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as _f:
            _all = json.load(_f)
        if _all:
            _saved = _all[-1].get("B1 response", "")

    response_input4 = mo.ui.text_area(
        label="**Enter your response**",
        value=_saved,  # ← Loads saved text
        rows=8, full_width=True
    )
    save_button3 = mo.ui.button(value=0, label="💾 Save", on_click= lambda value:value+1)  # No-op; we track clicks via value changes)

    mo.vstack([
        response_input4,
        save_button3
    ])
    return (response_input4,)


@app.cell
def _(mo, response_input4):


    mo.vstack([
        mo.callout(
            mo.md(f"**Your saved response:** " + response_input4.value if response_input4.value else "*No response yet*"),
            kind="success"
        ),
    ])
    return


@app.cell
def part_b2(mo):
    mo.md("""
    ### B2. Algorithm description

    Describe your chosen algorithm in plain English **before** expressing it as pseudocode.
    This narrative should make your design intent clear to a reader who hasn't seen your code.

    **Guiding questions:**
    - How does CRUDY-1 decide which sector to move to next?
    - In what order does it visit the supply units? Is there a strategy to the order?
    - How does the algorithm know when to head for the exit rather than collecting more supplies?
    - How does the algorithm use the ADT operations you defined in A3?
      Name at least two ADT operations and describe the role they play.
    - Is there a sub-problem within your algorithm that could be separated into its own
      function? What would that function do?

    ---
    """)
    return


@app.cell
def _(SAVE_FILE, json, mo, os):
    _saved = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as _f:
            _all = json.load(_f)
        if _all:
            _saved = _all[-1].get("B2 response", "")

    response_input5 = mo.ui.text_area(
        label="**Enter your response**",
        value=_saved,  # ← Loads saved text
        rows=8, full_width=True
    )

    save_button4 = mo.ui.button(value=0, label="💾 Save", on_click= lambda value:value+1)  # No-op; we track clicks via value changes)

    mo.vstack([
        response_input5,
        save_button4
    ])
    return (response_input5,)


@app.cell
def _(mo, response_input5):


    mo.vstack([
        mo.callout(
            mo.md(f"**Your saved response:** " + response_input5.value if response_input5.value else "*No response yet*"),
            kind="success"
        ),
    ])
    return


@app.cell
def part_b_research(mo):
    mo.callout(mo.md("""
    ### 🔬 Research & Inquiry — Part B

    **Search algorithms — going deeper:**
    - **Dijkstra's algorithm** finds the shortest path in a *weighted* graph. BFS only works
      on *unweighted* graphs (or graphs where all edges have equal weight). Look up Dijkstra's
      algorithm — how does using a priority queue change the order of exploration?
      *(This will become relevant in Memo 02 when edge weights are introduced.)*
    - **A\\* search** is Dijkstra's algorithm with a *heuristic* — an estimate of the remaining
      cost to the goal. A good heuristic for a grid graph is the Manhattan distance.
      Could you use Manhattan distance as a heuristic for the Emberlight problem? What are
      the conditions for a heuristic to be *admissible*?
    - **The Travelling Salesman Problem (TSP):** collecting all five supply units before
      reaching an exit is related to TSP — finding the shortest route that visits a set
      of locations. TSP is NP-hard. Does that mean your problem is NP-hard? Why or why not?

    **Completeness and optimality:**
    - An algorithm is **complete** if it always finds a solution when one exists.
    - An algorithm is **optimal** if it always finds the *best* solution.
    - Is your chosen algorithm complete? Is it optimal? These are separate questions —
      an algorithm can be complete but not optimal (e.g. DFS finds *a* path, not the *shortest*).

    **Real-world connections:**
    - Research "robot path planning" and "occupancy grid navigation". How do real
      autonomous systems handle environments that are not fully known in advance?
    - Look up "Monte Carlo Tree Search (MCTS)". This technique is used in game-playing AI
      (e.g. AlphaGo). Could it be applied to the Emberlight problem? What would the
      "game tree" look like?
    """), kind="neutral")
    return


@app.cell
def part_c_header(mo):
    mo.md("""
    ---
    ## Part C — Pseudocode
    *Criterion 3 · Observation 3*

    > Pseudocode must use **standard Algorithmics conventions** — see the reference below.
    > Your pseudocode must call your ADT operations from Part A by name.
    > It must be modular: use sub-functions or procedures where appropriate.
    """)
    return


@app.cell
def part_c_conventions(mo):
    mo.accordion({
        "📋 Algorithmics pseudocode conventions (click to expand)": mo.md(r"""
    **Structure:**
    ```
    FUNCTION name(param: Type, ...) -> ReturnType
    ...body...
    END FUNCTION

    PROCEDURE name(param: Type, ...)
    ...body...
    END PROCEDURE
    ```

    **Control flow:**
    ```
    IF condition THEN
    ...
    ELSE IF condition THEN
    ...
    ELSE
    ...
    END IF

    FOR each item IN collection DO
    ...
    END FOR

    WHILE condition DO
    ...
    END WHILE
    ```

    **Assignment and return:**
    ```
    variable <- value
    RETURN value
    ```

    **ADT operations (use the names you defined in A3):**
    ```
    neighbours(v)        // returns Set of adjacent vertices
    enqueue(queue, v)    // adds v to back of queue
    dequeue(queue)       // removes and returns front of queue
    push(stack, v)       // adds v to top of stack
    pop(stack)           // removes and returns top of stack
    add(set, v)          // adds v to set
    contains(set, v)     // returns Boolean
    ```

    **Modularity:** define sub-functions for any logical sub-task
    (e.g. `reconstruct_path`, `collect_supply`, `find_nearest_supply`).

    **Comments:** use `//` for inline comments.
        """)
    })
    return


@app.cell
def part_c_pseudocode(mo):
    mo.md(r"""
    ### C1. Algorithm in pseudocode

    Write your complete pseudocode below. Replace the skeleton with your full algorithm.
    Use your ADT operations from A3. Add sub-functions as needed.

    *(Extend and replace the skeleton below with your complete pseudocode.)*
    """)
    return


@app.cell
def _(mo):
    pseudocode_editor = mo.ui.code_editor(
            value="\n".join([
                "FUNCTION ember_rescue(graph: Graph, entry: Vertex,",
                "                      exits: Set[Vertex], supplies: Set[Vertex]) -> Path",
                "",
                "    // Initialise data structures",
                "",
                "    // Main loop",
                "",
                "    // Return the path",
                "",
                "END FUNCTION",
                "",
                "",
                "FUNCTION reconstruct_path(came_from: Map, current: Vertex) -> Path",
                "    ...",
                "END FUNCTION",
            ]),
            min_height=300,
        )
    pseudocode_editor
    return (pseudocode_editor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### C2. Algorithm in pseudocode

    Convert your Pseudocode to python below.

    *(Extend and replace the skeleton below with your complete code.)*
    """)
    return


@app.cell
def _(SAVE_FILE, json, mo, os):
    # Load the most recent saved value if it exists
    _saved_code = ""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as _f:
            _all = json.load(_f)
        if _all:  # If there are any saved entries
            _saved_code = _all[-1].get("C2 algorithm", "")  # Get most recent
    # Fall back to starter code if nothing saved
    if not _saved_code:
        _saved_code = "\n".join([
            "def my_algorithm(graph, entry, exit_a, exit_b, supplies):",
            "    from collections import deque",
            "    # --- Your algorithm here ---",
            "    return path, collected",
        ])

    code_editor = mo.ui.code_editor(
        value=_saved_code,
        language="python",
        min_height=400,
    )
    code_editor
    return (code_editor,)


@app.cell
def _(
    code_editor,
    deque,
    draw_facility,
    fac_entry,
    fac_exit_a,
    fac_exit_b,
    fac_graph,
    fac_supplies,
    mo,
    textwrap,
):
    import types

    _code = textwrap.dedent(code_editor.value)
    _namespace = {"deque": deque}

    try:
        exec(_code, _namespace)
        my_algorithm = _namespace["my_algorithm"]
        _path, _collected = my_algorithm(
            fac_graph, fac_entry, fac_exit_a, fac_exit_b, fac_supplies
        )
        if _path is None or _collected is None:
            raise ValueError("Your algorithm returned None — make sure it has a 'return path, collected' statement at the end.")
        _status = ("ok", _path, _collected)
    except Exception as _e:
        _status = ("error", str(_e), [])

    status_type, data, collected = _status

    if status_type == "error":
        output = mo.callout(
            mo.md(f"**Error in your algorithm:** `{data}`\n\nCheck your code above."),
            kind="danger"
        )
    else:
        algo_path = data
        at_exit = algo_path and (algo_path[-1] == fac_exit_a or algo_path[-1] == fac_exit_b)
        all_edges_valid = all(
            fac_graph.has_edge(algo_path[i], algo_path[i+1])
            for i in range(len(algo_path)-1)
        )
        results_fig = draw_facility(
            fac_graph, fac_entry, fac_exit_a, fac_exit_b, fac_supplies,
            highlight_path=algo_path,
            supply_collected=set(collected),
            title=f"Your Algorithm — Path length: {len(algo_path)-1} steps · "
                  f"Supplies collected: {len(collected)}/5"
        )
        output = mo.vstack([
            mo.md("### C2. Algorithm test results"),
            mo.hstack([
                mo.stat(label="Path length",        value=f"{len(algo_path)-1} steps"),
                mo.stat(label="Supplies collected", value=f"{len(collected)} / 5"),
                mo.stat(label="Ends at exit",       value="✅ Yes" if at_exit else "❌ No"),
                mo.stat(label="All moves valid",    value="✅ Yes" if all_edges_valid else "❌ No"),
            ], gap=1),
            results_fig,
            mo.md(f"**Collected:** {', '.join(f'S{fac_supplies.index(s)+1}' for s in collected) if collected else 'None'}"),
            mo.callout(mo.md("""
    **Reflect on your result:**
    - Does your path collect all 5 supplies, or just some? Is that by design?
    - Is the path you found the *shortest possible* path that collects the same supplies?
    - How does your path compare to the BFS/DFS paths in the Algorithm Tracer above?
            """), kind="info"),
        ])

    output
    return


@app.cell
def part_d_header(mo):
    mo.md("""
    ---
    ## Part D — Solution Justification
    *Criterion 4 · Observation 4 · Word range: 300–500 words*

    > A strong justification does not just assert that your solution is good.
    > It *argues* — using evidence from your algorithm's design and behaviour —
    > that it meets the mission requirements.
    """)
    return


@app.cell
def part_d1(mo):
    mo.md("""
    ### D1. Justification

    Justify your chosen solution by addressing all three dimensions below.
    You must engage with the *specific* Emberlight scenario — generic statements
    about your algorithm that could apply to any problem will not be sufficient.

    **1. Suitability**
    Why is this algorithm appropriate for *this* problem?
    - What properties of the Emberlight facility make your algorithm a natural fit?
    - Consider: does the facility structure (tree, grid, dead-end placements) favour
      your approach? Use evidence from the Graph Explorer.
    - Are there properties of the problem that your algorithm handles *better*
      than the alternatives you considered in B1?

    **2. Coherence**
    How does your algorithm integrate with your data model?
    - Name two ADT operations from Part A and explain exactly how they are used
      in your algorithm (not just "I use a graph" — be specific about which operation,
      when it is called, and what it returns).
    - Are there any tensions between your ADT design and your algorithm? For example,
      does your algorithm require an operation that isn't in your ADT signature?

    **3. Fitness for purpose**
    Does your solution meet the mission directive?
    - Go through each operational constraint from Memo 01 and state explicitly
      whether your solution satisfies it, and how.
    - Are there any constraints your solution *fails* to satisfy? If so, acknowledge
      this honestly and explain whether it is an acceptable trade-off.

    ---
    """)
    return


@app.cell
def _(mo):
    response_input6 = mo.ui.text_area(
        label="**Enter your response  (600 words)**",
        value="",
        rows=8, full_width=True
    )

    save_button5 = mo.ui.button(value=0, label="💾 Save", on_click= lambda value:value+1)  # No-op; we track clicks via value changes)

    mo.vstack([
        response_input6,
        save_button5
    ])
    return (response_input6,)


@app.cell
def _(mo, response_input6):
    mo.vstack([
        mo.callout(
            mo.md(f"**Your saved response:** " + response_input6.value if response_input6.value else "*No response yet*"),
            kind="success"
        ),
    ])
    return


@app.cell
def part_d_reflection(mo):
    mo.callout(mo.md("""
    ### 🔬 Reflection & Extension — Part D

    **Stress-testing your justification:**
    - Construct a specific scenario (a particular facility layout and supply placement)
      where your algorithm performs *poorly*. What would the path look like?
      Does this undermine your justification, or is it an acceptable edge case?
    - Your algorithm was designed for the Memo 01 constraints (uniform edge weights,
      no load penalty). If those assumptions were removed — as they are in Memos 02
      and 03 — which part of your justification would break first?

    **On correctness:**
    - A solution is *correct* if it always satisfies the constraints of the problem
      specification. Can you prove (informally) that your algorithm always terminates?
      Can you prove it always finds *a* valid path (not necessarily the best one)?
    - What is the difference between a solution being *correct* and being *optimal*?
      Is your solution correct? Is it optimal? These are different claims.

    **On fitness for purpose:**
    - The mission directive says "maximise recovered priority while maintaining
      structural integrity and ensuring successful extraction." These three goals
      can conflict. How does your algorithm resolve conflicts between them?
      Is your resolution principled or ad hoc?

    **Research prompt:**
    - Look up **formal program verification**. In safety-critical systems (medical devices,
      aircraft autopilots), software must be *proven* correct — not just tested.
      What would it mean to formally verify the correctness of your algorithm?
    """), kind="neutral")
    return


@app.cell
def footer(mo):
    mo.md("""
    ---
    *End of Memo 01 workbook — submit this notebook at Observation 4.*

    **Before submitting, check:**
    - [ ] Your seed is entered correctly and matches your cover sheet
    - [ ] All four Parts (A, B, C, D) have written responses
    - [ ] Your pseudocode (C1) uses ADT operations from Part A
    - [ ] Your implementation cell (C2) runs without errors
    - [ ] Your justification (D1) addresses all three dimensions

    *Your Memo 02 section will be appended to this file when Memo 02 is released.*
    """)
    return


if __name__ == "__main__":
    app.run()
