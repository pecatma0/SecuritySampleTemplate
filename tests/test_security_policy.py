import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github/security"))
from check_report import Finding, codeql_findings, semgrep_findings


class SemgrepPolicyTests(unittest.TestCase):
    def test_low_and_medium_include_legacy_severities(self):
        levels = ["LOW", "INFO", "MEDIUM", "WARNING", "HIGH", "ERROR", "CRITICAL"]
        report = {
            "errors": [],
            "paths": {"scanned": ["sample/urls.py"]},
            "results": [
                {"check_id": level, "extra": {"severity": level}} for level in levels
            ],
        }
        self.assertEqual(
            semgrep_findings(report),
            [Finding(level, index >= 2) for index, level in enumerate(levels)],
        )

    def test_empty_scan_and_scan_errors_are_rejected(self):
        for report in [
            {"errors": [], "paths": {"scanned": []}, "results": []},
            {"errors": [{"type": "Timeout"}], "paths": {"scanned": ["a.py"]}, "results": []},
        ]:
            with self.subTest(report=report), self.assertRaises(ValueError):
                semgrep_findings(report)

    def test_unknown_severity_is_rejected(self):
        report = {
            "errors": [],
            "paths": {"scanned": ["a.py"]},
            "results": [{"check_id": "rule", "extra": {"severity": "unexpected"}}],
        }
        with self.assertRaises(ValueError):
            semgrep_findings(report)


class CodeQLPolicyTests(unittest.TestCase):
    def test_uses_security_score_and_supports_query_pack_rules(self):
        report = {"runs": [{
            "tool": {
                "driver": {"name": "CodeQL", "rules": [
                    {"id": "low", "properties": {"security-severity": "3.9"}},
                    {"id": "quality", "properties": {"tags": ["maintainability"]}},
                ]},
                "extensions": [{"rules": [
                    {"id": "medium", "properties": {"security-severity": "4.0"}},
                ]}],
            },
            "results": [
                {"ruleId": "low", "level": "error"},
                {"ruleId": "medium", "level": "note"},
                {"ruleId": "quality", "level": "error"},
            ],
        }]}
        self.assertEqual(codeql_findings(report), [Finding("low", False), Finding("medium", True)])

    def test_security_result_without_score_blocks(self):
        report = {"runs": [{
            "tool": {"driver": {"name": "CodeQL", "rules": [
                {"id": "security", "properties": {"tags": ["security"]}},
            ]}},
            "results": [{"ruleId": "security"}],
        }]}
        self.assertEqual(codeql_findings(report), [Finding("security", True)])

    def test_empty_valid_analysis_passes(self):
        report = {"runs": [{
            "tool": {"driver": {"name": "CodeQL"}},
            "results": [],
        }]}
        self.assertEqual(codeql_findings(report), [])

    def test_invalid_analysis_fails_closed(self):
        reports = [
            {"runs": []},
            {"runs": [{"tool": {"driver": {"name": "CodeQL"}}}]},
            {"runs": [{
                "tool": {"driver": {"name": "CodeQL"}},
                "results": [{"ruleId": "missing"}],
            }]},
            {"runs": [{
                "tool": {"driver": {"name": "CodeQL", "rules": [
                    {"id": "score", "properties": {"security-severity": "NaN"}},
                ]}},
                "results": [{"ruleId": "score"}],
            }]},
        ]
        for report in reports:
            with self.subTest(report=report), self.assertRaises(ValueError):
                codeql_findings(report)
