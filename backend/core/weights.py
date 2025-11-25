# ===========================================
# core/weights.py - Edge cost calculation
# ===========================================
# Defines the weighted cost function for pathfinding algorithms.
# Users can prioritize different factors (latency, traffic, risk)
# to find optimal routes based on their needs.

from core.graph import Edge


def make_weight_function(latency_w: float, traffic_w: float, risk_w: float):
    """
    Creates a weighted cost function for graph edges based on user priorities.
    
    The cost function combines three factors:
    - Latency: Physical signal propagation delay (in milliseconds)
    - Traffic: Current network congestion level (0.0 to 1.0)
    - Risk: Environmental/political risk factor (0.0 to 1.0)
    
    Args:
        latency_w: Weight for latency factor (higher = prioritize low latency)
        traffic_w: Weight for traffic factor (higher = avoid congested routes)
        risk_w: Weight for risk factor (higher = avoid risky routes)
        
    Returns:
        A function that takes an Edge and returns its weighted cost
        
    Example:
        # Prioritize low latency (weight=1.0), moderate traffic (0.5), ignore risk (0.0)
        weight_func = make_weight_function(1.0, 0.5, 0.0)
        cost = weight_func(some_edge)  # Returns weighted cost for that edge
    """
    def func(edge: Edge):
        # Calculate linear combination of weighted factors
        return (
            latency_w * edge.latency_ms +      # Latency contribution
            traffic_w * edge.traffic_load +    # Traffic contribution
            risk_w * edge.risk                  # Risk contribution
        )
    return func
