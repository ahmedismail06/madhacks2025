# ===========================================
# core/weights.py
# ===========================================

from core.graph import Edge


# Weighted edge cost function
def make_weight_function(latency_w: float, cost_w: float, risk_w: float):
    def func(edge: Edge):
        # Use distance directly as latency metric
        return (
            latency_w * edge.distance +
            cost_w * edge.cost +
            risk_w * edge.risk
        )
    return func
