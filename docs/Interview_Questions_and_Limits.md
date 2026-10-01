# Interview questions and project limits

## Questions and concise answers

### Is this a real factory project

No. EMA-120 is a fictitious production system and the datasets are synthetic. The value of the project is the consistency of the engineering model, the reproducibility of the analysis, and the fact that assumptions are separated from measured baseline values.

### Why did you identify ST50 as the bottleneck

ST50 has a standard cycle time of 285 seconds, above the takt of 251.4 seconds. Its observed effective load is 329.4 seconds per unit, the highest in the line. It is the dominant station in every analyzed production period and has 664 units of WIP immediately upstream.

### Why is the ST50 OEE not the lowest OEE in the line

OEE alone does not determine the physical constraint. A station can have a lower OEE because its ideal cycle is much shorter and still retain excess capacity. I used effective load, capacity, takt pressure, WIP, and dominance by period to identify the bottleneck. Station OEEs were not averaged.

### How did you avoid double counting production and rework

Total count for OEE uses first-pass production events only. Rework passes are modeled as additional load, not new products. Good count uses first-pass units that are good or accepted without scrap. This keeps throughput, quality, and rework logically separated.

### How are scrap and FPY counted

FPY uses first-pass results. Scrap counts distinct physical products rejected on any pass, including rework. The supplied data has six final scraps: one at ST40, three at ST50, and two at ST60. Station scrap rates use first-pass arrivals at that station as the denominator. The first-pass defect Pareto attributes each final scrap to the initial defect at its terminal rejection station.

### Is 90.10 percent the projected OEE

No. It is the estimated reference capacity of 189.22 units/day divided by demand of 210 units/day. Initial ST50 OEE is 83.34 percent, but future OEE has not been calculated. It requires new Availability, Performance, and Quality factors and consistent conventions after balancing.

### Why does the proposed scenario not reach 210 units per day

The selected actions remove measured or targeted losses, but the remaining ST50 effective load is still too high. The model reaches 189.2 units per day and leaves a gap of 20.8 units per day. A structural solution such as parallel testing, separation of manual and automatic work, or additional capacity may still be necessary.

### Why did you choose a 12.5 minute SMED target

The target is not arbitrary. The 25-minute internal changeover was decomposed into tasks. The proposed standard retains 750 seconds of internal work after moving 420 seconds outside the stop and eliminating or simplifying 330 seconds. The target must still be confirmed on at least ten changes per transition.

### How reliable is the ROI

It is a synthetic sensitivity, not a financial forecast. The workbook shows low, base, and high cases for realization rate, unit contribution, downtime cost, scrap value, investment, and recurring cost. It also warns that capacity value and downtime savings may overlap. A real ROI requires measured pilot results, actual costs, and evidence that the additional output is sold.

### What would you do first in a real plant

I would confirm definitions and data capture, observe ST50 at the workplace, film and time at least 30 representative cycles, validate safety and ergonomics, verify the changeover task breakdown, perform MSA before changing quality thresholds, and run short pilots with controlled KPI tracking.

### What did Python add compared with Excel

Excel supports transparent engineering calculations and review. Python makes data loading, validation, KPI calculation, Pareto generation, and figure production repeatable. Both use the same validated data and definitions, and Power BI provides the management view.

### What is the main technical lesson

A strong industrial diagnosis needs consistent definitions and several converging signals. Takt, cycle time, capacity, OEE, WIP, downtime, quality, and flow must agree before an action is selected. A visually attractive dashboard cannot compensate for weak conventions or unvalidated assumptions.

## Limits to state without hesitation

- The line and all operational records are fictitious.
- The event distributions are engineered simulations and do not capture every human or physical effect.
- No safety, ergonomic, machine-capability, or product-validation trial was performed.
- The SMED task split is an engineering reconstruction calibrated to the observed 25 minutes.
- Maintenance and quality improvements are pilot hypotheses.
- Future OEE is not calculated. The 90.10 percent capacity-to-demand ratio must not be labeled OEE.
- Estimated scrap reduction applies a ratio from targeted ST50 defect families to total line scrap; validate its effect at each station.
- Financial inputs are synthetic and may include partial overlap between capacity and downtime value.
- The scenario still misses customer demand by 20.8 units per day.
- The Power BI file requires Power BI Desktop and was not designed as a production MES application.

## Questions to ask the interviewer

- How are bottlenecks and OEE conventions standardized across your production sites
- Which data source is considered authoritative for cycle time, downtime, quality, and changeovers
- How are improvement pilots validated before a new standard is released
- What balance do your teams maintain between Excel analysis, Python automation, MES data, and Power BI reporting
- Which industrial problem would provide the highest value during the internship: capacity, reliability, quality, flow, or digitalization
