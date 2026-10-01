"""Régressions de comptage des rebuts, indépendantes du nombre de passages."""

from pathlib import Path
from types import SimpleNamespace
import unittest

import pandas as pd

from src.data_loader import load_datasets
from src.quality_analysis import analyze_quality


def fixture(events):
    production = []
    quality = []
    for event_id, serial, station, passage, result, disposition in events:
        production.append({
            "production_event_id": event_id, "serial_number": serial,
            "station_id": station, "pass_number": passage,
            "product_variant": "A", "production_date": "2027-01-11", "shift_id": "S1",
        })
        quality.append({
            "production_event_id": event_id, "quality_result": result,
            "disposition": disposition, "first_pass_flag": passage == 1,
            "rework_required_flag": disposition == "REWORK", "scrap_flag": disposition == "SCRAP",
            "defect_code": "QL-TEST" if result == "FAIL" else None,
            "defect_category": "Test" if result == "FAIL" else None,
            "origin_station_id": station, "rework_duration_s": 10 if disposition == "REWORK" else 0,
            "notes": "",
        })
    return SimpleNamespace(production=pd.DataFrame(production), quality=pd.DataFrame(quality))


class QualityCountingTests(unittest.TestCase):
    def test_scrap_after_rework_does_not_disappear(self):
        bundle = fixture([
            ("E1", "P1", "ST50", 1, "FAIL", "REWORK"),
            ("E2", "P1", "ST50", 2, "FAIL", "SCRAP"),
            ("E3", "P2", "ST50", 1, "PASS", "ACCEPT"),
        ])
        result = analyze_quality(bundle, ["ST50"])
        station = result["by_station"].iloc[0]
        self.assertEqual(station["total_first_pass"], 2)
        self.assertEqual(station["good_first_pass"], 1)
        self.assertEqual(station["scrap"], 1)
        self.assertEqual(station["fpy"], 0.5)
        self.assertEqual(station["scrap_rate"], 0.5)
        self.assertEqual(result["defect_pareto"]["count"].sum(), 1)
        self.assertEqual(result["defect_pareto"]["scrap_count"].sum(), 1)
        self.assertEqual(result["summary"]["scrap_units"], 1)

    def test_direct_first_pass_scrap_is_counted(self):
        result = analyze_quality(fixture([
            ("E1", "P1", "ST50", 1, "FAIL", "SCRAP"),
        ]), ["ST50"])
        self.assertEqual(result["by_station"].iloc[0]["scrap"], 1)
        self.assertEqual(result["summary"]["scrap_units"], 1)
        self.assertEqual(result["summary"]["overall_fpy"], 0)

    def test_recovered_rework_is_not_scrap(self):
        result = analyze_quality(fixture([
            ("E1", "P1", "ST50", 1, "FAIL", "REWORK"),
            ("E2", "P1", "ST50", 2, "PASS", "ACCEPT"),
        ]), ["ST50"])
        self.assertEqual(result["by_station"].iloc[0]["scrap"], 0)
        self.assertEqual(result["defect_pareto"]["scrap_count"].sum(), 0)
        self.assertEqual(result["summary"]["overall_fpy"], 0)

    def test_scrap_is_attributed_to_its_terminal_station(self):
        result = analyze_quality(fixture([
            ("E1", "P1", "ST40", 1, "FAIL", "REWORK"),
            ("E2", "P1", "ST40", 2, "PASS", "ACCEPT"),
            ("E3", "P1", "ST50", 1, "FAIL", "REWORK"),
            ("E4", "P1", "ST50", 2, "FAIL", "SCRAP"),
        ]), ["ST40", "ST50"])
        counts = result["by_station"].set_index("station_id")["scrap"].to_dict()
        self.assertEqual(counts, {"ST40": 0, "ST50": 1})
        self.assertEqual(result["defect_pareto"]["scrap_count"].sum(), 1)

    def test_supplied_baseline_has_six_scrapped_products(self):
        root = Path(__file__).resolve().parents[1]
        bundle = load_datasets(root / "data/processed")
        result = analyze_quality(bundle, [f"ST{n}" for n in [10, 20, 30, 40, 50, 60, 70]])
        counts = result["by_station"].set_index("station_id")["scrap"].to_dict()
        self.assertEqual(counts, {"ST10": 0, "ST20": 0, "ST30": 0, "ST40": 1, "ST50": 3, "ST60": 2, "ST70": 0})
        self.assertEqual(result["summary"]["scrap_units"], 6)
        self.assertEqual(result["defect_pareto"]["scrap_count"].sum(), 6)
        self.assertEqual(result["summary"]["total_first_pass"], 25493)
        self.assertEqual(result["summary"]["good_first_pass"], 25361)
        self.assertEqual(result["summary"]["first_pass_fail"], 132)
        self.assertAlmostEqual(result["summary"]["overall_fpy"], 25361 / 25493)


if __name__ == "__main__":
    unittest.main()
