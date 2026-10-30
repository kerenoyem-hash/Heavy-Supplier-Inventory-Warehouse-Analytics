<div align="center">

# CADETX VIRTUAL WORK EXPERIENCE

## SPRINT 01 REPORT

### HEAVY SUPPLIER, INVENTORY & WAREHOUSE ANALYTICS

**Sprint:** Week 01 – Data Profiling  
**Duration:** 1 Week  
**Project Duration:** 12 Weeks  
**Role:** Data Analyst  

</div>

---

## 1. Sprint Overview

Sprint 01 focused on understanding the structure, completeness, and quality of the datasets provided for the Heavy Supplier, Inventory & Warehouse Analytics project.

The primary activity was data profiling across all 12 project tables to establish an understanding of the available data before proceeding to data cleaning, transformation, and analysis.

## 2. Sprint Objectives

The objectives of this sprint were to:

- Identify and inspect all 12 project tables.
- Understand the structure and dimensions of each table.
- Examine column names and data types.
- Identify missing and null values.
- Check for duplicate row patterns.
- Document initial data quality observations.
- Identify potential data standardisation requirements.
- Establish a foundation for subsequent project activities.

## 3. Activities Completed

The following activities were performed:

1. Connected to the project database using DuckDB.
2. Retrieved and inspected all 12 available tables.
3. Examined the structure of each table.
4. Identified the number of rows and columns.
5. Checked for missing and null values.
6. Checked for duplicate row patterns.
7. Reviewed column names and data types.
8. Identified potential data quality issues.
9. Documented the profiling results and observations.

## 4. Data Profiling Results

The following table summarises the profiling results for all 12 project tables.

| S/N | Table Name | Rows | Columns | Missing Values | Duplicate Row Patterns |
|---|---|---:|---:|---:|---:|
| 1 | branches | 6 | 13 | 0 | 0 |
| 2 | products | 30 | 23 | 0 | 0 |
| 3 | inventory_master | 180 | 8 | 0 | 0 |
| 4 | suppliers | 8 | 12 | 0 | 0 |
| 5 | customers | 500 | 15 | 0 | 0 |
| 6 | invoices | 18,033 | 10 | 0 | 0 |
| 7 | payments | 19,257 | 5 | 0 | 0 |
| 8 | purchase_orders_header | 24,000 | 10 | 2,370 | 0 |
| 9 | purchase_orders_lines | 155,495 | 9 | 0 | 0 |
| 10 | sales_orders_header | 20,000 | 11 | 0 | 0 |
| 11 | sales_orders_lines | 130,402 | 9 | 0 | 0 |
| 12 | stock_ledger | 237,230 | 9 | 0 | 0 |
| | **TOTAL** | **704,168** | **134** | **2,370** | **0** |

## 5. Key Findings

### 5.1 Missing Values

The profiling exercise identified missing values in one table.

| Table | Column | Missing Values |
|---|---|---:|
| purchase_orders_header | received_date | 2,370 |

The missing values in `received_date` may represent purchase orders that have not yet been received or records with incomplete delivery information.

Further investigation will be required before deciding how to handle these missing values.

### 5.2 Duplicate Records

No duplicate row patterns were identified across the 12 tables.

However, primary key and composite key uniqueness will require separate validation.

### 5.3 Potential Data Standardisation Areas

The following columns were identified for further review during the data-cleaning stage.

| Table | Column | Current Data Type | Recommended Review |
|---|---|---|---|
| branches | warehouse_capacity | VARCHAR | Review and convert to numeric capacity where appropriate |
| products | dimensions_cm | VARCHAR | Extract dimensions into separate numeric columns |
| suppliers | pincode | BIGINT | Review identifier formatting |
| customers | pincode | BIGINT | Review identifier formatting |
| sales_orders_lines | unit_price | BIGINT | Review financial data type |
| sales_orders_lines | line_total | BIGINT | Review financial data type |

These are potential standardisation areas and have not yet been confirmed as data errors.

## 6. Data Quality Considerations

Further validation is recommended in the following areas:

- Primary key uniqueness.
- Foreign key relationships.
- Date consistency across related tables.
- Negative or invalid numerical values.
- Financial calculations and reconciliation.
- Inventory stock consistency.
- Categorical value standardisation.
- Appropriate data types for numerical and financial columns.

These checks will support the preparation of reliable datasets for subsequent analysis.

## 7. Sprint Deliverables

| S/N | Deliverable | Description | Status |
|---|---|---|---|
| 1 | Data Profiling Notebook | Jupyter Notebook containing the profiling code and results. | Completed |
| 2 | Master Table Profiling | Profiling assessment covering all 12 tables. | Completed |
| 3 | Data Quality Assessment | Identification of missing values and duplicate row patterns. | Completed |
| 4 | Profiling Findings | Documentation of observations and potential data quality concerns. | Completed |
| 5 | Business Questions | Draft business questions to guide subsequent analysis. | Drafted |
| 6 | Sprint Report | Documentation of Week 01 activities, findings, and deliverables. | Completed |

## 8. Challenges and Observations

The profiling exercise established an initial understanding of the project database.

The main observation was the presence of 2,370 missing values in the `received_date` column of the `purchase_orders_header` table.

Additional attention will be required during subsequent project activities to investigate missing values, review data types, and validate relationships between the tables.

## 9. Sprint Conclusion

Sprint 01 successfully completed the initial data profiling exercise across all 12 tables in the Heavy Supplier, Inventory & Warehouse Analytics project.

The profiling covered a total of 704,168 records and 134 columns.

The exercise identified 2,370 missing values in the `received_date` column of the `purchase_orders_header` table. No duplicate row patterns were identified across the tables.

The findings provide a foundation for the data cleaning, standardisation, and analytical activities planned for subsequent sprints.
