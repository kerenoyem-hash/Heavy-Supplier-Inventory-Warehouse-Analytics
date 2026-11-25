# Week 04 Product Insight Brief

**Project:** Heavy Supplier, Inventory & Warehouse Analytics
**Sprint:** Week 4 (13 to 19 Nov 2026) · **Author:** Keren Oyem, Data Analyst
**Notebook:** `notebooks/04_product_performance.ipynb`

## 1. Question addressed and data used

Which products drive revenue, margin and volume, how steady is their demand, and is demand growing, falling or seasonal?

Data: 18,033 delivered sales orders (117,656 lines, 1,234,939 units), 1 Jan 2019 to 31 Dec 2024, cancelled orders excluded, from the Week 2 clean layer. Revenue is before GST: INR 22,959.0 M. Gross margin is INR 4,950.0 M (21.6%), estimated from the product master unit cost. Average order value is INR 1.27 M. The base dataset reconciled to the order headers on every check.

## 2. Key findings

1. **Revenue is concentrated, and it is driven by price, not volume.** 10 of 30 products generate 81.5% of revenue (the top 3 alone generate 44.3%). P015 Engine Block EB-600 brings 21.2% (INR 4,857 M), followed by P014 Transmission Assembly TA-800 (14.8%) and P021 Boom Cylinder BC-400 (8.4%). Yet every product sells almost the same volume, 548 to 587 units per month (about 41,000 units each over six years). P015 sells at about INR 119,000 per unit, against INR 310 for Grease Cartridge GC-5.
2. **The biggest revenue products earn a lower margin %.** P015 earns 19.8%, P014 18.0% and P010 Turbocharger 17.2%, against 21.6% overall. The highest margins sit in small, cheap categories (Lubricants 41.9%, Attachments 41.4%, Belts 38.5%, Seals 37.4%) that bring under 1% of revenue each. 12 products generate 80% of margin; the 10 revenue leaders are all among them.
3. **Every branch has the same core.** In all six branches the same 10 products make 80% of revenue (overlap 10 of 10). Branch size differs: Chennai 20.4%, Kolkata 18.9%, Ahmedabad 17.4%, Delhi 15.2%, Pune 14.7%, Hyderabad 13.4%. Average order value is nearly equal (INR 1.24 to 1.31 M), so the gap comes from the number of orders (Chennai 3,677 vs Hyderabad 2,478).
4. **Demand is steady for every product, so XYZ adds nothing.** The CV of monthly units is 0.14 to 0.19 for all 30 products, so all are X. The matrix is effectively ABC only: AX 10 products (81.5% of revenue), BX 7 (14.1%), CX 13 (4.4%). At product-branch level 176 of 180 series are X and 4 are Y; none is Z.
5. **Demand is declining slowly.** Yearly revenue fell from INR 3,870 M (2019) to INR 3,678 M (2024), about 5.0% lower, with 2024 down 3.8% on 2023. Units fell 3.9% over the same period. The Mann-Kendall test on total demand finds a significant decrease (p = 0.004; CAGR -0.8%, last year-on-year -2.3%). 9 products are decreasing, 2 increasing and 19 show no significant trend. Three A products are decreasing: P019 Swing Motor (-15.6% in 2024), P010 Turbocharger (-10.9%) and P001 Hydraulic Pump (borderline, p = 0.05).
6. **Seasonality is moderate.** Total demand has seasonal strength 0.56, peaking in July and weakest in February. At product level, 15 products are moderately seasonal and 15 weakly; none strongly. Product peaks fall in different months (for example P004 Track Chain peaks in July, P025 Cabin Glass in March, P015 in October), so there is no single season for all products.
7. **Velocity differences are small and partly reflect branch size.** The fastest product (P010, 587 units per month) and the slowest (P024, 548) differ by about 7%. P014, the second-largest revenue product, is classed Slow. At product-branch level, speed follows branch size: all 30 Chennai pairs are Fast and all 30 Hyderabad pairs are Slow. Every one of the 180 pairs had sales.

## 3. Recommendations

| # | Recommendation | Expected impact | Priority |
|---|---|---|---|
| 1 | Manage stock by **value**, not by volume. With equal volumes and very different prices, one excess unit of an AX product costs far more than one excess unit of a C product. Focus stock reduction and tight reorder control on the 10 AX products, which hold 81.5% of revenue. | Releases the most capital per unit of excess removed | High |
| 2 | Put P019, P010 and P001 (declining A products) on a replenishment review in Week 5 and cut purchasing to match demand. Also review P012, P028, P007, P020 (declining C products). | Stops excess growing on products with falling demand | High |
| 3 | Do not use the current Fast / Medium / Slow classes to set stock policy. Use days of stock cover (Week 5) and, for branches, compare velocity within each branch. | Avoids stocking decisions based on small differences | High |
| 4 | Plan purchases around the July peak and February low for total demand, but treat the pattern as moderate, not dominant. | Better timing of stock | Medium |
| 5 | Use one shared core list of 10 products for all six branches when checking branch stock in Week 6. | Simpler stocking policy | Medium |
| 6 | Review P015's supplier dependency in Week 7: one product carries 21.2% of revenue. | Lower concentration risk | Medium |

**Link to Week 2:** stock inflow was about 18 times outflow. Total demand is now slightly falling, so overstock is likely to grow unless purchasing is cut back. This is the main input for Week 5.

## 4. Limitations and assumptions

- Margin uses the product master unit cost, not actual purchase cost, so it is an estimate.
- Volume is almost identical across products (and CV is 0.14 to 0.19 for all), which looks like a feature of the supplied data. We report it as a finding rather than hide it (see the plan's risk on synthetic-data artefacts). It means XYZ and velocity separate products very little.
- With only 30 products the 80/20 splits are coarse: one product moves the shares noticeably.
- XYZ uses the default cut-offs (0.5 and 1.0). Because every product has CV below 0.2, percentile-based cut-offs would only split tiny differences and were not used.
- Velocity classes are terciles (10 / 10 / 10 by construction). At product-branch level the ranking is across all 180 pairs, so it mostly reflects branch size.
- Trend tests on monthly data are approximate (autocorrelation), and the declines are small in size even where statistically significant.

## 5. Links

- Notebook: `notebooks/04_product_performance.ipynb`
- Classification: `week-04/abc_xyz_classification.csv`, `week-04/abc_xyz_product_branch.csv`
- Velocity: `week-04/product_velocity.csv`, `week-04/product_branch_velocity.csv`
- Trend and growth: `week-04/demand_trends_product.csv`, `week-04/demand_trends_product_branch.csv`, `week-04/demand_growth_by_product.csv`
- Charts: `week-04/charts/`
