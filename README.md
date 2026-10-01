# EMA-120 Industrial Performance and Industry 4.0

End-to-end industrial engineering portfolio project covering data design, production analysis, OEE, bottleneck diagnosis, VSM, root-cause analysis, SMED, Python automation, Power BI, scenario calculations, and a synthetic business case.

> **Important disclaimer:** EMA-120 is a fictitious production system. All production, maintenance, quality, changeover, and financial data are synthetic. The project demonstrates engineering methods and analytical reasoning; it does not report results from a real factory.

## Problem statement

The simulated line must deliver **210 units per day**, but observed output is **157.2 units per day**, or **74.9%** of demand. The analysis identifies the constraint, quantifies the losses, proposes a measurable improvement scenario, and defines the conditions required before deployment.

## System studied

The line contains seven sequential stations:

| Station | Process | Standard cycle time |
|---|---|---:|
| ST10 | Kitting and verification | 180 s |
| ST20 | Mechanical pre-assembly | 215 s |
| ST30 | Shaft and bearing assembly | 240 s |
| ST40 | Controlled assembly and tightening | 225 s |
| ST50 | Functional testing | 285 s |
| ST60 | Quality control | 200 s |
| ST70 | Identification and packaging | 160 s |

The simulation covers **20 production days**, **2 shifts per day**, and **440 planned minutes per shift**. Available production time is **52,800 seconds per day**, giving a takt time of **251.4 seconds per unit**.

## Dataset

Four linked synthetic datasets are supplied in `data/raw/` and validated versions are stored in `data/processed/`:

- `production.csv`: 25,625 production events;
- `downtime.csv`: 949 downtime records in the full event log;
- `changeovers.csv`: 360 changeover records;
- `quality.csv`: 25,625 quality records.

The initial dataset validation performed 39 schema, key, chronology, range, reconciliation, and referential-integrity checks. The baseline passed all 39 checks with no critical issue or warning. The reusable Python pipeline runs its own 21 checks when loading the supplied data.

FPY uses first-pass operations only. Scrap counts include terminal rejections on every pass, including failed rework, and count distinct physical products. Station scrap rates divide those scrap counts by first-pass arrivals at the same station. Scrap in the first-pass defect Pareto is attributed to the initial defect at the station where the product was eventually rejected.

## Methodology

1. Define the product, route, operating calendar, demand, and KPI conventions.
2. Generate and validate relational production, downtime, changeover, and quality data.
3. Calculate takt time, cycle-time distributions, theoretical capacity, effective load, and OEE.
4. Diagnose downtime, quality, WIP, flow, and the primary bottleneck.
5. Build a current-state VSM and a data-backed root-cause analysis.
6. Design SMED, line-balancing, maintenance, quality, and FIFO actions.
7. Automate the analysis in Python and visualize it in Power BI.
8. Compare the baseline with an improved scenario and document economic sensitivity.

## Main findings

- **Observed output:** 157.2 units/day versus 210 units/day demand.
- **Primary constraint:** ST50 functional testing.
- **ST50 effective load:** 329.4 s/unit versus 251.4 s/unit takt.
- **ST50 OEE:** 83.34%, with Availability 91.14%, Performance 93.45%, and Quality 97.85%.
- **WIP before ST50:** 664 units, equivalent to 3.16 days of customer demand.
- **ST50 changeover:** 25 minutes per event and 67,500 seconds over the study period.
- **Main targeted unplanned losses:** sensor faults and equipment failures, representing 79.7% of ST50 unplanned downtime.
- **Main targeted quality codes:** QL-C06, QL-C07, and QL-C08, representing 53 of 68 first-pass defects at ST50.

## Root causes and improvement plan

The analysis separates measured losses from assumptions that require pilot confirmation. Five actions are prioritized:

1. Cap the FIFO before ST50 at one shift of demand, or 105 units.
2. Rebalance 33.6 seconds of standard work away from ST50.
3. Apply SMED to reduce internal changeover time from 25 to 12.5 minutes.
4. Run targeted maintenance on sensor and equipment failure modes.
5. Complete an MSA before testing poka-yoke solutions for the three dominant defect codes.

## Before and after scenario

| KPI | Baseline | Proposed scenario | Change |
|---|---:|---:|---:|
| ST50 OEE | 83.34% | Not calculated | Unavailable |
| Reference capacity / demand | 76.33% | 90.10% estimated | +13.78 points |
| ST50 downtime over 20 days | 25.98 h | 13.73 h projected | -47.17% |
| Estimated scrap | 6.00 units | 3.66 units | -38.97% |
| Reference capacity | 160.29 units/day | 189.22 units/day | +18.05% |
| Changeover duration | 25.0 min | 12.5 min | -50.0% |

The proposed capacity remains **20.8 units/day below demand**. The 90.10% figure is reference scenario capacity divided by demand, not OEE. It differs from observed baseline demand attainment (74.9%), which uses finished output. Future OEE requires a separate calculation of Availability, Performance, and Quality with consistent cycle and counting conventions. The line must not be declared capable until field pilots confirm the new cycle, downtime, quality, and changeover performance.

## Synthetic business case

The workbook in `excel/J19_Business_Case_ROI_Action_Plan_EMA120.xlsx` provides low, base, and high sensitivities. In the base sensitivity, the model returns:

- annual net benefit: **EUR 141,229**;
- initial investment: **EUR 38,000**;
- first-year ROI: **271.7%**;
- payback period: **3.2 months**.

These values are not real savings. They depend on synthetic unit margin, downtime cost, scrap value, implementation cost, and benefit-realization assumptions. Capacity value and downtime savings may partially overlap, so the case must be rebuilt after measured pilots using actual costs and sold throughput.

## Industry 4.0 architecture

The project uses a traceable analytical chain:

`Synthetic shop-floor events -> validated CSV layer -> Python KPI pipeline -> Excel engineering analyses -> Power BI management dashboard -> pilot decisions`

Source hashes, validation results, calculation conventions, and limitations are retained so the results can be audited and reproduced.

## Repository structure

```text
industrial-performance-industry4.0/
├── README.md
├── docs/
├── data/
│   ├── raw/
│   └── processed/
├── src/
├── excel/
├── powerbi/
├── vsm/
├── root_cause_analysis/
├── images/
├── run_analysis.py
├── config.json
└── requirements.txt
```

## Reproduce the Python analysis

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_analysis.py
```

The script reads the validated data, recalculates the core KPIs, regenerates tables and figures, and writes validation and run manifests.

Run the quality-counting regression tests with:

```bash
python -m unittest discover -s tests -v
```

The supplied baseline contains six scrapped products: one at ST40, three at ST50, and two at ST60. The tests cover direct scrap, scrap after rework, recovered rework, station attribution, and the supplied baseline. Corrected quality exports and a concise verification summary are included in `verification/`.

## Portfolio visuals

Seven selected figures are stored in `images/`:

1. daily output versus demand;
2. effective load by station;
3. ST50 downtime Pareto;
4. quality-defect Pareto;
5. current-state VSM;
6. Before and After comparison;
7. economic sensitivity and ROI.

## Limitations

- The production system, event history, losses, and financial assumptions are synthetic.
- The model does not prove physical feasibility, operator safety, ergonomic acceptability, or product conformity.
- Proposed reductions in maintenance and quality losses require measured pilots.
- OEE comparisons depend on consistent definitions of planned time, operating time, total count, good count, and ideal cycle time.
- Future OEE has not been calculated; the scenario's capacity-to-demand ratio must not be described as OEE.
- Estimated scrap reduction applies a ratio derived from ST50 defect families to total line scrap; that assumption requires validation by station.
- The base scenario still fails to meet the demand of 210 units/day.
- A structural ST50 solution may be required if pilots do not close the remaining capacity gap.

## Author

**Mohamed Alae Mountassir**  
Aerospace Engineering student at IMT Mines Albi  
Project focus: industrial performance, continuous improvement, data analytics, and Industry 4.0
