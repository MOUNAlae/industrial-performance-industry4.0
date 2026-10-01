"""Contrôles bloquants et réconciliations des données EMA-120."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import pandas as pd

from .data_loader import DatasetBundle


REQUIRED_COLUMNS = {
    "production": {"production_event_id", "serial_number", "production_date", "shift_id", "station_id", "pass_number", "first_pass_flag", "process_result", "standard_cycle_time_s", "elapsed_time_s", "downtime_overlap_s", "net_cycle_time_s"},
    "downtime": {"downtime_id", "production_date", "shift_id", "station_id", "downtime_category", "downtime_cause_code", "planned_flag", "duration_s", "oee_loss_flag"},
    "quality": {"quality_event_id", "production_event_id", "serial_number", "detection_station_id", "quality_result", "disposition", "rework_required_flag", "scrap_flag", "first_pass_flag", "defect_code"},
    "changeovers": {"changeover_id", "production_date", "shift_id", "station_id", "from_variant", "to_variant", "actual_duration_s", "first_article_result"},
}

ID_COLUMNS = {
    "production": "production_event_id",
    "downtime": "downtime_id",
    "quality": "quality_event_id",
    "changeovers": "changeover_id",
}


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    critical: bool
    detail: str


def _check(name: str, condition: bool, detail: str, critical: bool = True) -> Check:
    return Check(name=name, passed=bool(condition), critical=critical, detail=detail)


def _missing_columns(frame: pd.DataFrame, required: Iterable[str]) -> set[str]:
    return set(required) - set(frame.columns)


def validate_datasets(bundle: DatasetBundle) -> dict:
    checks: list[Check] = []
    warnings: list[str] = []
    frames = {
        "production": bundle.production,
        "downtime": bundle.downtime,
        "quality": bundle.quality,
        "changeovers": bundle.changeovers,
    }

    for name, frame in frames.items():
        missing = _missing_columns(frame, REQUIRED_COLUMNS[name])
        checks.append(_check(f"schema_{name}", not missing, f"Colonnes manquantes: {sorted(missing)}" if missing else "Schéma complet"))
        id_col = ID_COLUMNS[name]
        duplicates = int(frame[id_col].duplicated().sum()) if id_col in frame else len(frame)
        checks.append(_check(f"unique_{id_col}", duplicates == 0, f"Doublons: {duplicates}"))
        checks.append(_check(f"non_empty_{name}", len(frame) > 0, f"Lignes: {len(frame):,}"))

    production = bundle.production
    downtime = bundle.downtime
    quality = bundle.quality
    changeovers = bundle.changeovers

    checks.append(_check("production_quality_row_count", len(production) == len(quality), f"production={len(production):,}; quality={len(quality):,}"))
    missing_quality_links = set(production["production_event_id"]) - set(quality["production_event_id"])
    extra_quality_links = set(quality["production_event_id"]) - set(production["production_event_id"])
    checks.append(_check("quality_referential_integrity", not missing_quality_links and not extra_quality_links, f"Liens manquants={len(missing_quality_links)}; liens orphelins={len(extra_quality_links)}"))

    invalid_prod_duration = int(((production["elapsed_time_s"] < 0) | (production["net_cycle_time_s"] < 0) | (production["downtime_overlap_s"] < 0)).sum())
    checks.append(_check("production_durations_nonnegative", invalid_prod_duration == 0, f"Lignes invalides: {invalid_prod_duration}"))
    duration_gap = (production["elapsed_time_s"] - production["net_cycle_time_s"] - production["downtime_overlap_s"]).abs()
    checks.append(_check("production_time_reconciliation", bool((duration_gap <= 1).all()), f"Écart maximal: {duration_gap.max():.1f} s"))

    invalid_dt = int((downtime["duration_s"].isna() | (downtime["duration_s"] <= 0)).sum())
    checks.append(_check("downtime_duration_positive", invalid_dt == 0, f"Lignes invalides: {invalid_dt}"))
    invalid_co = int((changeovers["actual_duration_s"].isna() | (changeovers["actual_duration_s"] <= 0)).sum())
    checks.append(_check("changeover_duration_positive", invalid_co == 0, f"Lignes invalides: {invalid_co}"))

    planned_dt = downtime.loc[downtime["planned_flag"].fillna(False)].groupby("station_id")["duration_s"].sum()
    changeover_dt = changeovers.groupby("station_id")["actual_duration_s"].sum()
    stations = sorted(set(planned_dt.index) | set(changeover_dt.index))
    gaps = {station: float(planned_dt.get(station, 0) - changeover_dt.get(station, 0)) for station in stations}
    checks.append(_check("planned_downtime_changeover_reconciliation", all(abs(value) < 1e-9 for value in gaps.values()), f"Écarts par poste: {gaps}"))

    first_article_values = set(changeovers["first_article_result"].dropna().astype(str))
    checks.append(_check("changeover_first_article_domain", first_article_values.issubset({"PASS", "FAIL"}), f"Valeurs observées: {sorted(first_article_values)}"))
    first_article_fail = int((changeovers["first_article_result"].fillna("") == "FAIL").sum())
    checks.append(_check("changeover_first_article_results_counted", True, f"Premiers articles FAIL observés: {first_article_fail}", critical=False))
    if first_article_fail:
        warnings.append(f"{first_article_fail} changement(s) présentent un premier article FAIL; ils sont conservés dans l'analyse qualité.")

    failed_critical = [item for item in checks if item.critical and not item.passed]
    report = {
        "status": "PASS" if not failed_critical else "FAIL",
        "checks_total": len(checks),
        "checks_passed": sum(item.passed for item in checks),
        "critical_issues": len(failed_critical),
        "warning_count": len(warnings),
        "warnings": warnings,
        "checks": [asdict(item) for item in checks],
    }
    return report


def raise_for_critical(report: dict) -> None:
    if report["status"] != "PASS":
        failed = [item["name"] for item in report["checks"] if item["critical"] and not item["passed"]]
        raise ValueError(f"Validation bloquante: {', '.join(failed)}")
