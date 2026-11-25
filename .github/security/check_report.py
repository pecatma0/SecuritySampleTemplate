"""Turn Semgrep JSON and CodeQL SARIF severities into CI exit statuses."""

import argparse
import json
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    rule: str
    blocking: bool


SEMGREP_LEVELS = {
    "INFO": False,
    "LOW": False,
    "WARNING": True,
    "MEDIUM": True,
    "ERROR": True,
    "HIGH": True,
    "CRITICAL": True,
}


def semgrep_findings(report):
    if report["errors"] or not any(
        path.endswith(".py") for path in report["paths"]["scanned"]
    ):
        raise ValueError("Semgrep reported analysis errors or did not scan Python files")

    findings = []
    for result in report["results"]:
        severity = result["extra"]["severity"]
        if severity not in SEMGREP_LEVELS:
            raise ValueError("Unknown Semgrep severity")
        findings.append(Finding(result["check_id"], SEMGREP_LEVELS[severity]))
    return findings


def codeql_findings(report):
    if not report["runs"]:
        raise ValueError("CodeQL report did not contain an analysis")

    findings = []
    for run in report["runs"]:
        tool = run["tool"]
        driver = tool["driver"]
        if driver["name"] != "CodeQL" or not isinstance(run.get("results"), list):
            raise ValueError("Expected a CodeQL run with a results array")
        rules = {
            rule["id"]: rule.get("properties", {})
            for component in [driver, *tool.get("extensions", [])]
            for rule in component.get("rules", [])
        }
        for result in run["results"]:
            rule_id = result["ruleId"]
            if rule_id not in rules:
                raise ValueError("CodeQL result is missing its rule metadata")
            properties = rules[rule_id]
            score = properties.get("security-severity")
            if score is None:
                if "security" in properties.get("tags", []):
                    findings.append(Finding(rule_id, True))
                continue
            score = float(score)
            if not 0.0 <= score <= 10.0:
                raise ValueError("Invalid CodeQL security score")
            findings.append(Finding(rule_id, score >= 4.0))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", choices=["semgrep", "codeql"])
    parser.add_argument("reports", type=Path, nargs="+")
    args = parser.parse_args()
    read_findings = {"semgrep": semgrep_findings, "codeql": codeql_findings}[args.tool]
    try:
        findings = [
            finding
            for report_path in args.reports
            for finding in read_findings(json.loads(report_path.read_text(encoding="utf-8")))
        ]
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        print(f"::error::{args.tool} report is missing, invalid, or incomplete ({type(error).__name__})")
        return 1

    for rule, blocking in findings:
        annotation = "error" if blocking else "warning"
        safe_rule = rule.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
        print(f"::{annotation}::{args.tool}: {safe_rule}")
    blockers = sum(finding.blocking for finding in findings)
    print(f"{args.tool}: {blockers} blocking finding(s), {len(findings) - blockers} warning(s)")
    return int(blockers > 0)


if __name__ == "__main__":
    raise SystemExit(main())
