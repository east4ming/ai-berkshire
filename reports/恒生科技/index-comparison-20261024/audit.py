#!/usr/bin/env python3
"""Scoped source/formula audit. Does not certify estimates or vendor methodology."""
import contextlib
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT = HERE.parent / "恒生科技与纳斯达克估值对比-20261024.md"
sys.path.insert(0, str(ROOT / "tools"))
import report_audit
import model


def dump(name, content):
    (HERE / name).write_text(json.dumps(content, ensure_ascii=False, indent=2, default=str) + "\n")


def main():
    text = REPORT.read_text()
    inputs = json.loads((HERE / "inputs.json").read_text(), parse_float=D)
    observations = json.loads((HERE / "valuation-extract.json").read_text(), parse_float=D)
    computed = model.build()
    # Compare model input observations against the retained source extract.
    checks = 0
    for name, spec in inputs["valuation_comparison"].items():
        ticker = "HSTECH" if name.startswith("HSTECH") else "NDX"
        field = "pb" if "_PB" in name else "pe"
        for end in ("old", "new"):
            date = spec[end + "_date"].split()[0]
            observed = next(x[field] for x in observations["records"][ticker] if x["date"] == date)
            assert D(spec[end]) == D(str(observed)), (name, end)
            checks += 1
    # Separate numerical implementation of dividend/terminal-wealth arithmetic.
    for name, spec in inputs["scenarios"].items():
        p, g, t, pay = [float(spec[k]) for k in ("start_pe", "growth", "end_pe", "payout")]
        wealth = t * (1 + g) ** 5 + pay * math.fsum((1 + g) ** i for i in range(1, 6))
        independent = ((wealth / p) ** 0.2 - 1) * 100
        assert abs(independent - float(computed["scenarios"][name]["wealth_cagr_pct"])) < 1e-10
        displayed = f"{computed['scenarios'][name]['wealth_cagr_pct']:+.2f}%"
        assert displayed in text, (name, displayed)
        checks += 1

    # Retained source observations, not numbers copied from the report by the auditor.
    fred = "https://fred.stlouisfed.org/data/NASDAQ100"
    msft = "https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q4"
    specs = {
        "纳斯达克 100 NDX · 2022-10-31 收盘": ("source", D("11405.57"), fred + " observation 2022-10-31", D("11405.57"), "KFH Capital October 2022 p3 / Refinitiv; sources.md"),
        "纳斯达克 100 NDX · 2026-10-23 收盘": ("source", D("28957.53"), fred + " observation 2026-10-23", None, "Single originating market-data chain; not dual-source"),
        "恒生科技 PE-TTM · 倍数变化": ("formula", computed["valuation_changes_pct"]["HSTECH_PE"], "Decimal(20.63/31.94-1)*100; retained source extract", None, "Vendor-method limitation remains"),
        "恒生科技 PB · 倍数变化": ("formula", computed["valuation_changes_pct"]["HSTECH_PB"], "Decimal(2.092/1.743-1)*100; retained source extract", None, "Vendor-method limitation remains"),
        "恒生科技 PB · 最新可得观察": ("source", D("2.092"), "valuation-extract.json HSTECH 2026-10-23", D("2.09"), "baifenwei.com/index/hstech; rounded, possibly same upstream, NOT independent"),
        "纳指 100 PE-TTM · 倍数变化": ("formula", computed["valuation_changes_pct"]["NDX_PE"], "Decimal(28.74/25.34-1)*100; date labels preserved", None, "Vendor-method limitation remains"),
        "微软，FY2026Q4 · 盈利或现金指标": ("source", D("55.4") * 10, msft + " CFO USD55.4bn = 554亿美元", D("55.4") * 10, "StockAnalysis Q4 2026 transcript, same originating disclosure; NOT independent"),
        "美国十年恒定期限国债收益率 · 变化方向": ("formula", (D("4.96") - D("4.10")) * 100, "FRED DGS10 2026-10-22 minus 2022-10-31, percentage points *100 = bp", None, "Same official time series"),
        "恒科：压力 · 第五年 PE": ("assumption", D(inputs["scenarios"]["HSTECH_bear"]["end_pe"]), "inputs.json declared assumption", None, "Not a historical fact"),
        "纳指：中间假设 · 每单位盈利年增速": ("assumption", D(inputs["scenarios"]["NDX_base"]["growth"]) * 100, "inputs.json declared assumption", None, "Not consensus or a forecast certification"),
        "纳指中间假设 · 起始 PE": ("assumption", D(inputs["scenarios"]["NDX_base"]["start_pe"]), "inputs.json rounded starting multiple assumption", None, "Not independently reconstructed economic PE"),
    }
    all_points = report_audit.extract_data_points(text)
    sample = report_audit.sample_points(all_points, ratio=.15, seed=42)
    facts, assumptions, excluded, dispositions = [], [], [], []
    for item in sample:
        if item["label"] == "date" and item["line_number"] == 3:
            assert text.splitlines()[2] == "date: 2026-10-24"
            excluded.append({**item, "reason": "Front-matter date misparsed as financial value 2026; metadata verified separately"})
            continue
        if item["label"] not in specs:
            raise AssertionError("Unclassified sampled item: " + item["label"])
        kind, value, source, value2, source2 = specs[item["label"]]
        entry = {**item, "kind": kind, "fetched_value": str(value), "fetched_source": source,
                 "fetched_value2": str(value2) if value2 is not None else None, "fetched_source2": source2}
        (assumptions if kind == "assumption" else facts).append(entry)
        dispositions.append({"id": item["id"], "label": item["label"], "kind": kind, "source_limit": source2})
    assert len(facts) + len(assumptions) + len(excluded) == len(sample)
    dump("audit-sample.json", sample)
    dump("audit-facts-formulas.json", facts)
    dump("audit-assumptions.json", assumptions)
    dump("audit-exclusions.json", excluded)
    dump("audit-dispositions.json", dispositions)
    outcomes = {}
    for group, rows in (("facts-formulas", facts), ("assumptions", assumptions)):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            outcome = report_audit.render_verdict(rows, report_name=REPORT.name + " / " + group)
        verdict_text = re.sub(r"\x1b\[[0-9;]*m", "", stream.getvalue())
        (HERE / ("audit-" + group + "-verdict.txt")).write_text("\n".join(line.rstrip() for line in verdict_text.splitlines()) + "\n")
        assert outcome["fail_count"] == outcome["warn_count"] == 0
        assert outcome["total"] == len(rows) > 0
        outcomes[group] = outcome

    # Required shared-tool checks; use 1% rather than the toolkit's default 2%.
    commands = [
        ["cross-validate", "--field", "HSTECH close 2026-10-23", "--values", '{"HSI":3871.66,"HKEJ":3871.66}', "--unit", "point", "--tolerance", "1"],
        ["cross-validate", "--field", "HSTECH close 2022-10-31", "--values", '{"SecuritiesTimes":2852.57,"Zhitong":2852.57}', "--unit", "point", "--tolerance", "1"],
        ["cross-validate", "--field", "Tencent Q2 FCF", "--values", '{"Issuer":-138,"Telecompaper":-138}', "--unit", "CNY100m", "--tolerance", "1"],
        ["cross-validate", "--field", "Alibaba June quarter FCF", "--values", '{"Issuer":-446.7,"MoneyDJ":-446.7}', "--unit", "CNY100m", "--tolerance", "1"],
        ["cross-validate", "--field", "Microsoft FY26Q4 FCF", "--values", '{"Issuer":196,"Reuters":196}', "--unit", "USD100m", "--tolerance", "1"],
        ["calc", "--expr", "(20.63/31.94-1)*100"],
        ["calc", "--expr", "(2.092/1.743-1)*100"],
        ["calc", "--expr", "(28.74/25.34-1)*100"],
        ["calc", "--expr", "(9.037/6.490-1)*100"],
        ["calc", "--expr", "(28957.53/11405.57-1)*100"],
        ["three-scenario", "--price", "21", "--eps", "1", "--shares", "1", "--growth", ".15", ".08", "0", "--pe", "24", "20", "16", "--years", "5", "--currency", "normalized units (not market capitalization)"],
        ["three-scenario", "--price", "29", "--eps", "1", "--shares", "1", "--growth", ".18", ".12", ".04", "--pe", "30", "25", "20", "--years", "5", "--currency", "normalized units (not market capitalization)"],
    ]
    logs = []
    for command in commands:
        proc = subprocess.run([sys.executable, str(ROOT / "tools/financial_rigor.py"), *command], capture_output=True, text=True, check=True)
        logs.append("COMMAND: financial_rigor.py " + " ".join(command) + "\n" + proc.stdout)
    (HERE / "financial-rigor.txt").write_text("\n".join(logs))
    result = {"status": "PASS_WITH_EXPLICIT_SCOPE", "data_quality": "PARTIAL_DUAL_SOURCE",
        "report_sha256": hashlib.sha256(REPORT.read_bytes()).hexdigest(),
        "extracted_points": len(all_points), "random_sample": len(sample),
        "source_formula_checked": len(facts), "assumptions_checked": len(assumptions),
        "excluded_metadata": len(excluded), "additional_consistency_checks": checks,
        "outcomes": outcomes,
        "limits": ["No independent reconstruction of vendor PE/PB methodology", "No US close mapping for NDX valuation labels", "Scenario assumptions not validated forecasts", "Single-source or shared-upstream facts explicitly labeled", "financial_rigor calc uses float eval; authoritative arithmetic uses Decimal model"]}
    dump("audit-results.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "outcomes"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
