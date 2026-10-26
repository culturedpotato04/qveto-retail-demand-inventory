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


def order_policy(mean_daily, std_daily, lead_days, z_score, stock,
                 on_order=0, backorders=0, coverage_days=7, pack_size=1,
                 minimum_order=0):
    """Illustrative continuous-review (s,S) policy; never a measured saving.

    Constant lead time, independent stationary daily demand, normal approximation.
    coverage_days adds replenishment cycle coverage, not a review interval.
    """
    result = reorder_scenario(mean_daily, std_daily, lead_days, z_score,
                              stock, on_order, backorders)
    if not math.isfinite(coverage_days) or coverage_days <= 0:
        raise ValueError('coverage_days must be finite and positive')
    for name, value, lower in [('pack_size', pack_size, 1),
                                ('minimum_order', minimum_order, 0)]:
        if isinstance(value, bool) or not isinstance(value, int) or value < lower:
            raise ValueError(f'{name} must be an integer >= {lower}')
    horizon = lead_days + coverage_days
    target = mean_daily * horizon + z_score * std_daily * math.sqrt(horizon)
    gap = max(0., target - result['inventory_position'])
    quantity = 0
    if result['reorder_triggered'] and gap > 0:
        quantity = math.ceil(max(gap, minimum_order) / pack_size) * pack_size
    return {**result, 'order_up_to_units': target,
            'suggested_order_units': quantity,
            'post_order_inventory_position': result['inventory_position'] + quantity}
