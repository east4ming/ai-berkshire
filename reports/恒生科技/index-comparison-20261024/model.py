#!/usr/bin/env python3
"""Reproduce the report's arithmetic, not a forecast or a constituent backtest."""
import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 50
D = Decimal
HERE = Path(__file__).resolve().parent


def change(old, new):
    return (D(new) / D(old) - 1) * 100


def scenario(start_pe, growth, end_pe, payout, years=5):
    """E0=1; cash dividends at year-end, held as cash; no reinvestment.

    Growth is per-index-unit earnings growth after dilution/buybacks. Thus
    buybacks are NOT added again as a separate yield. No fees, tax or FX.
    """
    start, g, end, pay = map(D, (start_pe, growth, end_pe, payout))
    profits = [(1 + g) ** t for t in range(1, years + 1)]
    terminal_price = profits[-1] * end
    cash_dividends = sum(profits, D(0)) * pay
    wealth = terminal_price + cash_dividends
    return {
        "start_pe": start, "growth": g, "exit_pe": end, "payout": pay,
        "terminal_price_ratio": terminal_price / start,
        "cash_dividends_on_initial_price_pct": cash_dividends / start * 100,
        "total_return_pct": (wealth / start - 1) * 100,
        "wealth_cagr_pct": ((wealth / start) ** (D(1) / years) - 1) * 100,
    }


def build():
    source = json.loads((HERE / "inputs.json").read_text())
    result = {"price_changes_pct": {}, "valuation_changes_pct": {},
              "scenarios": {}, "thresholds": {}, "mechanical_examples": {}}
    for name, pair in source["price_comparison"].items():
        result["price_changes_pct"][name] = change(pair["old"], pair["new"])
    for name, pair in source["valuation_comparison"].items():
        result["valuation_changes_pct"][name] = change(pair["old"], pair["new"])
    for name, item in source["scenarios"].items():
        result["scenarios"][name] = scenario(**item)
    for name, item in source["thresholds"].items():
        # A price sensitivity holding the valuation denominator constant.
        price = D(item["current_price"]) * D(item["target_multiple"]) / D(item["current_multiple"])
        result["thresholds"][name] = {"price": price,
            "change_pct": change(item["current_price"], price)}
    # Pure algebraic illustrations; none of these inputs is an index estimate.
    result["mechanical_examples"] = {
        "earnings_minus_20_pe_rise_pct": change("20", D(20) / D("0.8")),
        "eps_minus_20_and_pe_25_to_20_price_pct": (D("0.8") * D(20) / D(25) - 1) * 100,
        "earnings_yield_20_pct": D(100) / D(20),
        "earnings_yield_30_pct": D(100) / D(30),
        "cash_yield_20pe_50conversion_pct": D(100) / D(20) * D("0.5"),
        "cash_yield_30pe_90conversion_pct": D(100) / D(30) * D("0.9"),
        "required_growth_10pct_25to20_price_only_pct":
            ((D("1.1") ** 5 * D(25) / D(20)) ** (D(1) / 5) - 1) * 100,
        "ust_change_bp": (D("4.96") - D("4.10")) * 100,
    }
    return result


def encode(obj):
    if isinstance(obj, D):
        return str(obj)
    raise TypeError(type(obj))


if __name__ == "__main__":
    results = build()
    (HERE / "model-results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=encode) + "\n")
    for group, values in results.items():
        print(group)
        for key, value in values.items():
            if isinstance(value, D):
                print(f"  {key}: {value:.4f}")
            elif "wealth_cagr_pct" in value:
                print(f"  {key}: CAGR {value['wealth_cagr_pct']:.4f}%, total {value['total_return_pct']:.4f}%")
            else:
                print(f"  {key}: {value}")
