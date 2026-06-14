from manim import ReplacementTransform
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


def get_square(x, y, scale=.25):
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
        res.add(Line((-scale, -scale, 0), (scale, -scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((-scale, -scale, 0), (scale, -scale, 0), color=[0, 0, 0, 0], buff=0.))

    if not facility_drawer.graph.has_edge((x, y), (x - 1, y)):
        res.add(Line((-scale, scale, 0), (scale, scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((-scale, scale, 0), (scale, scale, 0), color=[0, 0, 0, 0], buff=0.))

    if not facility_drawer.graph.has_edge((x, y), (x, y + 1)):
        res.add(Line((scale, scale, 0), (scale, -scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((scale, scale, 0), (scale, -scale, 0), color=[0, 0, 0, 0], buff=0.))

    if not facility_drawer.graph.has_edge((x, y), (x, y - 1)):
        res.add(Line((-scale, scale, 0), (-scale, -scale, 0), color=colour, buff=0.))
    else:
        res.add(Line((-scale, scale, 0), (-scale, -scale, 0), color=[0, 0, 0, 0], buff=0.))

    return res


class Memo1(Slide):
    def construct(self):
        f = self.get_facility()
        self.play(GrowFromCenter(f))
        self.next_slide()

        self.clear()
        g0 = self.get_facility_graph()
        g1 = self.get_facility_graph_abstraction()
        self.play(Create(g0))
        self.next_slide()

        self.play(ReplacementTransform(g0, g1))
        self.next_slide()
        self.wait(10)

        self.next_slide()

    @staticmethod
    def get_facility():
        min_x = min([x for x, y in facility_drawer.graph.nodes])
        max_x = max([x for x, y in facility_drawer.graph.nodes])
        boxes = VGroup(*[get_square(x, y) for x, y in facility_drawer.graph.nodes])
        boxes.arrange_in_grid(rows=max_x - min_x + 1, buff=0.)
        return boxes

    @staticmethod
    def get_facility_graph(scale=.5):
        min_x = min([x for x, y in facility_drawer.graph.nodes])
        max_x = max([x for x, y in facility_drawer.graph.nodes])
        offset = (max_x - min_x) / 2 * scale
        g = Graph(facility_drawer.graph.nodes, [e for e in facility_drawer.graph.edges],
                  vertex_config={(x, y): get_base_vertex_config(x, y) for x, y in facility_drawer.graph.nodes})
        for x, y in facility_drawer.graph.nodes:
            g[(x, y)].move_to([x * scale - offset, y * scale - offset, 0])
        return g

    @staticmethod
    def get_facility_graph_abstraction(scale=.5):
        abs_graph = facility_drawer.get_abstracted_graph()
        min_x = min([x for x, y in facility_drawer.graph.nodes])
        max_x = max([x for x, y in facility_drawer.graph.nodes])
        offset = (max_x - min_x) / 2 * scale
        g = Graph(facility_drawer.graph.nodes, [e for e in facility_drawer.graph.edges], vertex_config={
            (x, y): {"fill_opacity": 0.} if (x, y) not in abs_graph.nodes else get_base_vertex_config(x, y) for x, y in
            facility_drawer.graph.nodes})
        for x, y in facility_drawer.graph.nodes:
            g[(x, y)].move_to([x * scale - offset, y * scale - offset, 0])
        return g
