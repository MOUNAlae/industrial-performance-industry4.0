"""Pareto des arrêts non planifiés et synthèse maintenance."""

from __future__ import annotations

import pandas as pd

from .data_loader import DatasetBundle


def _pareto(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(group_columns, dropna=False).agg(event_count=("downtime_id", "count"), duration_s=("duration_s", "sum")).reset_index()
    grouped = grouped.sort_values(["duration_s", "event_count"], ascending=[False, False]).reset_index(drop=True)
    total = float(grouped["duration_s"].sum())
    grouped["duration_share"] = grouped["duration_s"] / total if total else 0.0
    grouped["cumulative_share"] = grouped["duration_share"].cumsum()
    grouped["mean_duration_s"] = grouped["duration_s"] / grouped["event_count"]
    return grouped


def analyze_downtime(bundle: DatasetBundle, primary_station: str) -> dict[str, pd.DataFrame | dict]:
    data = bundle.downtime.loc[
        (~bundle.downtime["planned_flag"].fillna(False))
        & bundle.downtime["oee_loss_flag"].fillna(False)
    ].copy()
    station = _pareto(data, ["station_id"])
    category = _pareto(data, ["downtime_category"])
    cause = _pareto(data, ["downtime_cause_code", "downtime_category", "description"])
    primary = data.loc[data["station_id"] == primary_station]
    primary_category = _pareto(primary, ["downtime_category"])
    primary_cause = _pareto(primary, ["downtime_cause_code", "downtime_category", "description"])
    return {
        "summary": {
            "event_count": int(len(data)),
            "duration_s": float(data["duration_s"].sum()),
            "primary_station": primary_station,
            "primary_event_count": int(len(primary)),
            "primary_duration_s": float(primary["duration_s"].sum()),
        },
        "by_station": station,
        "by_category": category,
        "by_cause": cause,
        "primary_by_category": primary_category,
        "primary_by_cause": primary_cause,
    }

