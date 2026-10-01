"""Calcul des KPI de capacité, charge effective et TRS/OEE."""

from __future__ import annotations

import pandas as pd

from .data_loader import DatasetBundle


def calculate_station_kpis(bundle: DatasetBundle, config: dict) -> pd.DataFrame:
    prod = bundle.production.copy()
    quality = bundle.quality.set_index("production_event_id")
    downtime = bundle.downtime.loc[bundle.downtime["oee_loss_flag"].fillna(False)].copy()
    changes = bundle.changeovers.copy()

    available_s_per_day = config["shifts_per_day"] * config["planned_minutes_per_shift"] * 60
    takt_s = available_s_per_day / config["daily_customer_demand_units"]
    periods = prod[["production_date", "shift_id"]].drop_duplicates()
    planned_period_s = len(periods) * config["planned_minutes_per_shift"] * 60

    rows = []
    for station in config["station_order"]:
        st = prod.loc[prod["station_id"] == station].copy()
        first = st.loc[st["pass_number"] == 1]
        rework = st.loc[st["pass_number"] > 1]
        first_count = len(first)
        if first_count == 0:
            raise ValueError(f"Aucun premier passage pour {station}")

        dt = downtime.loc[downtime["station_id"] == station]
        planned_dt_s = float(dt.loc[dt["planned_flag"].fillna(False), "duration_s"].sum())
        unplanned_dt_s = float(dt.loc[~dt["planned_flag"].fillna(False), "duration_s"].sum())
        changeover_s = float(changes.loc[changes["station_id"] == station, "actual_duration_s"].sum())
        if abs(planned_dt_s - changeover_s) > 1e-9:
            raise ValueError(f"Les arrêts planifiés ne correspondent pas aux changements pour {station}")

        q = quality.loc[first["production_event_id"]]
        good_mask = (
            q["quality_result"].eq("PASS")
            & q["disposition"].eq("ACCEPT")
            & ~q["scrap_flag"].fillna(False)
            & q["first_pass_flag"].fillna(False)
        )
        good_count = int(good_mask.sum())
        standard_cycle = float(config["standard_cycle_time_s"][station])
        operating_s = planned_period_s - planned_dt_s - unplanned_dt_s
        availability = operating_s / planned_period_s
        performance = standard_cycle * first_count / operating_s
        quality_rate = good_count / first_count
        oee = availability * performance * quality_rate

        first_net = float(first["net_cycle_time_s"].sum()) / first_count
        rework_net = float(rework["net_cycle_time_s"].sum()) / first_count
        unplanned_load = float(st["downtime_overlap_s"].sum()) / first_count
        changeover_load = changeover_s / first_count
        effective_load = (float(st["elapsed_time_s"].sum()) + changeover_s) / first_count

        rows.append({
            "station_id": station,
            "process_name": config["process_names"][station],
            "standard_cycle_time_s": standard_cycle,
            "first_pass_units": first_count,
            "rework_events": len(rework),
            "first_pass_net_load_s_per_unit": first_net,
            "rework_load_s_per_unit": rework_net,
            "unplanned_downtime_load_s_per_unit": unplanned_load,
            "changeover_load_s_per_unit": changeover_load,
            "effective_load_s_per_unit": effective_load,
            "takt_s_per_unit": takt_s,
            "pressure_vs_takt": effective_load / takt_s,
            "reference_capacity_units_per_day": available_s_per_day / effective_load,
            "availability": availability,
            "performance": performance,
            "quality": quality_rate,
            "oee": oee,
            "planned_downtime_s": planned_dt_s,
            "unplanned_downtime_s": unplanned_dt_s,
        })
    return pd.DataFrame(rows)


def calculate_daily_output(bundle: DatasetBundle, config: dict) -> pd.DataFrame:
    final_station = config["station_order"][-1]
    final_first = bundle.production.loc[(bundle.production["station_id"] == final_station) & (bundle.production["pass_number"] == 1)]
    daily = final_first.groupby(final_first["production_date"].dt.date).size().rename("output_units").reset_index()
    daily["demand_units"] = config["daily_customer_demand_units"]
    daily["attainment"] = daily["output_units"] / daily["demand_units"]
    daily["production_date"] = pd.to_datetime(daily["production_date"])
    return daily


def calculate_overall_kpis(bundle: DatasetBundle, station_kpis: pd.DataFrame, daily_output: pd.DataFrame, config: dict) -> dict:
    bottleneck = station_kpis.loc[station_kpis["effective_load_s_per_unit"].idxmax()]
    primary = station_kpis.loc[station_kpis["station_id"] == config["primary_station"]].iloc[0]
    output_per_day = float(daily_output["output_units"].mean())
    return {
        "production_days": int(len(daily_output)),
        "daily_customer_demand_units": float(config["daily_customer_demand_units"]),
        "observed_output_units_per_day": output_per_day,
        "output_attainment": output_per_day / config["daily_customer_demand_units"],
        "bottleneck_station": str(bottleneck["station_id"]),
        "bottleneck_effective_load_s_per_unit": float(bottleneck["effective_load_s_per_unit"]),
        "bottleneck_reference_capacity_units_per_day": float(bottleneck["reference_capacity_units_per_day"]),
        "primary_station": config["primary_station"],
        "primary_station_oee": float(primary["oee"]),
        "primary_station_availability": float(primary["availability"]),
        "primary_station_performance": float(primary["performance"]),
        "primary_station_quality": float(primary["quality"]),
    }

