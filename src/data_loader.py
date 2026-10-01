"""Chargement typé et traçable des sources validées EMA-120."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import pandas as pd


FILES = {
    "production": "production.csv",
    "downtime": "downtime.csv",
    "quality": "quality.csv",
    "changeovers": "changeovers.csv",
}

BOOLEAN_COLUMNS = {
    "production": ["first_pass_flag"],
    "downtime": ["planned_flag", "micro_stop_flag", "oee_loss_flag"],
    "quality": ["rework_required_flag", "scrap_flag", "first_pass_flag"],
    "changeovers": [],
}

DATE_COLUMNS = {
    "production": ["production_date", "operation_start_ts", "operation_end_ts", "record_created_ts"],
    "downtime": ["production_date", "event_start_ts", "event_end_ts", "record_created_ts"],
    "quality": ["production_date", "detection_ts", "record_created_ts"],
    "changeovers": ["production_date", "event_start_ts", "event_end_ts", "record_created_ts"],
}

NUMERIC_COLUMNS = {
    "production": ["pass_number", "standard_cycle_time_s", "elapsed_time_s", "downtime_overlap_s", "net_cycle_time_s"],
    "downtime": ["duration_s"],
    "quality": ["rework_duration_s"],
    "changeovers": ["planned_duration_s", "actual_duration_s", "internal_duration_s", "external_duration_s"],
}


@dataclass(frozen=True)
class DatasetBundle:
    production: pd.DataFrame
    downtime: pd.DataFrame
    quality: pd.DataFrame
    changeovers: pd.DataFrame
    validation_summary: dict
    file_hashes: dict[str, str]
    input_dir: Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_boolean(series: pd.Series, name: str) -> pd.Series:
    mapping = {"TRUE": True, "FALSE": False, "1": True, "0": False}
    normalized = series.astype("string").str.strip().str.upper()
    invalid = normalized.dropna()[~normalized.dropna().isin(mapping)]
    if not invalid.empty:
        raise ValueError(f"Valeurs booléennes invalides dans {name}: {sorted(invalid.unique())[:5]}")
    return normalized.map(mapping).astype("boolean")


def _load_table(input_dir: Path, key: str) -> pd.DataFrame:
    path = input_dir / FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Source manquante: {path}")
    frame = pd.read_csv(path, low_memory=False)
    if frame.empty:
        raise ValueError(f"Source vide: {path}")
    for column in BOOLEAN_COLUMNS[key]:
        if column in frame:
            frame[column] = _parse_boolean(frame[column], f"{key}.{column}")
    for column in DATE_COLUMNS[key]:
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="raise", utc=True)
    for column in NUMERIC_COLUMNS[key]:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def load_datasets(input_dir: str | Path) -> DatasetBundle:
    """Charge les quatre tables et bloque si la validation J06 n'est pas PASS."""
    directory = Path(input_dir).resolve()
    validation_path = directory / "validation_summary.json"
    if not validation_path.exists():
        raise FileNotFoundError(f"Résumé de validation manquant: {validation_path}")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS" or validation.get("critical_issues", 0) != 0:
        raise ValueError("Les données sources ne sont pas validées: statut J06 différent de PASS")
    tables = {key: _load_table(directory, key) for key in FILES}
    hashes = {FILES[key]: sha256(directory / FILES[key]) for key in FILES}
    hashes[validation_path.name] = sha256(validation_path)
    return DatasetBundle(
        production=tables["production"],
        downtime=tables["downtime"],
        quality=tables["quality"],
        changeovers=tables["changeovers"],
        validation_summary=validation,
        file_hashes=hashes,
        input_dir=directory,
    )
