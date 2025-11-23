# ===========================================
# core/graph.py
# ===========================================

class Node:
    def __init__(self, id: int, name: str, node_type: str, lat: float, lng: float, edge_ids: list[int]):
        self.id = id                    # unique node ID (integer)
        self.name = name                # human-readable name
        self.type = node_type           # "city" | "routing" | "regen"
        self.lat = lat
        self.lng = lng
        self.edge_ids = edge_ids        # list of edge IDs connected to this node


class Edge:
    def __init__(self, id: int, from_node: int, to_node: int, distance: float, cost: float, risk: float, degrade_rate: float):
        self.id = id                    # unique edge ID
        self.from_node = from_node      # source node ID
        self.to_node = to_node          # destination node ID
        self.distance = distance        # distance in km
        self.cost = cost
        self.risk = risk
        self.degrade_rate = degrade_rate

    def get_other_node(self, node_id: int) -> int:
        """Get the other end of this edge given one node ID"""
        return self.to_node if node_id == self.from_node else self.from_node


class Graph:
    def __init__(self):
        self.nodes: dict[int, Node] = {}      # node_id -> Node
        self.edges: dict[int, Edge] = {}      # edge_id -> Edge

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        self.edges[edge.id] = edge
