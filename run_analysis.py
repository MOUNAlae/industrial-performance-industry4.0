#!/usr/bin/env python3
"""Point d'entrée unique du pipeline analytique EMA-120."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.data_loader import load_datasets
from src.data_validation import raise_for_critical, validate_datasets
from src.downtime_analysis import analyze_downtime
from src.kpi_calculator import calculate_daily_output, calculate_overall_kpis, calculate_station_kpis
from src.quality_analysis import analyze_quality
from src.visualization import create_visualizations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exécute toute l'analyse EMA-120 avec une seule commande.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_DIR / "data" / "processed", help="Répertoire contenant les CSV validés")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "outputs", help="Répertoire des résultats")
    parser.add_argument("--config", type=Path, default=PROJECT_DIR / "config.json", help="Configuration de la ligne")
    parser.add_argument("--no-charts", action="store_true", help="Désactive uniquement la génération des PNG")
    return parser.parse_args()


def json_ready(value):
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        return value.item()
    if pd.isna(value):
        return None
    return value


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output_dir = args.output_dir.resolve()
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    print("[1/6] Chargement des données validées")
    bundle = load_datasets(args.input_dir)

    print("[2/6] Validation et réconciliations")
    validation = validate_datasets(bundle)
    write_json(output_dir / "validation_report.json", validation)
    raise_for_critical(validation)

    print("[3/6] Calcul des KPI")
    station_kpis = calculate_station_kpis(bundle, config)
    daily_output = calculate_daily_output(bundle, config)
    overall_kpis = calculate_overall_kpis(bundle, station_kpis, daily_output, config)
    station_kpis.to_csv(tables_dir / "station_kpis.csv", index=False)
    daily_output.to_csv(tables_dir / "daily_output.csv", index=False, date_format="%Y-%m-%d")

    print("[4/6] Analyse des arrêts")
    downtime = analyze_downtime(bundle, config["primary_station"])
    for name in ["by_station", "by_category", "by_cause", "primary_by_category", "primary_by_cause"]:
        downtime[name].to_csv(tables_dir / f"downtime_{name}.csv", index=False)

    print("[5/6] Analyse qualité")
    quality = analyze_quality(bundle, config["station_order"])
    for name in ["by_station", "by_variant", "defect_pareto"]:
        quality[name].to_csv(tables_dir / f"quality_{name}.csv", index=False)

    figures = []
    if not args.no_charts:
        print("[6/6] Création des visualisations")
        figures = create_visualizations(station_kpis, downtime, quality, daily_output, figures_dir, config["primary_station"])
    else:
        print("[6/6] Visualisations désactivées")

    payload = {
        "project": config["project"],
        "overall_kpis": overall_kpis,
        "downtime_summary": downtime["summary"],
        "quality_summary": quality["summary"],
        "source_hashes": bundle.file_hashes,
    }
    write_json(output_dir / "kpi_summary.json", payload)
    manifest = {
        "status": "PASS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": "python run_analysis.py",
        "input_dir": str(bundle.input_dir),
        "output_dir": str(output_dir),
        "tables": sorted(str(path.relative_to(output_dir)) for path in tables_dir.glob("*.csv")),
        "figures": sorted(str(path.relative_to(output_dir)) for path in figures),
        "validation": {"status": validation["status"], "checks_passed": validation["checks_passed"], "checks_total": validation["checks_total"]},
    }
    write_json(output_dir / "run_manifest.json", manifest)

    print("Analyse terminée: PASS")
    print(f"Goulot: {overall_kpis['bottleneck_station']} | charge: {overall_kpis['bottleneck_effective_load_s_per_unit']:.2f} s/u")
    print(f"Sortie observée: {overall_kpis['observed_output_units_per_day']:.1f} u/j | demande: {overall_kpis['daily_customer_demand_units']:.0f} u/j")
    print(f"Résultats: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

