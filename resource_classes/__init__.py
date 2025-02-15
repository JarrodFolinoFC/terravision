import contextvars
import os
import sys
import uuid
from pathlib import Path
from typing import List, Union, Dict
#from graphviz import Digraph
from graphviz import Source, Digraph, render
from random import randint

# Global contexts for a resource_classes and a cluster.
# Allowing all nodes to draw to one canvas class

__diagram = contextvars.ContextVar("resource_classes")
__cluster = contextvars.ContextVar("cluster")
defaultdir = 'LR'

#basepath = os.environ.get('resource_images', '/home/username/')
try:
    base_path = sys._MEIPASS
except:
    base_path = Path.cwd()


def getdiagram():
    try:
        return __diagram.get()
    except LookupError:
        return None


def setdiagram(diagram):
    __diagram.set(diagram)


def getcluster():
    try:
        return __cluster.get()
    except LookupError:
        return None


def setcluster(cluster):
    __cluster.set(cluster)


class Canvas:
    __directions = ("TB", "BT", "LR", "RL")
    __curvestyles = ("ortho", "curved")
    __outformats = ("png", "jpg", "svg", "pdf")

    # fmt: off
    _default_graph_attrs = {
        # "pad": "2.0",
        "splines": "true",
        "overlap" : "false",
        "nodesep": "4.5",
        "fontname": "Sans-Serif",
        "fontsize": "30",
        "fontcolor": "#2D3436",
        "labelloc" : "t",
        "concentrate": 'true',
        "ranksep": "5",
        "center": "true",
        "pad" : "1.5",
        "ranksep" :"8",

    }
    _default_node_attrs = {
        "shape": "box",
        "style": "rounded",
        "fixedsize": "true",
        "width": "1.4",
        "height": "1.4",
        "labelloc": "b",
        "imagepos": "c",
        "imagescale": "true",
        "fontname": "Sans-Serif",
        "fontsize": "14",
        "fontcolor": "#2D3436",
        "center": "true",
    }
    _default_edge_attrs = {
        "color": "#7B8894",

    }

    # fmt: on

    # TODO: Label position option
    # TODO: Save directory option (filename + directory?)
    def __init__(
        self,
        name: str = "",
        filename: str = "",
        direction: str = "TB",
        curvestyle: str = "ortho",
        outformat: str = "png",
        show: bool = True,
        graph_attr: dict = {},
        node_attr: dict = {},
        edge_attr: dict = {},
    ):
        """Diagram represents a global resource_classes context.

        :param name: Diagram name. It will be used for output filename if the
            filename isn't given.
        :param filename: The output filename, without the extension (.png).
            If not given, it will be generated from the name.
        :param direction: Data flow direction. Default is 'left to right'.
        :param curvestyle: Curve bending style. One of "ortho" or "curved".
        :param outformat: Output file format. Default is 'png'.
        :param show: Open generated image after save if true, just only save otherwise.
        :param graph_attr: Provide graph_attr dot config attributes.
        :param node_attr: Provide node_attr dot config attributes.
        :param edge_attr: Provide edge_attr dot config attributes.
        """
        self.name = name
        if not name and not filename:
            filename = "resource_classes_image"
        elif not filename:
            filename = "_".join(self.name.split()).lower()
        self.filename = filename
        self.dot = Digraph(self.name, filename=self.filename + '.gv')

        # Set Title of Diagram
        self.dot.graph_attr["label"] = self.name

        # Set Default Graph attributes.
        for k, v in self._default_graph_attrs.items():
            self.dot.graph_attr[k] = v

        # Set Default Node and Edge Attributes
        for k, v in self._default_node_attrs.items():
            self.dot.node_attr[k] = v
        for k, v in self._default_edge_attrs.items():
            self.dot.edge_attr[k] = v

        if not self._validate_direction(direction):
            raise ValueError(f'"{direction}" is not a valid direction')
        self.dot.graph_attr["rankdir"] = direction

        # if not self._validate_curvestyle(curvestyle):
        #     raise ValueError(f'"{curvestyle}" is not a valid curvestyle')
        self.dot.graph_attr["splines"] = curvestyle

        if not self._validate_outformat(outformat) and outformat !='dot':
            raise ValueError(f'"{outformat}" is not a valid output format')
        self.outformat = outformat

        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)
        self.dot.node_attr.update(node_attr)
        self.dot.edge_attr.update(edge_attr)
        self.show = show

    def __str__(self) -> str:
        return str(self.dot)

    def __enter__(self):
        setdiagram(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.render()
        # Remove the graphviz file leaving only the output.
        os.remove(self.filename)
        setdiagram(None)

    def _repr_png_(self):
        return self.dot.pipe(format="png")

    def _validate_direction(self, direction: str) -> bool:
        direction = direction.upper()
        for v in self.__directions:
            if v == direction:
                return True
        return False

    def _validate_curvestyle(self, curvestyle: str) -> bool:
        curvestyle = curvestyle.lower()
        for v in self.__curvestyles:
            if v == curvestyle:
                return True
        return False

    def _validate_outformat(self, outformat: str) -> bool:
        outformat = outformat.lower()
        for v in self.__outformats:
            if v == outformat:
                return True
        return False

    def add_node(self, nodeid: str, label: str, **attrs) -> None:
        """Create a new node."""
        self.dot.node(nodeid, label=label, **attrs)

    def node(self, nodeid: str, label: str, **attrs) -> None:
        """Create a new node."""
        self.dot.node(nodeid, label=label, **attrs)

    def connect(self, node: "Node", node2: "Node", edge: "Edge") -> None:
        """Connect the two Nodes."""
        self.dot.edge(node.nodeid, node2.nodeid, **edge.attrs)

    def subgraph(self, dot: Digraph) -> None:
        """Create a subgraph for clustering"""
        self.dot.subgraph(dot)

    def pre_render(self) -> str:
        return self.dot.render(format='dot', quiet=True, cleanup=False, directory=Path.cwd())
    
    def render(self) -> str:
        dotsource = Source.from_file(self.filename+'.dot', engine='dot', directory=Path.cwd())
        filename = dotsource.render(format=self.outformat, view=self.show, quiet=True, engine='dot', directory=Path.cwd())
        return filename


class Cluster:
    __directions = ("TB", "BT", "LR", "RL")
    __bgcolors = ("#E5F5FD", "#EBF3E7", "#ECE8F6", "#FDF7E3")

    _default_graph_attrs = {
        "shape": "box",
        "style": "rounded",
        "labeljust": "l",
        "pencolor": "black",
        "fontname": "Sans-Serif",
        "fontsize": "14",
    }

    def __init__(
        self, label: str = "cluster", direction: str = "LR", graph_attr: dict = {},
    ):
        """Cluster represents a cluster context.

        :param label: Cluster label.
        :param direction: Data flow direction. Default is 'left to right'.
        :param graph_attr: Provide graph_attr dot config attributes.
        """
        self.label = label
        self.name = "cluster_" + self.__class__.__name__ + "." + str(randint(1, 1000))
        self.dot = Digraph(self.name)
        # Set attributes.
        for k, v in self._default_graph_attrs.items():
            self.dot.graph_attr[k] = v
        self.dot.graph_attr["label"] = self.label
        if not self._validate_direction(direction):
            raise ValueError(f'"{direction}" is not a valid direction')
        self.dot.graph_attr["rankdir"] = direction
        # Node must be belong to a diagrams.
        self._diagram = getdiagram()
        if self._diagram is None:
            raise EnvironmentError("Global diagrams context not set up")
        self._parent = getcluster()
        # Merge passed in attributes
        self.dot.graph_attr.update(graph_attr)

    def __enter__(self):
        setcluster(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._parent:
            self._parent.subgraph(self.dot)
        else:
            self._diagram.subgraph(self.dot)
        setcluster(self._parent)

    def _validate_direction(self, direction: str):
        direction = direction.upper()
        for v in self.__directions:
            if v == direction:
                return True
        return False

    def node(self, nodeid: str, label: str, **attrs) -> None:
        """Create a new node in the cluster."""
        self.dot.node(nodeid, label=label, **attrs)

    def add_node(self, nodeid: str, label: str, **attrs) -> None:
        """Create a new node in the cluster."""
        self.dot.node(nodeid, label=label, **attrs)

    def subgraph(self, dot: Digraph) -> None:
        self.dot.subgraph(dot)
 
 
class Node:
    """Node represents a node for a specific backend service."""

    _provider = None
    _type = None

    _icon_dir = None
    _icon = None

    _height = 1.9

    def __init__(self, label: str = "", **attrs: Dict):
        """Node represents a system component.

        :param label: Node label.
        """
        # Generates an ID for identifying a node.
        self._id = self._rand_id(self, attrs)
        #label = f'< <font color="blue">{label} </font>>'
        self.label = label
        # fmt: off
        padding = 0.4 * (label.count('\n'))
        self._attrs = {
            "shape": "none",
            "tf_resource_name" : "unknown",
            "height": str(self._height + padding),
            "image": self._load_icon(),
            "labelloc": "b"
        } if self._icon else {}

        # fmt: on
        self._attrs.update(attrs)

        # Node must belong to a resource_classes.
        self._diagram = getdiagram()
        if self._diagram is None:
            raise EnvironmentError("Global resource_classes context not set up")
        self._cluster = getcluster()

        # If a node is in the cluster context, add it to cluster.
        if self._cluster:
            self._cluster.node(self._id, self.label, **self._attrs)
        else:
            self._diagram.node(self._id, self.label, **self._attrs)

    def __repr__(self):
        _name = self.__class__.__name__
        return f"<{self._provider}.{self._type}.{_name}>"

    def __sub__(self, other: Union["Node", List["Node"], "Edge"]):
        """Implement Self - Node, Self - [Nodes] and Self - Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self))
            return other
        elif isinstance(other, Node):
            return self.connect(other, Edge(self))
        else:
            other.node = self
            return other

    def __rsub__(self, other: Union[List["Node"], List["Edge"]]):
        """ Called for [Nodes] and [Edges] - Self because list don't have __sub__ operators. """
        for o in other:
            if isinstance(o, Edge):
                o.connect(self)
            else:
                o.connect(self, Edge(self))
        return self

    def __rshift__(self, other: Union["Node", List["Node"], "Edge"]):
        """Implements Self >> Node, Self >> [Nodes] and Self Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self, forward=True))
            return other
        elif isinstance(other, Node):
            return self.connect(other, Edge(self, forward=True))
        else:
            other.forward = True
            other.node = self
            return other

    def __lshift__(self, other: Union["Node", List["Node"], "Edge"]):
        """Implements Self << Node, Self << [Nodes] and Self << Edge."""
        if isinstance(other, list):
            for node in other:
                self.connect(node, Edge(self, reverse=True))
            return other
        elif isinstance(other, Node):
            return self.connect(other, Edge(self, reverse=True))
        else:
            other.reverse = True
            return other.connect(self)

    def __rrshift__(self, other: Union[List["Node"], List["Edge"]]):
        """Called for [Nodes] and [Edges] >> Self because list don't have __rshift__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.forward = True
                o.connect(self)
            else:
                o.connect(self, Edge(self, forward=True))
        return self

    def __rlshift__(self, other: Union[List["Node"], List["Edge"]]):
        """Called for [Nodes] << Self because list of Nodes don't have __lshift__ operators."""
        for o in other:
            if isinstance(o, Edge):
                o.reverse = True
                o.connect(self)
            else:
                o.connect(self, Edge(self, reverse=True))
        return self

    @property
    def nodeid(self):
        return self._id

    # TODO: option for adding flow description to the connection edge
    def connect(self, node: "Node", edge: "Edge"):
        """Connect to other node.

        :param node: Other node instance.
        :param edge: Type of the edge.
        :return: Connected node.
        """
        if not isinstance(node, Node):
            ValueError(f"{node} is not a valid Node")
        if not isinstance(node, Edge):
            ValueError(f"{node} is not a valid Edge")
        # An edge must be added on the global resource_classes, not a cluster.
        self._diagram.connect(self, node, edge)
        return node

    @staticmethod
    def _rand_id(self, attr):
        return f"{self._provider}.{self._type}.{self.__class__.__name__}.{uuid.uuid4().hex}"

    def _load_icon(self):
        basedir = Path(os.path.abspath(os.path.dirname(__file__)))
        return os.path.join(basedir.parent, self._icon_dir, self._icon)


class Edge:
    """Edge represents an edge between two nodes."""

    _default_edge_attrs = {
        "fontcolor": "#2D3436",
        "fontname": "Sans-Serif",
        "fontsize": "13",
    }

    def __init__(
        self,
        node: "Node" = None,
        forward: bool = False,
        reverse: bool = False,
        label: str = "",
        color: str = "",
        style: str = "",
        **attrs: Dict,
    ):
        """Edge represents an edge between two nodes.

        :param node: Parent node.
        :param forward: Points forward.
        :param reverse: Points backward.
        :param label: Edge label.
        :param color: Edge color.
        :param style: Edge style.
        :param attrs: Other edge attributes
        """
        if node is not None:
            assert isinstance(node, Node)

        self.node = node
        self.forward = forward
        self.reverse = reverse

        self._attrs = {}

        # Set attributes.
        for k, v in self._default_edge_attrs.items():
            self._attrs[k] = v

        if label:
            self._attrs["xlabel"] = "  " + label + "  "
        if color:
            self._attrs["color"] = color
        if style:
            self._attrs["style"] = style
        self._attrs.update(attrs)

    def __sub__(self, other: Union["Node", "Edge", List["Node"]]):
        """Implement Self - Node or Edge and Self - [Nodes]"""
        return self.connect(other)

    def __rsub__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] - Self because list don't have __sub__ operators."""
        return self.append(other)

    def __rshift__(self, other: Union["Node", "Edge", List["Node"]]):
        """Implements Self >> Node or Edge and Self >> [Nodes]."""
        self.forward = True
        return self.connect(other)

    def __lshift__(self, other: Union["Node", "Edge", List["Node"]]):
        """Implements Self << Node or Edge and Self << [Nodes]."""
        self.reverse = True
        return self.connect(other)

    def __rrshift__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] >> Self because list of Edges don't have __rshift__ operators."""
        return self.append(other, forward=True)

    def __rlshift__(self, other: Union[List["Node"], List["Edge"]]) -> List["Edge"]:
        """Called for [Nodes] or [Edges] << Self because list of Edges don't have __lshift__ operators."""
        return self.append(other, reverse=True)

    def append(self, other: Union[List["Node"], List["Edge"]], forward=None, reverse=None) -> List["Edge"]:
        result = []
        for o in other:
            if isinstance(o, Edge):
                o.forward = forward if forward else o.forward
                o.reverse = forward if forward else o.reverse
                self._attrs = o.attrs.copy()
                result.append(o)
            else:
                result.append(
                    Edge(o, forward=forward, reverse=reverse, **self._attrs))
        return result

    def connect(self, other: Union["Node", "Edge", List["Node"]]):
        if isinstance(other, list):
            for node in other:
                self.node.connect(node, self)
            return other
        elif isinstance(other, Edge):
            self._attrs = other._attrs.copy()
            return self
        else:
            if self.node is not None:
                return self.node.connect(other, self)
            else:
                self.node = other
                return self

    @property
    def attrs(self) -> Dict:
        if self.forward and self.reverse:
            direction = "both"
        elif self.forward:
            direction = "forward"
        elif self.reverse:
            direction = "back"
        else:
            direction = "none"
        return {**self._attrs, "dir": direction}
