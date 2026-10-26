"""Assumption-based retail scenario math, separate from rental benchmark outputs."""
import math


def reorder_scenario(mean_daily, std_daily, lead_days, z_score, stock, on_order=0, backorders=0):
    values = (mean_daily, std_daily, lead_days, z_score, stock, on_order, backorders)
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('All scenario inputs must be finite and nonnegative')
    safety_stock = z_score * std_daily * math.sqrt(lead_days)
    reorder_point = mean_daily * lead_days + safety_stock
    inventory_position = stock + on_order - backorders
    return {'scenario_only': True, 'safety_stock': safety_stock,
            'reorder_point': reorder_point, 'inventory_position': inventory_position,
            'gap_to_reorder_point': max(0., reorder_point - inventory_position),
            'reorder_triggered': inventory_position <= reorder_point}
