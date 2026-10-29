<div align="center">

# CADETX VIRTUAL WORK EXPERIENCE

## WEEK 01 – DATA PROFILING

### HEAVY SUPPLIER, INVENTORY & WAREHOUSE ANALYTICS

</div>

---

## 📌 Project Overview

This project is part of the CadetX Virtual Work Experience programme. It focuses on analysing supplier, inventory, warehouse, purchasing, and sales data to generate insights that can support better business decisions.

During Week 01, the primary activity was **data profiling** to understand the structure, quality, and characteristics of the datasets before proceeding with data cleaning and analysis.

## 🎯 Objectives

- Understand the structure of the available datasets.
- Identify missing values across all tables.
- Check for duplicate records.
- Examine column names and data types.
- Identify potential data quality and standardisation issues.
- Establish a foundation for subsequent analysis.

## 📊 Dataset Overview

The project contains 12 tables covering different aspects of the business.

| S/N | Table Name | Rows | Columns |
|---|---|---:|---:|
| 1 | branches | 6 | 13 |
| 2 | products | 30 | 23 |
| 3 | inventory_master | 180 | 8 |
| 4 | suppliers | 8 | 12 |
| 5 | customers | 500 | 15 |
| 6 | invoices | 18,033 | 10 |
| 7 | payments | 19,257 | 5 |
| 8 | purchase_orders_header | 24,000 | 10 |
| 9 | purchase_orders_lines | 155,495 | 9 |
| 10 | sales_orders_header | 20,000 | 11 |
| 11 | sales_orders_lines | 130,402 | 9 |
| 12 | stock_ledger | 237,230 | 9 |

## 🔍 Activities Performed

1. Loaded the project database using DuckDB.
2. Retrieved the available tables.
3. Examined the structure of each table.
4. Checked the number of rows and columns.
5. Identified missing values.
6. Checked for duplicate row patterns.
7. Reviewed column data types.
8. Documented the profiling findings.

## 📈 Key Findings

### 1. Missing Values

The profiling exercise identified missing values in one table:

- **Table:** `purchase_orders_header`
- **Column:** `received_date`
- **Missing values:** 2,370

The missing values may require further investigation during the data-cleaning stage.

### 2. Duplicate Records

No duplicate row patterns were identified across the 12 tables during the profiling exercise.

### 3. Potential Data Standardisation Areas

The following columns were identified for further review:

| Table | Column | Current Data Type | Recommended Review |
|---|---|---|---|
| branches | warehouse_capacity | VARCHAR | Convert to numeric where appropriate |
| products | dimensions_cm | VARCHAR | Extract dimensions into separate numeric columns |
| suppliers | pincode | BIGINT | Review identifier format |
| customers | pincode | BIGINT | Review identifier format |
| sales_orders_lines | unit_price | BIGINT | Review financial data type |
| sales_orders_lines | line_total | BIGINT | Review financial data type |

These are potential standardisation areas, not confirmed data errors.

## ⚠️ Data Quality Considerations

Further validation will be required to investigate:

- Primary key uniqueness.
- Foreign key relationships.
- Date consistency.
- Negative or invalid numerical values.
- Financial calculations and reconciliation.
- Inventory stock consistency.

These checks are recommended for subsequent stages of the project.

## 📁 Deliverables

The Week 01 deliverables include:

- Data profiling notebook.
- Master table profiling report.
- Data quality observations.
- Draft business questions to guide subsequent analysis.

## 🛠️ Tools and Technologies

- Python
- Jupyter Notebook
- DuckDB
- SQL
- GitHub

## 🚀 Next Steps

The next stage will focus on data cleaning and standardisation, including:

- Handling missing values.
- Standardising date columns.
- Converting appropriate columns to suitable data types.
- Cleaning categorical values.
- Extracting product dimensions into separate columns.
- Preparing the datasets for further analysis.

## 📝 Conclusion

Week 01 established an understanding of the structure and quality of the project datasets. The profiling exercise identified missing values in `purchase_orders_header.received_date` and highlighted potential areas for data standardisation.

These findings provide a foundation for the data-cleaning and transformation activities in Week 02.

---

### Prepared By

**Keren Oyem**  
**Role:** Data Analyst   
**Programme:** CadetX Virtual Work Experience
