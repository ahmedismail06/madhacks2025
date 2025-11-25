# ===========================================
# core/graph.py - Graph data structures
# ===========================================
# Defines Node, Edge, and Graph classes for representing
# the fiber optic network topology.

class Node:
    """
    Represents a node in the fiber optic network graph.
    
    Node types:
    - city: Major city endpoint where users connect
    - network_node: Intermediate routing point in the network
    - regen_spot: Signal regeneration station (resets signal quality to 100%)
    - city_connection: Connection point between city and network
    - routing: General routing node
    """
    def __init__(self, id: int, name: str, node_type: str, x: float, y: float, edge_ids: list[int]):
        self.id = id                    # Unique node identifier
        self.name = name                # Human-readable name (empty for non-city nodes)
        self.type = node_type           # Node type (see above)
        self.x = x                      # Latitude coordinate
        self.y = y                      # Longitude coordinate
        self.edge_ids = edge_ids        # List of edge IDs connected to this node


class Edge:
    """
    Represents a fiber optic cable connection between two nodes.
    
    Each edge has physical properties like distance, traffic load, and signal degradation rate.
    The edge cost is calculated based on weighted factors (latency, traffic, risk).
    """
    def __init__(self, id: int, from_node: int, to_node: int, distance: float, traffic_load: float, 
                 base_ms: float, risk: float, degrade_rate: float, start_x: float = 0, 
                 start_y: float = 0, end_x: float = 0, end_y: float = 0):
        self.id = id                    # Unique edge identifier
        self.from_node = from_node      # Source node ID
        self.to_node = to_node          # Destination node ID
        self.distance = distance        # Physical distance in kilometers
        self.traffic_load = traffic_load  # Current traffic utilization (0.0 to 1.0)
        self.base_ms = base_ms          # Base latency per km in milliseconds
        self.latency_ms = distance * base_ms  # Total calculated latency
        self.risk = risk                # Risk factor (e.g., environmental, political)
        self.degrade_rate = degrade_rate  # Signal attenuation rate in dB/km
        # Geographic coordinates for visualization
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y

    def get_other_node(self, node_id: int) -> int:
        """
        Given one endpoint of this edge, returns the other endpoint.
        Used for bidirectional graph traversal.
        
        Args:
            node_id: ID of one endpoint node
            
        Returns:
            ID of the other endpoint node
        """
        return self.to_node if node_id == self.from_node else self.from_node


class Graph:
    """
    Container for the complete fiber optic network topology.
    Stores all nodes and edges, providing efficient lookup by ID.
    """
    def __init__(self):
        self.nodes: dict[int, Node] = {}      # Maps node_id -> Node object
        self.edges: dict[int, Edge] = {}      # Maps edge_id -> Edge object

    def add_node(self, node: Node):
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        """Add an edge to the graph."""
        self.edges[edge.id] = edge
