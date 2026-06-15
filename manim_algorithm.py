from manim_slides.slide import *
from manim import *
from memo1_algorithm_test import GraphDrawer

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


class Memo1(Slide):
    input_supply_storage = [None] * 5
    supplies = [f"s{i}" for i in range(5)]
    found_supplies = []

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

        fs = self.get_found_supplies().shift(3. * RIGHT)
        self.play(g1.animate.shift(3.*LEFT), Create(fs))
        self.wait()
        self.next_slide()
        self.wait(10)

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
        def get_supply_array_str(i):
            return r"\text{Null}" if i is None else str(i)
        arr = MathTex(
            r"["+
            ",".join([get_supply_array_str(i) for i in self.input_supply_storage])+
            "]", font_size=36*scale)
        s_map = MathTex(
            r"\{"+
            ",".join(["v_{s"+str(i)+"}" for i in self.supplies])+
            r"\}", font_size=36*scale)
        fs_set = MathTex(
            r"\{"+
            rf",".join([r"\text{\""+str(i)+"\"}" for i in self.found_supplies])+
            r"\}", font_size=36*scale)
        vg.add(arr)
        vg.add(s_map)
        vg.add(fs_set)
        vg.arrange(DOWN)
        return vg