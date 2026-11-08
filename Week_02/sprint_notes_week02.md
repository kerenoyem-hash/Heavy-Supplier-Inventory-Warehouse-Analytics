# Sprint 2 Notes: Data Cleaning, Validation & Integrity Checks

**Project:** Heavy Supplier, Inventory & Warehouse Analytics (CadetX Virtual Work Experience)
**Sprint:** Week 02 · Fri 30 Oct – Thu 5 Nov 2026 (Days 8–14)
**Prepared by:** Keren Oyem (Data Analyst, individual submission)
**Phase:** Phase 1 · Foundation & Exploration

> Items marked **[FILL IN]** need information only you have (commit hash, pytest result, submission time).

---

## 1. Sprint goal

Produce a reproducible, validated clean data layer and resolve or formally document every data-quality issue.

## 2. Selected tasks

| Code | Catalogue task | Covered by | Status |
|---|---|---|---|
| A2 | Data Cleaning & Quality Improvement | Notebook Tasks 1, 5 | Done |
| A5 | Data Validation & Consistency Checks | Notebook Tasks 2, 3, 4 | Done |
| G4 | Data Integrity & Error Detection | Notebook Tasks 4, 5, 6 | Done |

Completion: **3 of 3 catalogue tasks closed**; cumulative **4 of 59 (7%)**.

### Work breakdown

| # | Task | Status |
|---|---|---|
| 1 | Type casting and standardisation | Done |
| 2 | Stock position reconstruction and reconciliation | Done, discrepancies flagged |
| 3 | Financial reconciliation | Done, exceptions flagged |
| 4 | Referential integrity and business-rule checks | Done |
| 5 | Automated checks (pytest) and Parquet export | Done |
| 6 | Issue log and resolution decisions | Done |

Single deliverable notebook: `02_cleaning_validation.ipynb` (Tasks 1–6, with explanation, output notes and summary for each task).

## 3. Daily progress log

**[FILL IN]** your actual daily progress. Planned flow for the week:

| Date | Focus | Done / Next / Blockers |
|---|---|---|
| Fri 30 Oct | Sprint planning; prioritise issue log by business impact | [FILL IN] |
| Fri–Sat | Type casting and standardisation | [FILL IN] |
| Sat–Sun | Stock reconstruction and reconciliation | [FILL IN] |
| Sun–Mon | Financial reconciliation; integrity and business rules | [FILL IN] |
| Tue | Pytest suite; Parquet export | [FILL IN] |
| Wed | Issue-log decisions; sprint review and retro | [FILL IN] |
| Thu 5 Nov | Notes, README, tag, submission | [FILL IN] |

## 4. Review: what was delivered

### Task 1: Type casting and standardisation
* `warehouse_capacity` (text, e.g. `45230 sqft`) converted to numeric `warehouse_capacity_sqft` for all 6 branches.
* `dimensions_cm` split into `length_cm`, `width_cm`, `height_cm`; `volume_m3` calculated for all 30 products.
* `pincode` (customers, suppliers) converted from number to 6-character text.
* All reviewed date columns already `DATE`; only `received_date` has blanks (2,370, all on cancelled POs: accepted).
* No spelling or spacing clashes in category labels.

### Task 2: Stock reconstruction
* Stock rebuilt as opening + IN − OUT ± ADJUSTMENT for all 180 product-branch pairs.
* Ledger is internally consistent for 180 / 180 pairs (order-independent test).
* `current_stock` equals the ledger balance for 166 / 180 pairs and is consistent with it for 171 / 180.
* All 2,454 ADJUSTMENT quantities are positive, so gain/loss direction is not stored.
* The earlier "179 of 180 mismatch" was caused by text-sorted `movement_id` and unsigned adjustments, not bad data.

### Task 3: Financial reconciliation
* Line arithmetic, GST (18% / 28% only) and header-vs-line totals: no exceptions in sales or purchase data.
* Invoices vs payments: 393 invoices ambiguous (reused `invoice_id`), 52 overpaid, 67 stored `Paid` but only partly paid.
* Customer `total_purchase_value` does not reconcile with transactions (stored ≈ 5% of recomputed); recomputed field added.
* Cancelled sales orders (1,967) have no invoices, as expected.

### Task 4: Referential integrity and business rules
* All 17 foreign keys valid: 0 orphans, 0 nulls.
* Primary keys unique in 10 tables. **197** surplus `invoice_id` rows and **202** surplus `payment_id` rows; no exact copies, so these are re-issued IDs on different records.
* Cancelled POs have no received date; active POs all have one.
* No delivery before its order date; all 1,967 cancelled orders still carry a delivery date (placeholder).
* 22 customers sit in regions with no local branch (service-coverage note).

### Task 5: Automation and export
* `src/cleaning.py`: reusable pipeline, run with `python -m src.cleaning`; raw database opened read-only.
* `tests/test_data_quality.py` + `tests/conftest.py`: pytest suite (rule tests and pinned known-issue tests).
* 12 cleaned tables written to `data/processed/*.parquet`; row counts match raw; no original column dropped.

### Task 6: Issue log
* 28 issues logged, each with severity, evidence, decision, treatment and owner.
* Decisions: Fix · Flag · Accept · Exclude (counts in notebook section 6.2).
* Saved to `docs/dq_issue_log_v2.csv` (and `.xlsx` if `openpyxl` is installed).

## 5. Key results

| KPI | Result |
|---|---|
| Tables profiled and validated | 12 of 12 |
| Foreign keys valid | 17 of 17 |
| Header = line totals | Sales 20,000 / 20,000; purchase 24,000 / 24,000 |
| Stock pairs consistent with ledger | 180 of 180 |
| Issues logged | 28 |
| Pytest result | **[FILL IN: e.g. "N passed"]** |

## 6. Decisions taken this sprint

1. **Never delete rows.** Problems are carried by flag columns (`is_cancelled`, `invoice_id_duplicated`, `payment_id_duplicated`, `current_above_max_flag`, `purchase_value_mismatch_flag`).
2. **Derive payment status from payments**, not the stored `payment_status`.
3. **Recompute customer purchase value** from delivered orders; keep the original for comparison only.
4. **Join invoices to orders on `so_id`**, not `invoice_id`.
5. **Accept** missing `received_date` on cancelled POs; no dates invented.
6. **Use the ledger** as the stock source of truth.

## 7. Retrospective

| Keep | Improve | Try |
|---|---|---|
| Order-independent stock test (removed a false 179/180 mismatch) | Prove a key is unique before joining on it | Ask the programme coordinator for the Fields Documentation (adjustment direction, ID meaning) |
| Labelling uncertain invoices *Ambiguous* instead of guessing | Generate numbers in result notes from live output | Request a sequence column or timestamp in the ledger |
| Flag columns instead of deleting rows | Run the notebook top to bottom before writing a status | Pin known issues in tests from day one |
| Known-issue tests pinned to recorded sizes | | Decide how to treat reused `payment_id` values when building the star schema in Week 3 |

## 8. Risks and open questions

| Item | Impact | Next step |
|---|---|---|
| Direction of ADJUSTMENT movements unknown | Shrinkage analysis (Week 11) | Confirm with coordinator / Fields Documentation |
| Cause of 52 overpaid invoices | Receivables accuracy | Business answer needed |
| Genuine `current_stock` differences (notebook 2.4) | Stock health figures | Investigate in Week 5 |
| Reused `invoice_id` / `payment_id` | Payment attribution for 393 invoices | Join on `so_id`; keep ambiguity flag in star schema |

## 9. Carry-over

None. All three catalogue tasks closed. **[FILL IN]** if any admin item (e.g. Word versions of the issue log and validation report) is still open.

## 10. Definition of done

- [x] Cleaning pipeline re-runs end-to-end from raw with one command (`python -m src.cleaning`)
- [x] Every known issue has a decision and rationale
- [x] Cleaned Parquet layer in `data/processed/`
- [ ] All tests pass (record the result in section 5)
- [ ] Sprint notes, README week entry and git tag `week-02` pushed
- [ ] Repo link submitted in the portal (Week 2 deadline: Thu 5 Nov 2026, 20:00 IST)

## 11. Submission

| Field | Value |
|---|---|
| Commit hash | [FILL IN] |
| Git tag | `week-02` |
| Portal submission time | [FILL IN] |
