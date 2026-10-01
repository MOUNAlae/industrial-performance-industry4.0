"""FPY au premier passage et rebuts terminaux sur tous les passages."""

from __future__ import annotations

import pandas as pd

from .data_loader import DatasetBundle


def analyze_quality(bundle: DatasetBundle, station_order: list[str]) -> dict[str, pd.DataFrame | dict]:
    # Un rebut après retouche est porté par un événement de passage 2.
    # Le compter à partir des seuls premiers passages le ferait disparaître.
    terminal_scrap = bundle.production[[
        "production_event_id", "serial_number", "station_id"
    ]].merge(
        bundle.quality.loc[bundle.quality["scrap_flag"].fillna(False), ["production_event_id"]],
        on="production_event_id", how="inner", validate="one_to_one",
    )
    scrap_by_station = terminal_scrap.groupby("station_id")["serial_number"].nunique()
    scrapped_keys = terminal_scrap[["serial_number", "station_id"]].drop_duplicates()
    scrapped_keys["final_scrap"] = True

    first = bundle.production.loc[bundle.production["pass_number"] == 1, [
        "production_event_id", "serial_number", "product_variant", "production_date", "shift_id", "station_id"
    ]].copy()
    qcols = [
        "production_event_id", "quality_result", "disposition", "rework_required_flag", "scrap_flag",
        "first_pass_flag", "defect_code", "defect_category", "origin_station_id", "rework_duration_s", "notes"
    ]
    joined = first.merge(bundle.quality[qcols], on="production_event_id", how="left", validate="one_to_one")
    joined = joined.merge(
        scrapped_keys, on=["serial_number", "station_id"], how="left", validate="many_to_one",
    )
    joined["final_scrap"] = joined["final_scrap"].eq(True)
    joined["good_first_pass"] = (
        joined["quality_result"].eq("PASS")
        & joined["disposition"].eq("ACCEPT")
        & joined["first_pass_flag"].fillna(False)
        & ~joined["scrap_flag"].fillna(False)
    )
    joined["first_pass_fail"] = ~joined["good_first_pass"]

    by_station = joined.groupby("station_id").agg(
        total_first_pass=("production_event_id", "count"),
        good_first_pass=("good_first_pass", "sum"),
        first_pass_fail=("first_pass_fail", "sum"),
        rework_required=("rework_required_flag", "sum"),
        rework_duration_s=("rework_duration_s", "sum"),
    ).reindex(station_order).reset_index()
    by_station["scrap"] = by_station["station_id"].map(scrap_by_station).fillna(0).astype(int)
    # Conserver le schéma de sortie : le taux de rebut d'un poste utilise
    # les unités entrées à ce poste, soit les premiers passages.
    by_station = by_station[[
        "station_id", "total_first_pass", "good_first_pass", "first_pass_fail",
        "rework_required", "scrap", "rework_duration_s",
    ]]
    by_station["fpy"] = by_station["good_first_pass"] / by_station["total_first_pass"]
    by_station["rework_rate"] = by_station["rework_required"] / by_station["total_first_pass"]
    by_station["scrap_rate"] = by_station["scrap"] / by_station["total_first_pass"]

    failures = joined.loc[joined["first_pass_fail"]].copy()
    failures["defect_code"] = failures["defect_code"].fillna("NON_CODE")
    defect = failures.groupby(["defect_code", "defect_category"], dropna=False).agg(
        count=("production_event_id", "count"),
        rework_duration_s=("rework_duration_s", "sum"),
        # Attribution au défaut du premier passage au poste de mise au rebut.
        scrap_count=("final_scrap", "sum"),
    ).reset_index().sort_values(["count", "rework_duration_s"], ascending=[False, False]).reset_index(drop=True)
    total_failures = int(defect["count"].sum())
    defect["share"] = defect["count"] / total_failures if total_failures else 0.0
    defect["cumulative_share"] = defect["share"].cumsum()

    by_variant = joined.groupby("product_variant").agg(
        total_first_pass=("production_event_id", "count"),
        good_first_pass=("good_first_pass", "sum"),
        first_pass_fail=("first_pass_fail", "sum"),
    ).reset_index()
    by_variant["fpy"] = by_variant["good_first_pass"] / by_variant["total_first_pass"]

    return {
        "summary": {
            "total_first_pass": int(len(joined)),
            "good_first_pass": int(joined["good_first_pass"].sum()),
            "first_pass_fail": int(joined["first_pass_fail"].sum()),
            "overall_fpy": float(joined["good_first_pass"].mean()),
            "scrap_units": int(terminal_scrap["serial_number"].nunique()),
        },
        "by_station": by_station,
        "by_variant": by_variant,
        "defect_pareto": defect,
    }
