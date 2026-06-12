import random
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import copy

import memo1_algorithm


class GraphDrawer:
    def __init__(self) -> None:
        self.graph, self.entry, self.exit_a, self.exit_b, self.supplies = self._get_facility(28122007)

    def _neighbours(self, cols, rows, c, r):
        for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nc, nr = c + dc, r + dr
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
            (0, cols // 2, 0, rows // 2),
            (cols // 2, cols, 0, rows // 2),
            (0, cols // 2, rows // 2, rows),
            (cols // 2, cols, rows // 2, rows),
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
        entry = (0, 0)
        exit_a = (COLS - 1, ROWS - 1)
        exit_b = (COLS - 1, 0)
        reserved = {entry, exit_a, exit_b}
        rng2 = random.Random(int(seed))
        supplies = self._place_supplies(graph, COLS, ROWS, rng2, reserved)
        return graph, entry, exit_a, exit_b, supplies

    def _draw_facility(self, graph, entry, exit_a, exit_b, supplies,
                       highlight_path=None, title="Facility Layout",
                       node_colors=None, supply_collected=None,
                       figsize=(8, 8)):
        COLS, ROWS = 12, 12
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

        fig, ax = plt.subplots(figsize=figsize)
        ax.set_facecolor(COL_BG)
        fig.patch.set_facecolor(COL_BG)

        # Grid
        for c in range(COLS + 1):
            ax.plot([c, c], [0, ROWS], color=COL_GRID, lw=0.4, zorder=1)
        for r in range(ROWS + 1):
            ax.plot([0, COLS], [r, r], color=COL_GRID, lw=0.4, zorder=1)

        # Border
        for x0, y0, x1, y1 in [(0, 0, COLS, 0), (COLS, 0, COLS, ROWS), (COLS, ROWS, 0, ROWS), (0, ROWS, 0, 0)]:
            ax.plot([x0, x1], [y0, y1], color=COL_WALL, lw=2.2, zorder=3)

        # Internal walls
        for c in range(COLS):
            for r in range(ROWS):
                if c + 1 < COLS and not graph.has_edge((c, r), (c + 1, r)):
                    ax.plot([c + 1, c + 1], [r, r + 1], color=COL_WALL, lw=1.6, zorder=3)
                if r + 1 < ROWS and not graph.has_edge((c, r), (c, r + 1)):
                    ax.plot([c, c + 1], [r + 1, r + 1], color=COL_WALL, lw=1.6, zorder=3)

        # Highlighted nodes
        if node_colors:
            for node, color in node_colors.items():
                c, r = node
                rect = plt.Rectangle((c, r), 1, 1, color=color, alpha=0.50, zorder=2)
                ax.add_patch(rect)

        # Solution path
        if highlight_path and len(highlight_path) > 1:
            px = [c + 0.5 for c, r in highlight_path]
            py = [r + 0.5 for c, r in highlight_path]
            ax.plot(px, py, color=COL_PATH, lw=1.8, linestyle='--', alpha=0.75, zorder=4)

        # Supply markers
        for i, (sc, sr) in enumerate(supplies):
            already = supply_collected and (sc, sr) in supply_collected
            col = '#AAAAAA' if already else COL_SUPPLY
            mkr = 'x' if already else '*'
            ax.plot(sc + 0.5, sr + 0.5, marker=mkr, markersize=14, color=col,
                    markeredgecolor=COL_ENTRY if not already else '#999',
                    markeredgewidth=0.8, zorder=5)
            ax.text(sc + 0.62, sr + 0.58, f'S{i + 1}', fontsize=6, color=COL_WALL, zorder=6)

        # Entry circle
        ec, er = entry
        ax.add_patch(plt.Circle((ec + 0.5, er + 0.5), 0.22, color=COL_ENTRY, zorder=6))
        ax.text(ec + 0.5, er + 0.5, 'E', ha='center', va='center',
                fontsize=6, color='white', fontweight='bold', zorder=7)

        # Exit circles
        for lbl, node in [('A', exit_a), ('B', exit_b)]:
            xc, xr = node
            ax.add_patch(plt.Circle((xc + 0.5, xr + 0.5), 0.22, color=COL_EXIT, zorder=6))
            ax.text(xc + 0.5, xr + 0.5, lbl, ha='center', va='center',
                    fontsize=6, color='white', fontweight='bold', zorder=7)

        legend_items = [
            mpatches.Patch(color=COL_ENTRY, label='Entry'),
            mpatches.Patch(color=COL_EXIT, label='Exit A / B'),
            mpatches.Patch(color=COL_SUPPLY, label='Supply unit'),
        ]
        if node_colors:
            legend_items += [
                mpatches.Patch(color=COL_VISITED, alpha=0.5, label='Visited'),
                mpatches.Patch(color=COL_FRONTIER, alpha=0.5, label='Frontier'),
                mpatches.Patch(color=COL_CURRENT, alpha=0.7, label='Current'),
            ]
        ax.legend(handles=legend_items, loc='upper left', fontsize=8, framealpha=0.9)
        ax.set_xlim(0, COLS)
        ax.set_ylim(0, ROWS)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=11, fontweight='bold', color='#0B1F3B', pad=10)
        plt.tight_layout()
        return fig

    def draw_facility(self, seed, highlight_path=None, title="Facility Layout",
                      node_colors=None, supply_collected=None, figsize=(8, 8)):
        return self._draw_facility(self.graph, self.entry, self.exit_a, self.exit_b, self.supplies, highlight_path=None,
                                   title="Facility Layout", node_colors=None, supply_collected=None, figsize=(8, 8))


facility_drawer = GraphDrawer()

res = memo1_algorithm.ember_rescue(facility_drawer.get_abstracted_graph(), facility_drawer.entry, {facility_drawer.exit_a, facility_drawer.exit_b}, set(facility_drawer.supplies), {i: str(i) for i in facility_drawer.supplies}, list(), set())

print(f"super path: {res}")
print(f"len of super path: {len(res)}")
print(f"super path: {facility_drawer.get_path_from_super_path(res)}")
print(f"len of super path: {len(facility_drawer.get_path_from_super_path(res)   )}")

print(f"entry: {facility_drawer.entry}")
print(f"exit_a: {facility_drawer.exit_a}")
print(f"exit_b: {facility_drawer.exit_b}")