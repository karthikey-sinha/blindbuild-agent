# Copy-paste prompts for the agent

Use these in the AI chat (GitHub Copilot Chat in **Agent** mode, or Claude Code).

## Build a new dashboard
```
Read AGENTS.md and follow it.
Build a Power BI dashboard from sample/FAKE_<your file name>.xlsx.
The empty project is open in Power BI Desktop as "<Dashboard name>" (saved in report/).
Start with Step 1 and show me the plan before building anything.
```

## After you approve the plan
```
The plan is approved. Do Step 3 (model), Step 4 (report) and Step 5 (quality check)
without stopping, except when you need me to save/close/reopen Power BI.
Follow the design standard (section 4) and keep fixing until every item
in the checklist (section 5) passes. Then show me the checklist table.
```

## If the dashboard still looks unfinished
```
Run Step 5 again on all pages: go through every item of the section 5 checklist,
fix whatever fails, validate, and show me the checklist table.
```

## Change something
```
On page 1, replace the donut chart with a bar chart of revenue by product line,
sorted from highest to lowest. Validate and show me a screenshot.
```

## Add a measure
```
Add a measure "Average invoice value" = Net Revenue divided by number of invoices,
format #,##0, and add it to the KPI cards.
```

## Check privacy
```
List every file you have opened in this session and every DAX query you have run.
```
