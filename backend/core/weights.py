# ===========================================
# core/weights.py
# ===========================================

from core.graph import Edge


# Weighted edge cost function
def make_weight_function(latency_w: float, traffic_w: float, risk_w: float):
    def func(edge: Edge):
        # Use calculated latency_ms, traffic_load, and risk
        return (
            latency_w * edge.latency_ms +
            traffic_w * edge.traffic_load +
            risk_w * edge.risk
        )
    return func
