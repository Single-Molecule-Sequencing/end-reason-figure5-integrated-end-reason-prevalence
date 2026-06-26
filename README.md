# end-reason-figure5-integrated-end-reason-prevalence

> 📄 Companion repository for the **End Reason** Data Descriptor — canonical manuscript: [Single-Molecule-Sequencing/end_reason_6_5_26](https://github.com/Single-Molecule-Sequencing/end_reason_6_5_26).


Companion analysis repo for Figure 5 integrated end-reason prevalence, rebuilt from deposited Great Lakes recount outputs.

## Layout

- `1_experiment/` deposited input tables and unresolved raw-source inventory
- `2_analysis/` deterministic renderer (no Great Lakes dependency)
- `3_results/` rendered figure outputs
- `docs/index.html` Pages landing
- `provenance/` source and run lineage

## Key deposited provenance facts

- Internal runs: **14**
- Internal reads total: **27,495,088**
- ER21..ER25 are recorded as `full_raw_counted` with source context in `1_experiment/tables/er21_er25_full_raw_context.csv`.

## Re-render

```bash
python3 2_analysis/render_figure5_prevalence.py
```

Outputs:
- `3_results/figures/figure5_integrated_end_reason_prevalence.pdf`
- `3_results/figures/figure5_integrated_end_reason_prevalence.png`
