import heapq

from manim import *
from manim.utils.rate_functions import ease_out_quart, ease_in_quart
from manim_slides.slide import *

from memo1_algorithm_test import GraphDrawer
from memo1_algorithm import get_unfound_supplies

facility_drawer = GraphDrawer()


def get_base_vertex_config(x, y):
    if (x, y) == facility_drawer.exit_a:
        return {"color": "red"}
    elif (x, y) == facility_drawer.exit_b:
        return {"color": "red"}
    elif (x, y) in facility_drawer.supplies:
        return {"color": "blue"}
    elif (x, y) == facility_drawer.entry:
        return {"color": "green"}
    else:
        return {}


def get_square(x, y, scale=1.):
    res = VGroup()

    colour: str = "white"
    if (x, y) == facility_drawer.exit_a:
        res.add(Circle(radius=scale * .75, color="red"))
        res.add(MathTex('x_a', font_size=96 * scale))
    if (x, y) == facility_drawer.exit_b:
        res.add(Circle(radius=scale * .75, color="red"))
        res.add(MathTex('x_b', font_size=96 * scale))
    if (x, y) in facility_drawer.supplies:
        res.add(Circle(radius=scale * .75, color="blue"))
        res.add(MathTex(f"s_{facility_drawer.supplies.index((x, y))}", font_size=96 * scale))
    if (x, y) == facility_drawer.entry:
        res.add(Circle(radius=scale * .75, color="green"))
        res.add(MathTex('e', font_size=96 * scale))

    if not facility_drawer.graph.has_edge((x, y), (x + 1, y)):
        res.add(Line((scale, -scale, 0), (scale, scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((scale, -scale, 0), (scale, scale, 0), color=[0, 0, 0, 0], buff=0.))

    if not facility_drawer.graph.has_edge((x, y), (x - 1, y)):
        res.add(Line((-scale, -scale, 0), (-scale, scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((-scale, -scale, 0), (-scale, scale, 0), color=[0, 0, 0, 0], buff=0.))

    if not facility_drawer.graph.has_edge((x, y), (x, y + 1)):
        res.add(Line((-scale, scale, 0), (scale, scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((-scale, scale, 0), (scale, scale, 0), color=[0, 0, 0, 0], buff=0.))

    if not facility_drawer.graph.has_edge((x, y), (x, y - 1)):
        res.add(Line((-scale, -scale, 0), (scale, -scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((-scale, -scale, 0), (scale, -scale, 0), color=[0, 0, 0, 0], buff=0.))

    return res


def pq_len(pq: list) -> int:
    return len(set(pq))

def get_mobj_edge(g: Graph, u, v):
    if (u, v) in g.edges:
        return u, v
    elif (v, u) in g.edges:
        return v, u
    return None

def get_vert_name(v) -> str:
    if v == facility_drawer.entry:
        return "e"
    elif v == facility_drawer.exit_a:
        return "xa"
    elif v == facility_drawer.exit_b:
        return "xb"
    elif v in facility_drawer.supplies:
        return "s" + str(facility_drawer.supplies.index(v))
    else:
        return "fuck this wasn't supposed to happen"


class Memo1(Slide):
    input_supply_storage = ["s2"] + [None] * 4
    supplies = [f"s{i}" for i in range(5)]
    found_supplies = ["s0"]

    def construct(self):
        f = self.get_facility()
        self.play(*[GrowFromCenter(f[i]) for i in range(len(f))])
        self.wait()
        self.next_slide()

        self.clear()
        g0 = self.get_facility_graph()
        g1 = self.get_facility_graph_abstraction()
        self.play(*[ShrinkToCenter(f[i]) for i in range(len(f))],
                  *[GrowFromCenter(g0.vertices[i]) for i in g0.vertices.keys()],
                  *[GrowFromCenter(g0.edges[i]) for i in g0.edges.keys()])
        self.wait()
        self.next_slide()

        self.play(ReplacementTransform(g0, g1))
        self.wait()
        self.next_slide()

        self.play_some_pairs_shortest_paths(g1, get_unfound_supplies(facility_drawer.supplies, {facility_drawer.supplies[i]: self.supplies[i] for i in range(len(facility_drawer.supplies))}, set(self.found_supplies), self.input_supply_storage))

        self.wait(10)

    def play_unfound_supplies(self, scale=1., do_wait=True):
        fs = self.get_found_supplies(scale)
        self.play(Write(fs))
        if do_wait:
            self.wait()
        self.next_slide()

        new_fs_set = MathTex(
            r"S := \{" +
            r",".join([r"\text{``" + s + "''}" for s in self.found_supplies + [ss for ss in self.input_supply_storage if
                                                                               ss not in self.found_supplies and ss is not None]]) +
            r"\}", font_size=36 * scale)
        new_fs_set.move_to(fs[2], aligned_edge=LEFT)
        self.play(Succession(
            fs[3].animate(rate_func=ease_in_quart).move_to(fs[2], aligned_edge=LEFT),
            ReplacementTransform(VGroup(fs[2], fs[3]), new_fs_set, rate_func=ease_out_quart)
        ))
        fs[2] = new_fs_set
        del new_fs_set
        if do_wait:
            self.wait()
        self.next_slide()

        new_fs_vert_set = MathTex(
            r"S := \{" +
            r",".join([r"v_{" + s + r"}" for s in self.found_supplies + [ss for ss in self.input_supply_storage if
                                                                         ss not in self.found_supplies and ss is not None]]) +
            r"\}", font_size=36 * scale)
        new_fs_vert_set.move_to(fs[1], aligned_edge=LEFT)
        self.play(Succession(
            fs[2].animate(rate_func=ease_in_quart).move_to(fs[1], aligned_edge=LEFT),
            ReplacementTransform(VGroup(fs[1], fs[2]), new_fs_vert_set, rate_func=ease_out_quart)
        ))
        fs[1] = new_fs_vert_set
        del new_fs_vert_set
        if do_wait:
            self.wait()
        self.next_slide()

        new_vert_set = MathTex(
            r"V_s := \{" +
            r",".join([r"v_{" + s + r"}" for s in self.supplies if
                       s not in self.found_supplies + [ss for ss in self.input_supply_storage if
                                                       ss not in self.found_supplies and ss is not None]]) +
            r"\}", font_size=36 * scale)
        new_vert_set.move_to(fs[0], aligned_edge=LEFT)
        self.play(Succession(
            fs[1].animate(rate_func=ease_in_quart).move_to(fs[0], aligned_edge=LEFT),
            ReplacementTransform(VGroup(fs[0], fs[1]), new_vert_set, rate_func=ease_out_quart)
        ))
        fs[0] = new_vert_set
        del new_vert_set
        if do_wait:
            self.wait()
        self.next_slide()

    def play_some_pairs_shortest_paths(self, g: Graph, unfound_supplies: set, scale=1., do_wait=True):
        self.play(g.animate.move_to(LEFT * 3.5))

        sources = self.supplies + ["e"]
        inner_sources = [r"v_{" + v + "}" for v in sources]
        for i in range(len(inner_sources) - 1, 0, -1):
            inner_sources.insert(i, r",\ ")
        sources_mobj = MathTex(r"\text{sources} := [\ ", *inner_sources, r"\ ]", font_size=36 * scale).next_to(g, RIGHT,
                                                                                                               .4)

        sinks = self.supplies + ["xa", "xb"]
        inner_sinks = [r"v_{" + v + "}" for v in sinks]
        for i in range(len(inner_sinks) - 1, 0, -1):
            inner_sinks.insert(i, r",\ ")
        sinks_mobj = MathTex(r"\text{sinks} := [\ ", *inner_sinks, r"\ ]", font_size=36 * scale).next_to(sources_mobj,
                                                                                                         DOWN, .1, LEFT)

        VGroup(sources_mobj, sinks_mobj).move_to((0, 0, 0), ORIGIN, (0, 1, 0))

        self.play(Write(sources_mobj), Write(sinks_mobj))
        if do_wait:
            self.wait()
        self.next_slide()

        source = sources[0]
        source_mobj = MathTex(r"\text{source} := v_{" + source + "}", font_size=36 * scale).next_to(sinks_mobj, DOWN,
                                                                                                    .1, LEFT)
        source_vertex_mobj = g.vertices[facility_drawer.supplies[0]]

        sinks = [v for v in self.supplies + ["xa", "xb"] if v != source]
        inner_sinks = [r"v_{" + v + "}" for v in sinks]
        for i in range(len(inner_sinks) - 1, 0, -1):
            inner_sinks.insert(i, r",\ ")
        new_sinks_mobj = MathTex(r"\text{sinks} := [\ ", *inner_sinks, r"\ ]", font_size=36 * scale).next_to(
            sources_mobj, DOWN, .1, LEFT)
        new_sinks_mobj.move_to(sinks_mobj, aligned_edge=LEFT)

        self.play(AnimationGroup(Indicate(sources_mobj[1]), Write(source_mobj),
                                 ReplacementTransform(sinks_mobj, new_sinks_mobj)))
        self.play(Succession(
            AnimationGroup(
                VGroup(sources_mobj, new_sinks_mobj, source_mobj).animate.move_to((0, 0, 0), ORIGIN, (0, 1, 0))),
            AnimationGroup(Uncreate(sources_mobj),
                           VGroup(new_sinks_mobj, source_mobj).animate.move_to((0, 0, 0), ORIGIN, (0, 1, 0))),
            LaggedStart(FocusOn(source_vertex_mobj), Indicate(source_vertex_mobj), lag_ratio=.4)
        ))
        if do_wait:
            self.wait()
        self.next_slide()

        self.play_dijkstras(g, source_mobj, sinks_mobj, source, facility_drawer.supplies[0],
                            unfound_supplies.difference({source}).union(
                                {facility_drawer.exit_a, facility_drawer.exit_b}), scale, do_wait)

    def play_reconstruct_path(self, g_mobj: Graph, came_from, source) -> list:
        res = []
        reset_colours_v = {}
        reset_colours_e = {}
        curr = source
        prev = None
        while curr in came_from:
            edges = None
            if prev is not None:
                super_path_v = facility_drawer.get_path_from_super_path([prev, curr])
                edges = [get_mobj_edge(g_mobj, super_path_v[i], super_path_v[i + 1]) for i in range(len(super_path_v) - 1)]
            if edges is not None:
                for edge in edges:
                    reset_colours_e[edge] = g_mobj.edges[edge].get_color()
            reset_colours_v[curr] = g_mobj.vertices[curr].get_color()
            animations = []
            if edges is not None:
                for i in range(len(edges)):
                    rate_func = ease_in_quart if i == 0 else (ease_out_quart if i == len(edges) - 1 else linear)
                    animations.append(g_mobj.edges[edges[i]].animate(run_time=.1, rate_func=rate_func).set_color(TEAL))
            animations.append(g_mobj.vertices[curr].animate(run_time=.1).set_color(TEAL))
            self.play(Succession(*animations))

            res.append(curr)
            prev = curr
            curr = came_from[curr]
        res.reverse()
        for v in reset_colours_v:
            g_mobj.vertices[curr].set_color(reset_colours_v[v])
        for e in reset_colours_e:
            g_mobj.edges[e].set_color(reset_colours_e[e])
        return res

    def play_dijkstras(self, g_mobj: Graph, source_mobj: MathTex, sinks_mobj: MathTex, source_name: str, source_vertex,
                       sinks: set, scale=1., do_wait=True):
        abs_graph = facility_drawer.get_abstracted_graph()

        res = {}
        dist = {s: float('infinity') for s in abs_graph}
        dist[source_vertex] = 0

        # visited set replaced update(PQ, v)
        visited = set()

        prev = {}
        pq = [(0., source_vertex)]
        heapq.heapify(pq)

        res_mobj = MathTex(r"\text{res} := \varnothing", font_size=36 * scale).next_to(source_mobj, DOWN, .1, LEFT)
        dist_mobj = MathTex(r"\text{dist} := \{ \dots \}", font_size=36 * scale).next_to(res_mobj, DOWN, .1, LEFT)
        prev_mobj = MathTex(r"prev := \{ \dots \}", font_size=36 * scale).next_to(dist_mobj, DOWN, .1, LEFT)
        pq_mobj = MathTex(r"\text{pq} := [\ " + source_name + r"\ ]", font_size=36 * scale).next_to(prev_mobj, DOWN, .1,
                                                                                                   LEFT)
        VGroup(sinks_mobj, source_mobj, res_mobj, dist_mobj, prev_mobj, pq_mobj).move_to((0, 0, 0), ORIGIN, (0, 1, 0))

        self.play(Write(res_mobj), Write(dist_mobj), Write(prev_mobj), Write(pq_mobj))
        if do_wait:
            self.wait()
        self.next_slide()

        _, u = heapq.heappop(pq)
        visited.add(u)

        u_mobj = MathTex(r"u := " + source_name, font_size=36 * scale).next_to(pq_mobj, DOWN, .1, LEFT)
        new_pq_mobj = MathTex(r"\text{pq} := [\ ]", font_size=36 * scale).move_to(pq_mobj, aligned_edge=LEFT)
        self.play(Succession(
            AnimationGroup(g_mobj.vertices[u].animate.set_color(YELLOW), ReplacementTransform(pq_mobj, new_pq_mobj)),
            AnimationGroup(Write(u_mobj),
                           VGroup(res_mobj, dist_mobj, prev_mobj, new_pq_mobj, u_mobj).animate.move_to((0, 0, 0), ORIGIN,
                                                                                              (0, 1, 0)))
        ))
        pq_mobj = new_pq_mobj
        if do_wait:
            self.wait()
        self.next_slide()

        for v in abs_graph.neighbors(u):
            self.play(Indicate(g_mobj.vertices[v]))
            w = abs_graph.get_edge_data(u, v)["weight"]
            if dist[u] + w < dist[v]:
                prev[v] = u
                dist[v] = dist[u] + w
                old_len = pq_len(pq)
                heapq.heappush(pq, (dist[v], v))
                if old_len == 0 and pq_len(pq) > 0:
                    new_pq_mobj = MathTex(r"\text{pq} := [\ \dots\ ]", font_size=36 * scale).move_to(pq_mobj,
                                                                                                     aligned_edge=LEFT)
                    self.play(ReplacementTransform(pq_mobj, new_pq_mobj))
                    pq_mobj = new_pq_mobj
                elif old_len > 0 and pq_len(pq) == 0:
                    new_pq_mobj = MathTex(r"\text{pq} := [\ ]", font_size=36 * scale).move_to(pq_mobj,
                                                                                              aligned_edge=LEFT)
                    self.play(ReplacementTransform(pq_mobj, new_pq_mobj))
                    pq_mobj = new_pq_mobj

        if do_wait:
            self.wait()
        self.next_slide()

        while len(pq) > 0:
            old_len = pq_len(pq)

            _, u = heapq.heappop(pq)
            new_u_mobj = MathTex(r"u := " + source_name, font_size=36 * scale).move_to(u_mobj, aligned_edge=LEFT)
            self.play(ReplacementTransform(u_mobj, new_u_mobj, run_time=.1))
            u_mobj = new_u_mobj

            # required for the python heapq that:esn't allow changing priority
            if u in visited:
                continue
            visited.add(u)

            if old_len == 0 and pq_len(pq) > 0:
                new_pq_mobj = MathTex(r"\text{pq} := [\ \dots\ ]", font_size=36 * scale).move_to(pq_mobj,
                                                                                                 aligned_edge=LEFT)
                self.play(ReplacementTransform(pq_mobj, new_pq_mobj, run_time=.1))
                pq_mobj = new_pq_mobj
            elif old_len > 0 and pq_len(pq) == 0:
                new_pq_mobj = MathTex(r"\text{pq} := [\ ]", font_size=36 * scale).move_to(pq_mobj, aligned_edge=LEFT)
                self.play(ReplacementTransform(pq_mobj, new_pq_mobj, run_time=.1))
                pq_mobj = new_pq_mobj
            super_path_v = facility_drawer.get_path_from_super_path([prev[u], u])
            self.play(g_mobj.vertices[u].animate(run_time=.1).set_color(YELLOW),
                      *[g_mobj.edges[get_mobj_edge(g_mobj, super_path_v[i+1], super_path_v[i])].animate(run_time=.1).set_color(YELLOW) for i in range(len(super_path_v) - 1)])

            if u in sinks:
                res[u] = [source_vertex] + self.play_reconstruct_path(g_mobj, prev, u)
                new_res_mobj = MathTex(r"\text{res} := \{" + ",".join(
                    (r"v_{" + source_name + r"}: v_{" + source_name + r"} \rightsquigarrow v_{" + get_vert_name(v) + r"}" for v in
                     res.keys())) + r"\}", font_size=36 * scale).move_to(pq_mobj, aligned_edge=LEFT)
                self.play(ReplacementTransform(res_mobj, new_res_mobj, run_time=.1))
                res_mobj = new_res_mobj
                if do_wait:
                    self.wait()
                self.next_slide()
                if len(res) == len(sinks):
                    return res

            for v in abs_graph.neighbors(u):
                self.play(Indicate(g_mobj.vertices[v], run_time=.1))
                w = abs_graph.get_edge_data(u, v)["weight"]
                if dist[u] + w < dist[v]:
                    prev[v] = u
                    dist[v] = dist[u] + w
                    old_len = pq_len(pq)
                    heapq.heappush(pq, (dist[v], v))
                    if old_len == 0 and pq_len(pq) > 0:
                        new_pq_mobj = MathTex(r"\text{pq} := [\ \dots\ ]", font_size=36 * scale).move_to(pq_mobj,
                                                                                                         aligned_edge=LEFT)
                        self.play(ReplacementTransform(pq_mobj, new_pq_mobj, run_time=.1))
                        pq_mobj = new_pq_mobj
                    elif old_len > 0 and pq_len(pq) == 0:
                        new_pq_mobj = MathTex(r"\text{pq} := [\ ]", font_size=36 * scale).move_to(pq_mobj,
                                                                                                  aligned_edge=LEFT)
                        self.play(ReplacementTransform(pq_mobj, new_pq_mobj, run_time=.1))
                        pq_mobj = new_pq_mobj

        return res

    @staticmethod
    def get_facility(scale=1.):
        SCALE_MOD = .25
        scale *= SCALE_MOD
        min_x = min([x for x, y in facility_drawer.graph.nodes])
        max_x = max([x for x, y in facility_drawer.graph.nodes])
        sorted_nodes = [(x, y) for x, y in facility_drawer.graph.nodes]
        sorted_nodes.sort(key=lambda x: x[1], reverse=True)
        boxes = VGroup(*[get_square(x, y, scale) for x, y in sorted_nodes])
        boxes.arrange_in_grid(rows=max_x - min_x + 1, buff=0.)
        return boxes

    @staticmethod
    def get_facility_graph(scale=1.):
        SCALE_MOD = .5
        scale *= SCALE_MOD

        min_x = min([x for x, y in facility_drawer.graph.nodes])
        max_x = max([x for x, y in facility_drawer.graph.nodes])
        offset = (max_x - min_x) / 2 * scale

        g = Graph(facility_drawer.graph.nodes, [e for e in facility_drawer.graph.edges],
                  vertex_config={(x, y): get_base_vertex_config(x, y) for x, y in facility_drawer.graph.nodes})

        for x, y in facility_drawer.graph.nodes:
            g[(x, y)].move_to((x * scale - offset, y * scale - offset, 0.))
        g.update_edges(g)
        return g

    @staticmethod
    def get_facility_graph_abstraction(scale=1.):
        SCALE_MOD = .5
        scale *= SCALE_MOD

        abs_graph = facility_drawer.get_abstracted_graph()
        min_x = min([x for x, y in facility_drawer.graph.nodes])
        max_x = max([x for x, y in facility_drawer.graph.nodes])
        offset = (max_x - min_x) / 2 * scale

        g = Graph(facility_drawer.graph.nodes, [e for e in facility_drawer.graph.edges], vertex_config={
            (x, y): {"fill_opacity": 0.} if (x, y) not in abs_graph.nodes else get_base_vertex_config(x, y) for x, y in
            facility_drawer.graph.nodes})

        for x, y in facility_drawer.graph.nodes:
            g[(x, y)].move_to((x * scale - offset, y * scale - offset, 0.))
        g.update_edges(g)
        return g

    def get_found_supplies(self, scale=1.):
        SCALE_MOD = 1.
        scale *= SCALE_MOD
        vg = VGroup()

        def get_supply_array_str(s):
            return r"\text{Null}" if s is None else r"\text{``" + s + "''}"

        s_set = MathTex(
            r"V_s := \{" +
            rf",".join([r"v_{" + s + "}" for s in self.supplies]) +
            r"\}", font_size=36 * scale)

        arr = MathTex(
            r"A := [" +
            ",".join([get_supply_array_str(s) for s in self.input_supply_storage]) +
            "]", font_size=36 * scale)

        s_map = MathTex(
            r"M_s := \{" +
            r"v_{" + self.supplies[0] + r"}: \text{``" + self.supplies[0] + r"''}" +
            r", \dots, "
            r"v_{" + self.supplies[-1] + r"}: \text{``" + self.supplies[-1] + r"''}" +
            r"\}", font_size=36 * scale)

        fs_set = MathTex(
            r"S := \{" +
            rf",".join([r"\text{``" + s + "''}" for s in self.found_supplies]) +
            r"\}", font_size=36 * scale)

        vg.add(s_set)
        vg.add(s_map)
        vg.add(fs_set)
        vg.add(arr)
        vg.arrange(DOWN, aligned_edge=LEFT)
        return vg
