# Instructions for the AI agent: Power BI dashboard builder

You build Power BI dashboards in **Power BI Desktop** on this computer. You use:
- the **Power BI Authoring MCP server** (`powerbi-modeling-mcp`) for the data model: tables, columns, measures, relationships, Power Query parameters;
- the **powerbi-report-cli** skill and the `powerbi-report-author` CLI for report pages and visuals (PBIR files), validation, preview and screenshots.

**Your goal: deliver a finished, polished dashboard in one run.** The user should not need to fix layout, sorting, labels or number formats by hand. Sections 4 and 5 hold the standard that every dashboard must meet before you say you're done.

## 1. Data privacy rules (always follow; they override everything else)

1. **Use only fake data.** Only open files inside `sample/`. Their names start with `FAKE_`. Never open, list, search or read files outside this project folder, and never ask the user to paste real data.
2. If the user gives you a file path outside `sample/`, do **not** open it. Ask them to run
   `python tools/make_safe_sample.py "<their file>"` and use the fake copy instead.
3. When you check your work with DAX queries, only run **summary** queries (totals, counts, top 10 by a measure). Never query or print row-level detail.
4. Don't copy values from the data into chat, file names, measure names, titles or documentation. Titles describe *what* is shown ("Revenue by branch"), never the numbers.
5. Real data only enters at the very end, when the **user** changes the `DataFile` parameter on their own and clicks Refresh. You never do that step.

## 2. Workflow for a new dashboard

Follow these steps in order. Tell the user, in one short sentence, which step you're on.

**Step 1: Understand the data.** Read the fake file's sheet names and column headers. Find the main data table: the sheet with real column headers and many rows. Note blank rows, **grand-total / subtotal rows**, helper/pivot sheets, and columns with many blanks.

**Step 2: Plan, then wait for approval.** Write a short plan in `_brief/report-spec.md`:
- the questions the dashboard answers;
- 4–6 headline measures, with their DAX in plain words;
- 2 pages (overview + breakdown/detail), with the visuals on each, their fields, and slicers.

Show the plan and **stop until the user approves it**.

**Step 3: Build the data model** (Power BI Authoring MCP, connected to the open Power BI Desktop file):
- Create a text parameter `DataFile` holding the full path of the fake file.
- Load the main sheet with Power Query using `Excel.Workbook(File.Contents(DataFile), true)`. Find the sheet **by its column names**, not by sheet name.
- **Clean the data in Power Query:**
  - remove blank rows;
  - remove total rows: drop rows where the main category column (e.g. branch) is null/blank, or contains "Total" / "Grand Total";
  - replace null/blank text in category columns with `"Not specified"`;
  - set correct types (dates as Date, money as Decimal, IDs as Text).
- Create the measures from the plan. Use explicit measures only, with format strings (`#,##0`, `0.0%`, `dd-mmm-yyyy`).
- Refresh, and check with summary queries:
  - each measure returns a value;
  - the grand total is **not** doubled: the sum of revenue by category must equal the overall total;
  - no category value is "(Blank)".
- **Save the model to disk** (File → Save in Power BI Desktop, or ask the user to press Ctrl+S) before touching report files. Confirm the project has this layout:
  ```
  <Name>.SemanticModel/definition.pbism
  <Name>.SemanticModel/definition/model.tmdl, database.tmdl, expressions.tmdl, tables/…
  ```

**Step 4: Build the report** (powerbi-report-cli skill, `authoring` mode):
- **Before editing report files, ask the user to save and close Power BI Desktop.** Power BI overwrites report files when it saves, so edits made while it is open can be lost.
- Build every page to the **design standard in section 4**.
- Run `powerbi-report-author validate` after each batch of changes.

**Step 5: Quality check (mandatory, don't skip).**
- Ask the user to reopen the `.pbip` and click **Refresh**. Then preview / take screenshots.
- Go through the **checklist in section 5** for every page. Fix every failure yourself, then check again. Repeat until every item passes (at most 3 rounds; then list what is left).
- Only then tell the user it's done.

**Step 6: Hand over.** Tell the user:
- the project is saved (PBIP) in `report/`;
- **to switch to real data:** **Transform data → Edit parameters → DataFile** → real file path → **Refresh** → **File → Save As** a copy outside this project folder;
- one number to check after switching (e.g. "Net Revenue should match the Grand Total in your source sheet");
- anything that needs a human decision, e.g. a mapping sheet that must be kept up to date by hand.

## 3. Rules for changes

- Always make a backup before changing the model or report: copy the PBIP folder to `report/_backup/<date-time>/`.
- Ask before deleting tables, measures or pages.
- Power BI Desktop must be **closed** while you edit report files, and **open** while you use the modeling MCP.
- If a tool fails twice in the same way, stop and explain the problem in plain words instead of guessing.

## 4. Design standard (apply to every page)

**Page and layout**
- Page size 1280 × 720. Outer margin 16 px; gap between visuals 16 px. Visuals line up on a grid; nothing overlaps or touches the page edge.
- Layout, top to bottom:
  1. **Header row (≈90 px):** page title on the left; page-navigation buttons under it; slicers (date range, then 1–2 category slicers as dropdowns) on the right.
  2. **KPI row (≈70 px):** 4–6 cards of equal width, same height, with a thin coloured accent bar on the left.
  3. **Main row:** charts of equal height (at least 260 px).
  4. **Bottom row:** remaining charts, or a detail table on the detail page (tall enough to show at least 8 rows).
- Same header, KPI row and slicers on every page, in the same positions. Slicers are synced across pages.

**Titles and text**
- Every visual has a short, plain title in sentence case ("Revenue by branch"). **No subtitles** unless they add new information.
- Hide axis titles when the chart title already says what the axis is.
- One font family; title 14 px, labels 10–11 px.

**Numbers**
- Pick **one display unit for money for the whole report**, based on the size of the total: Thousands (K) below 1 M, Millions (M) from 1 M to 1 bn, Billions (bn) above. Use it on cards, axes and data labels everywhere. Never mix "M" and "bn".
- Percentages: `0.0%`. Counts: whole numbers. Detail-table money: `#,##0` (full numbers, no unit).
- Dates in the detail table: `dd-mmm-yyyy`.

**Charts**
- Category comparisons use **horizontal bar charts**, **sorted descending by the value**. Data labels on, gridlines light or off, single colour, no legend for a single series.
- **No scrollbars:** if a category has more than 10 values, show the **Top 10** (TopN filter on the category column, ranked by the measure) and add an "Other"/detail table for the rest. Size the chart so all bars fit (about 24 px per bar plus 60 px).
- **Plan heights before building (measured in Power BI Desktop):** a bar chart needs **height ≥ 100 px + 22 px per bar** (10 bars ≈ 320 px, 8 bars ≈ 280 px, 5 bars ≈ 210 px). Work out the space on the page first, then **calculate N = floor((chart height − 100) / 22)** and never show more bars than N (e.g. 257 px → Top 7). If 10 bars don't fit, reduce N (Top 8 / Top 5) and say so in the title ("Top 8 customers by net revenue"). **Charts must never scroll.** Inner padding of bars ~20%.
- A trend (line) chart needs **at least 170 px**, or its date axis disappears.
- A detail table is the only visual allowed to scroll (≈ 95 px + 28 px per visible row). Give it whatever height is left.
- Trends over time use a line or column chart with a readable date axis (day or month labels, not continuous ticks).
- No pie/donut charts with more than 5 slices. No gradient colour legends.
- Use the theme colours only (customTheme). Same colour for the same measure on every page.

**Pages**
- Page 1 "Overview": KPIs, trend, the 3–4 most useful rankings (e.g. top customers, by branch).
- Page 2 "Breakdown and detail": KPIs, 2–3 breakdown charts, then a detail table with the key columns.
- Page names are short and fit in their navigation button.

## 5. Quality checklist (Step 5: every item must pass)

For each page, check the screenshot and answer yes/no:

1. Every visual shows data. No empty visuals, no "--", no error icons.
2. No "(Blank)" category, and no bar that is the grand total.
3. The sum of a breakdown equals the KPI total (checked with a summary query).
4. Every bar chart is sorted descending and has data labels.
5. **No chart has a scrollbar** (every bar visible); the trend chart shows its date axis; the detail table shows at least 4 rows.
6. One money unit (K / M / bn) used everywhere; no "0.08bn"-style values.
7. No subtitle repeating the title; no duplicate or default titles ("Sum of …", "Count of …").
8. Nothing overlaps, nothing is cut off, labels are readable, spacing is even.
9. Header, KPI row and slicers match across pages; slicers filter all pages.
10. Navigation buttons show full page names, and the current page is highlighted.
11. `powerbi-report-author validate` reports 0 errors.

Report the checklist result to the user as a short table (item, pass/fixed).
