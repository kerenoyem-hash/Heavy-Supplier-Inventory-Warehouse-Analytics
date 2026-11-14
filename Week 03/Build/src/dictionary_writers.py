import os
import pandas as pd

# ------------------------------- Excel --------------------------------------
def write_excel(path, about_rows, tables_df, dict_df, issues_df=None):
    """Write the dictionary workbook: About, Tables, Data_Dictionary (+ Issue_Log)."""
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame(about_rows, columns=["Item", "Detail"]).to_excel(xw, sheet_name="About", index=False)
        tables_df.to_excel(xw, sheet_name="Tables", index=False)
        dict_df.to_excel(xw, sheet_name="Data_Dictionary", index=False)
        if issues_df is not None:
            issues_df.to_excel(xw, sheet_name="Issue_Log", index=False)
        head_fill = PatternFill("solid", fgColor="D9D9D9")
        for ws in xw.book.worksheets:
            for cell in ws[1]:
                cell.font = Font(bold=True, name="Times New Roman", size=11)
                cell.fill = head_fill
                cell.alignment = Alignment(vertical="center", wrap_text=True)
            for i, col in enumerate(ws.columns, start=1):
                longest = max((len(str(c.value)) for c in col if c.value is not None), default=10)
                ws.column_dimensions[get_column_letter(i)].width = min(max(longest + 2, 10), 60)
                for c in col[1:]:
                    c.alignment = Alignment(vertical="top", wrap_text=True)
                    c.font = Font(name="Times New Roman", size=11)
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
    return path


# -------------------------------- Word --------------------------------------
def write_word(path, info_rows, tables_df, dict_df, issues_df=None, table_pt=10):
    """Write the data dictionary as a Word document in the team format:
    Times New Roman 12 pt, black text, justified paragraphs, 1.5 line spacing.
    (Table cells use `table_pt`, left aligned, so wide tables stay readable.)"""
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    FONT = "Times New Roman"
    doc = Document()

    # ---- page: A4 landscape -------------------------------------------------
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(2.0)

    # ---- styles ---------------------------------------------------------------
    def style_font(style, size, bold=False):
        style.font.name = FONT
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.italic = False
        style.font.color.rgb = RGBColor(0, 0, 0)
        rpr = style.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            rfonts.attrib.pop(qn(attr), None)
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), FONT)

    normal = doc.styles["Normal"]
    style_font(normal, 12)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    for name, size in (("Title", 22), ("Heading 1", 16), ("Heading 2", 13)):
        st = doc.styles[name]
        style_font(st, size, bold=True)
        st.paragraph_format.alignment = (WD_ALIGN_PARAGRAPH.CENTER if name == "Title"
                                         else WD_ALIGN_PARAGRAPH.LEFT)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.space_before = Pt(12)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = 1.15
        # remove the blue bottom border that the Title style carries
        ppr = st.element.get_or_add_pPr()
        for b in ppr.findall(qn("w:pBdr")):
            ppr.remove(b)

    # ---- helpers --------------------------------------------------------------
    def shade(cell, fill="D9D9D9"):
        tcpr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fill)
        tcpr.append(shd)

    def cell_text(cell, text, bold=False):
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run("" if text is None or (isinstance(text, float) and pd.isna(text)) else str(text))
        run.font.size = Pt(table_pt)
        run.bold = bold

    def add_table(df, widths_cm):
        t = doc.add_table(rows=1, cols=len(df.columns))
        t.style = "Table Grid"
        t.autofit = False
        for i, name in enumerate(df.columns):
            cell_text(t.rows[0].cells[i], name, bold=True)
            shade(t.rows[0].cells[i])
        trpr = t.rows[0]._tr.get_or_add_trPr()          # repeat header on each page
        hdr = OxmlElement("w:tblHeader")
        hdr.set(qn("w:val"), "true")
        trpr.append(hdr)
        for _, r in df.iterrows():
            cells = t.add_row().cells
            for i, v in enumerate(r):
                cell_text(cells[i], v)
        for row in t.rows:
            for i, w in enumerate(widths_cm):
                row.cells[i].width = Cm(w)
        for i, w in enumerate(widths_cm):
            t.columns[i].width = Cm(w)
        doc.add_paragraph()
        return t

    def para(text):
        return doc.add_paragraph(text)

    # ---- footer with page number ------------------------------------------------
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run("Heavy Supplier, Inventory & Warehouse Analytics - Data Dictionary - Page ")
    run.font.size = Pt(10)
    r2 = fp.add_run()
    r2.font.size = Pt(10)
    for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        r2._r.append(el)

    # ---- content ----------------------------------------------------------------
    doc.add_paragraph("Data Dictionary", style="Title")
    doc.add_paragraph("Heavy Supplier, Inventory & Warehouse Analytics", style="Title")
    add_table(pd.DataFrame(info_rows, columns=["Item", "Detail"]), [6.0, 19.7])

    doc.add_heading("1. Purpose", level=1)
    para("This document defines every field used in the project: the 12 raw tables, the columns "
         "added by the Week 2 cleaning layer, the star schema (5 dimensions and 4 facts) and the "
         "feature tables built in Week 3. It lets any team member or reviewer see what a field "
         "means, where it comes from, what values it holds and which data-quality issues affect it.")

    doc.add_heading("2. How to read this dictionary", level=1)
    para("Each field row shows the column name, its data type, a definition, the allowed values "
         "(for labels) or the observed range (for numbers and dates), the number of empty values "
         "and any known quality note. Values, ranges and null counts were measured from the "
         "database when this document was generated.")
    para("The status of a definition is one of: Verified (the field was checked in the Week 1-2 "
         "profiling and reconciliation); Inferred (the meaning is taken from the column name and "
         "must be confirmed against the official Fields Documentation, which was not available); "
         "Defined in the Week 2 cleaning or the Week 3 build (the field was created by this project). "
         "The status of every field is given in the Excel version of this dictionary.")

    doc.add_heading("3. Layers and tables", level=1)
    add_table(tables_df[["layer", "table", "description", "rows", "columns"]]
              .rename(columns={"layer": "Layer", "table": "Table", "description": "Description",
                               "rows": "Rows", "columns": "Columns"}),
              [2.6, 5.2, 14.0, 2.0, 1.9])

    def field_table(df):
        out = pd.DataFrame({
            "Column": df["column"], "Type": df["data_type"], "Definition": df["definition"],
            "Values / range": df["values_or_range"], "Nulls": df["null_count"],
            "Notes": df["quality_notes"]})
        add_table(out, [4.0, 2.2, 8.6, 4.8, 1.4, 4.7])

    def section_for(title, layer_names, only_defined=False):
        part = dict_df[dict_df["layer"].isin(layer_names)]
        for tname, g in part.groupby("table", sort=False):
            doc.add_heading(tname, level=2)
            desc = tables_df.loc[tables_df["table"] == tname, "description"]
            if len(desc):
                para(str(desc.iloc[0]))
            if only_defined and bool(g["inherited"].any()):
                g = g[~g["inherited"].astype(bool)]
                para("Columns copied unchanged from the source table are not repeated here; "
                     "see the source table in section 4.")
            field_table(g)

    doc.add_heading("4. Raw and cleaned tables", level=1)
    para("Columns marked [Clean layer] in the Notes column were added or changed by the Week 2 "
         "cleaning pipeline. All other columns are as received.")
    raw = dict_df[dict_df["layer"].isin(["Raw", "Clean"])].copy()
    raw["quality_notes"] = [("[Clean layer] " + (n or "")).strip() if l == "Clean" else n
                            for l, n in zip(raw["layer"], raw["quality_notes"])]
    for tname, g in raw.groupby("table", sort=False):
        doc.add_heading(tname, level=2)
        desc = tables_df.loc[(tables_df["table"] == tname) & (tables_df["layer"] == "Raw"), "description"]
        if len(desc):
            para(str(desc.iloc[0]))
        field_table(g)

    doc.add_heading("5. Star schema (schema star)", level=1)
    para("Facts hold the measurable events; dimensions describe who, what, where and when. "
         "Natural keys are used. Dates are stored as integer keys (YYYYMMDD) joining to dim_date.")
    section_for("star", ["Star"], only_defined=True)

    doc.add_heading("6. Feature tables (schema feat)", level=1)
    para("Derived measures built in Week 3 for KPIs, segmentation, forecasting and optimisation.")
    section_for("feat", ["Feature"])

    if issues_df is not None and len(issues_df):
        doc.add_heading("Appendix A. Data-quality decisions (Week 2 issue log)", level=1)
        para("Each issue found in Week 2 has one decision: FIX (corrected in the clean layer), "
             "FLAG (kept and marked, needs a business answer), ACCEPT (valid or explainable) or "
             "EXCLUDE (kept but left out of specific analyses through a flag column).")
        keep = [c for c in ["Issue_ID", "Table_or_Column", "Severity", "Issue", "Decision"]
                if c in issues_df.columns]
        add_table(issues_df[keep], [1.8, 6.5, 2.0, 11.4, 2.5][:len(keep)])

    doc.save(path)
    return path
