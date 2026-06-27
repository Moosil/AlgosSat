import math
import random
from itertools import chain

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import copy

from tqdm import tqdm
from typing_extensions import runtime

import memo1a_algorithm


class GraphDrawer:
	def __init__(self, seed) -> None:
		self.WING_COLS, self.WING_ROWS = 10, 10

		self.n_wings, self.wing_names, self.wings, self.entry, self.exit_a, self.exit_b, self.supplies, self.junctions = self._get_multi_wing_facility(
			seed
		)

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
				if d == 2 and w_u not in self.supplies and w_u not in {
					self.exit_a, self.exit_b,
					self.entry
				} and w_u not in set(
					chain(*self.junctions)
				):
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

	def draw_multi_wing(
		self, highlight_path=None, node_colors=None,
		supply_collected=None, title="Multi-Wing Facility"
		):
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
				ax.plot(
					[ox + c, ox + c], [0, self.WING_ROWS],
					color=COL_GRID, lw=0.4, zorder=1
					)
			for r in range(self.WING_ROWS + 1):
				ax.plot(
					[ox, ox + self.WING_COLS], [r, r],
					color=COL_GRID, lw=0.4, zorder=1
					)

			# Wing border
			ax.add_patch(
				plt.Rectangle(
					(ox, 0), self.WING_COLS, self.WING_ROWS,
					fill=False, edgecolor=COL_WALL, lw=2.2, zorder=3
				)
			)

			# Wing label
			ax.text(
				ox + self.WING_COLS / 2, self.WING_ROWS + 0.38,
				f"Wing {self.wing_names[w]}",
				ha='center', va='bottom', fontsize=9,
				fontweight='bold', color='#0B1F3B', zorder=8
				)

			# Internal walls (draw where no edge exists)
			for c in range(self.WING_COLS):
				for r in range(self.WING_ROWS):
					if c + 1 < self.WING_COLS and not wing.has_edge((c, r), (c + 1, r)):
						ax.plot(
							[ox + c + 1, ox + c + 1], [r, r + 1],
							color=COL_WALL, lw=1.4, zorder=3
							)
					if r + 1 < self.WING_ROWS and not wing.has_edge((c, r), (c, r + 1)):
						ax.plot(
							[ox + c, ox + c + 1], [r + 1, r + 1],
							color=COL_WALL, lw=1.4, zorder=3
							)

			# Node highlights
			if node_colors:
				for (ww, c, r), color in node_colors.items():
					if ww == w:
						ax.add_patch(
							plt.Rectangle(
								(ox + c, r), 1, 1,
								color=color, alpha=0.5, zorder=2
							)
						)

		# Inter-wing corridors and junction nodes
		for (w1, c1, r1), (w2, c2, r2) in self.junctions:
			x1, y1 = xoff(w1) + c1 + 0.5, r1 + 0.5
			x2, y2 = xoff(w2) + c2 + 0.5, r2 + 0.5
			ax.plot(
				[x1, x2], [y1, y2],
				color=COL_JUNCTION, lw=1.8,
				linestyle='--', alpha=0.7, zorder=4
				)
			ax.plot(x1, y1, 'o', ms=8, color=COL_JUNCTION, zorder=5)
			ax.plot(x2, y2, 'o', ms=8, color=COL_JUNCTION, zorder=5)

		# Supply markers
		for i, (ws, cs, rs) in enumerate(self.supplies):
			ox = xoff(ws)
			already = supply_collected and (ws, cs, rs) in supply_collected
			col = '#AAAAAA' if already else COL_SUPPLY
			mkr = 'x' if already else '*'
			ax.plot(
				ox + cs + 0.5, rs + 0.5,
				marker=mkr, markersize=14, color=col,
				markeredgecolor=COL_ENTRY if not already else '#999',
				markeredgewidth=0.8, zorder=5
				)
			ax.text(
				ox + cs + 0.62, rs + 0.58, f'S{i + 1}',
				fontsize=6, color=COL_WALL, zorder=6
				)

		# Entry marker
		we, ce, re = self.entry
		ox = xoff(we)
		ax.add_patch(
			plt.Circle(
				(ox + ce + 0.5, re + 0.5), 0.28,
				color=COL_ENTRY, zorder=6
			)
		)
		ax.text(
			ox + ce + 0.5, re + 0.5, 'E',
			ha='center', va='center',
			fontsize=6, color='white', fontweight='bold', zorder=7
			)

		# Exit markers
		for lbl, (wx, cx, rx) in [('A', self.exit_a), ('B', self.exit_b)]:
			ox = xoff(wx)
			ax.add_patch(
				plt.Circle(
					(ox + cx + 0.5, rx + 0.5), 0.28,
					color=COL_EXIT, zorder=6
				)
			)
			ax.text(
				ox + cx + 0.5, rx + 0.5, lbl,
				ha='center', va='center',
				fontsize=6, color='white', fontweight='bold', zorder=7
				)

		# Highlight path
		if highlight_path and len(highlight_path) > 1:
			for i in range(len(highlight_path) - 1):
				w1, c1, r1 = highlight_path[i]
				w2, c2, r2 = highlight_path[i + 1]
				ax.plot(
					[xoff(w1) + c1 + 0.5, xoff(w2) + c2 + 0.5],
					[r1 + 0.5, r2 + 0.5],
					color=COL_PATH, lw=1.8, linestyle='--',
					alpha=0.75, zorder=4
				)

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
		ax.legend(
			handles=legend_items, loc='upper left',
			fontsize=7, framealpha=0.9
			)

		ax.set_xlim(-0.5, total_w + 0.5)
		ax.set_ylim(-0.9, self.WING_ROWS + 1.1)
		ax.set_aspect('equal')
		ax.axis('off')
		ax.set_title(
			title, fontsize=11, fontweight='bold',
			color='#0B1F3B', pad=10
			)
		plt.tight_layout()
		return fig


if __name__ == "__main__":
	if False:
		from time import perf_counter_ns as timer

		facility_drawer = GraphDrawer(0)
		abs_graph = facility_drawer.get_abstracted_graph()

		exits = {facility_drawer.exit_a, facility_drawer.exit_b}
		supplies = set(facility_drawer.supplies)
		storage = tuple([None] * 5)
		supply_map = {i: hash(i) for i in facility_drawer.supplies}

		trials = 10
		start = timer()
		for i in range(max(1, trials)):
			res = memo1a_algorithm.ember_rescue(
				abs_graph, facility_drawer.entry,
				exits, supplies,
				storage, supply_map, set()
				)
		end = timer()

		run_time = end - start
		average_time = run_time / trials
		print(f"found walk in {round(average_time)}ns = {round(average_time / 100_000) / 10}ms")

		path = facility_drawer.get_path_from_super_path(res[0])

		print(f"super path: {res}")
		print(f"len of super path: {len(res[0])}")
		print(f"path: {path}")
		print(f"len of path: {len(path)}")

		print(f"entry: {facility_drawer.entry}")
		print(f"exit_a: {facility_drawer.exit_a}")
		print(f"exit_b: {facility_drawer.exit_b}")

		is_correct = path[0] == facility_drawer.entry
		is_correct &= (path[-1] == facility_drawer.exit_a or path[-1] == facility_drawer.exit_b)
		print(f"correctness: {is_correct}")
	else:
		import cProfile, pstats, io
		from pstats import SortKey

		facility_drawer = GraphDrawer(0)
		abs_graph = facility_drawer.get_abstracted_graph()

		exits = {facility_drawer.exit_a, facility_drawer.exit_b}
		supplies = set(facility_drawer.supplies)
		storage = tuple([None] * 5)
		supply_map = {i: hash(i) for i in facility_drawer.supplies}

		pr = cProfile.Profile()
		pr.enable()
		res = memo1a_algorithm.ember_rescue(
			abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set()
			)
		pr.disable()
		sortby = SortKey.CUMULATIVE
		ps = pstats.Stats(pr).sort_stats(sortby)
		print(ps.stats[tuple(next(s for s in ps.stats if 'ember_rescue' in s))][3])

		import tracemalloc

		tracemalloc.start()

		res = memo1a_algorithm.ember_rescue(
			abs_graph, facility_drawer.entry, exits, supplies, storage, supply_map, set()
		)

		snapshot = tracemalloc.take_snapshot()
		top_stats = snapshot.statistics('filename')
		total_mem = sum(stat.size for stat in top_stats if "memo1a_algorithm.py" in stat.traceback._frames[0][0])
		print(f"Total allocated size: {total_mem / 1024:.3f} KiB")

		cProfile.run(r'''memo1a_algorithm.ember_rescue(abs_graph, facility_drawer.entry, {facility_drawer.exit_a, facility_drawer.exit_b}, set(facility_drawer.supplies), tuple([None] * 5), {i: hash(i) for i in facility_drawer.supplies}, set())''')