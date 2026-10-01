"""Visualisations industrielles reproductibles en PNG."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


NAVY = "#0A1F33"
BLUE = "#0B63CE"
CYAN = "#28B8D5"
ORANGE = "#E67E22"
RED = "#C0392B"
GREEN = "#26734D"
GRID = "#CBD5E1"


def _finish(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def station_load_chart(station_kpis: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    colors = [RED if station == "ST50" else BLUE for station in station_kpis["station_id"]]
    ax.bar(station_kpis["station_id"], station_kpis["effective_load_s_per_unit"], color=colors)
    takt = float(station_kpis["takt_s_per_unit"].iloc[0])
    ax.axhline(takt, color=ORANGE, linewidth=2, linestyle="--", label=f"Takt {takt:.1f} s/u")
    ax.set_title("Charge effective par poste")
    ax.set_ylabel("Secondes par unité")
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax.legend(frameon=False)
    path = output_dir / "station_effective_load.png"
    _finish(fig, path)
    return path


def downtime_pareto_chart(primary_by_cause: pd.DataFrame, output_dir: Path, primary_station: str) -> Path:
    data = primary_by_cause.head(8).copy()
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    ax.bar(data["downtime_cause_code"], data["duration_s"] / 60, color=BLUE)
    ax.set_title(f"Pareto des arrêts non planifiés - {primary_station}")
    ax.set_ylabel("Durée (min)")
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax2 = ax.twinx()
    ax2.plot(data["downtime_cause_code"], data["cumulative_share"] * 100, color=ORANGE, marker="o", linewidth=2)
    ax2.set_ylabel("Cumul (%)")
    ax2.set_ylim(0, 105)
    path = output_dir / "downtime_pareto_primary_station.png"
    _finish(fig, path)
    return path


def quality_pareto_chart(defect_pareto: pd.DataFrame, output_dir: Path) -> Path:
    data = defect_pareto.head(8).copy()
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    ax.bar(data["defect_code"], data["count"], color=GREEN)
    ax.set_title("Pareto des défauts au premier passage")
    ax.set_ylabel("Nombre de défauts")
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax2 = ax.twinx()
    ax2.plot(data["defect_code"], data["cumulative_share"] * 100, color=ORANGE, marker="o", linewidth=2)
    ax2.set_ylabel("Cumul (%)")
    ax2.set_ylim(0, 105)
    path = output_dir / "quality_defect_pareto.png"
    _finish(fig, path)
    return path


def daily_output_chart(daily_output: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.plot(daily_output["production_date"], daily_output["output_units"], color=BLUE, marker="o", linewidth=2, label="Sortie observée")
    ax.plot(daily_output["production_date"], daily_output["demand_units"], color=ORANGE, linestyle="--", linewidth=2, label="Demande")
    ax.set_title("Sortie quotidienne de la ligne")
    ax.set_ylabel("Unités par jour")
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax.legend(frameon=False)
    fig.autofmt_xdate(rotation=35)
    path = output_dir / "daily_output_vs_demand.png"
    _finish(fig, path)
    return path


def create_visualizations(station_kpis: pd.DataFrame, downtime_results: dict, quality_results: dict, daily_output: pd.DataFrame, output_dir: str | Path, primary_station: str) -> list[Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return [
        station_load_chart(station_kpis, directory),
        downtime_pareto_chart(downtime_results["primary_by_cause"], directory, primary_station),
        quality_pareto_chart(quality_results["defect_pareto"], directory),
        daily_output_chart(daily_output, directory),
    ]

