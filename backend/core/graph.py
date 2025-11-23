# ===========================================
# core/graph.py
# ===========================================

class Node:
    def __init__(self, id: int, name: str, node_type: str, x: float, y: float, edge_ids: list[int]):
        self.id = id                    # unique node ID (integer)
        self.name = name                # human-readable name
        self.type = node_type           # "city" | "routing" | "regen"
        self.x = x
        self.y = y
        self.edge_ids = edge_ids        # list of edge IDs connected to this node


class Edge:
    def __init__(self, id: int, from_node: int, to_node: int, distance: float, traffic_load: float, base_ms: float, risk: float, degrade_rate: float, start_x: float = 0, start_y: float = 0, end_x: float = 0, end_y: float = 0):
        self.id = id                    # unique edge ID
        self.from_node = from_node      # source node ID
        self.to_node = to_node          # destination node ID
        self.distance = distance        # distance in km
        self.traffic_load = traffic_load  # traffic load (0.0 to 1.0)
        self.base_ms = base_ms          # base latency per unit distance in ms
        self.latency_ms = distance * base_ms  # calculated latency in milliseconds
        self.risk = risk
        self.degrade_rate = degrade_rate
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y

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
