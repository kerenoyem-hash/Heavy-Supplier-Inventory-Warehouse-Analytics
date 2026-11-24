# Week 04: Product Performance & Demand Patterns

**Project:** Heavy Supplier, Inventory & Warehouse Analytics (CadetX Virtual Work Experience)
**Sprint:** Week 4, Fri 13 Nov to Thu 19 Nov 2026 (Phase 2)
**Scrum Master:** Keren Oyem
**Prepared by:** Keren Oyem, Data Analyst

## Sprint goal

Explain which products drive revenue, margin and volume, classify them, and describe demand trends and seasonality.

## Catalogue tasks

| Code | Task | Where it is done | Status |
|---|---|---|---|
| B1 | Product Performance Analysis | Notebook section 1 | Done |
| B7 | ABC / Pareto Classification (with XYZ) | Notebook section 2 | Done |
| B2 | Fast-Moving Product Identification | Notebook section 3 | Done |
| B9 | Product Demand Trend Analysis | Notebook section 4 | Done |

Completion: 4 of 4 tasks (cumulative 11 of 59).

## Headline results

Period: 1 Jan 2019 to 31 Dec 2024. Cancelled orders excluded. Revenue is before GST.

| Measure | Result |
|---|---|
| Delivered orders / order lines / units | 18,033 / 117,656 / 1,234,939 |
| Revenue | INR 22,959.0 M |
| Gross margin (estimated) | INR 4,950.0 M (21.6%) |
| Average order value | INR 1.27 M |
| Products generating 80% of revenue | 10 of 30 (top 3 = 44.3%) |
| Products generating 80% of margin | 12 of 30 |
| Top product | P015 Engine Block EB-600, 21.2% of revenue |
| Top branch | Chennai 20.4% (Hyderabad lowest, 13.4%) |
| Volume per product | 548 to 587 units/month: revenue differences come from price |
| ABC-XYZ | AX 10 (81.5% of revenue), BX 7, CX 13; all 30 products are X (CV 0.14 to 0.19) |
| Total demand trend | Decreasing (Mann-Kendall p = 0.004); 9 products decreasing, 2 increasing, 19 no trend |
| Revenue by year | INR 3,870 M (2019) to INR 3,678 M (2024); 2024 is -3.8% |
| Total demand growth | Last year-on-year -2.3%, CAGR -0.8% |
| Seasonality | Strength 0.56; peak July, weakest February |

Full findings and recommendations: `reports/week04_product_insights.md`.

## Files in this week

| File | Description |
|---|---|
| `notebooks/04_product_performance.ipynb` | Main notebook: B1, B7, B2, B9, charts, key findings |
| `src/product_analysis.py` | Helper module (base dataset, ABC-XYZ, velocity, trend, charts) |
| `week-04/abc_xyz_classification.csv` | **Deliverable.** ABC-XYZ per product |
| `week-04/product_velocity.csv` | **Deliverable.** Velocity score and class per product (reused in Week 5) |
| `week-04/abc_xyz_product_branch.csv` | ABC-XYZ for the 180 product-branch series (Week 9) |
| `week-04/product_branch_velocity.csv` | Velocity per product-branch pair (Week 5 slow and dead stock) |
| `week-04/demand_trends_product.csv`, `demand_trends_product_branch.csv` | Trend, seasonality and strength per series |
| `week-04/demand_growth_by_product.csv` | Yearly units, year-on-year change and CAGR |
| `week-04/product_performance_by_*.csv`, `performance_by_*.csv`, `pareto_by_branch.csv` | B1 summary tables |
| `week-04/charts/*.png` | 12 charts, each with title, units and a one-line takeaway |
| `reports/week04_product_insights.md` | One-page product insight brief |
| `week-04/sprint_notes.md` | Sprint notes for Week 4 |

## How to run

```bash
python -m src.cleaning          # only if data/processed/ is missing or old
jupyter lab                     # open notebooks/04_product_performance.ipynb
# Kernel > Restart & Run All
```

The notebook finds the project root by itself and writes every output to `week-04/`.

## Assumptions

1. Cancelled sales orders are excluded everywhere (Week 2 issue I19).
2. Revenue = `line_total`, before GST.
3. Cost of goods = quantity x `products.unit_cost`; gross margin = revenue - cost of goods. This is an estimate from the product master, not accounting margin.
4. Branch = branch on the sales order header.
5. Demand = units sold per calendar month by order date; months with no sales count as zero.
6. ABC cut-offs: A to 80% cumulative share, B to 95%. XYZ cut-offs: X below CV 0.5, Y below 1.0.
7. `customers.total_purchase_value` is not used (Week 2 issue I18).

## Notes for reviewers

- Every product sells almost the same volume, so XYZ places all 30 products in X and the velocity classes separate products by only about 7%. We report this as a finding about the data.
- The velocity classes (Fast / Medium / Slow) are terciles, so 10 / 10 / 10 is by construction. At product-branch level the ranking follows branch size (all Chennai pairs Fast, all Hyderabad pairs Slow).
- Total demand has a statistically significant decline, but it is small (CAGR -0.8%). Seasonality is moderate, not dominant.

## Definition of done

- [x] Each chart has a title, units and a one-line takeaway
- [x] Classifications exported as CSV for dashboards and models
- [x] All 4 catalogue tasks marked complete in `sprint_review.docx`
- [x] Sprint notes, README week entry and git tag `week-04` pushed; link submitted in the portal

