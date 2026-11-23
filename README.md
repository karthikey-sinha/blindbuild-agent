# Power BI Dashboard Agent

An AI agent that builds Power BI dashboards for you, inside **Power BI Desktop on your own computer**, **without ever seeing the company's real data**.

You give it a data file. It plans the dashboard, builds the data model and the pages, checks its own work with screenshots, and fixes what looks wrong. You then switch the dashboard to the real data with one click.

---

## How it works, in plain English

Think of it like an architect and a builder:

- The **AI agent is the architect.** It designs the house: which numbers to show, which charts, where they go.
- It works from a **fake copy** of your data: same columns, same layout, but invented names and numbers.
- **Power BI on your computer is the builder.** When you point the finished dashboard at the real file, Power BI fills in the real numbers itself. The AI is not involved in that step at all.

```
Real file (C:\CompanyData)                     ← never seen by the AI
      │
      │  1. make_safe_sample.py (runs on your PC)
      ▼
FAKE copy (sample\FAKE_....xlsx)               ← the only file the AI uses
      │
      │  2. AI agent in VS Code
      │     ├─ plans the dashboard → you approve
      │     ├─ builds the data model ── Power BI Authoring MCP server
      │     └─ builds the pages ─────── Microsoft report skill + CLI
      │        (validates, takes screenshots, fixes)
      ▼
Dashboard in Power BI Desktop (with fake numbers)
      │
      │  3. YOU: Transform data → Edit parameters → DataFile = real file → Refresh
      ▼
Same dashboard with REAL numbers               ← calculated by Power BI, on your PC
```

---

## What you need

| Item | Why |
|---|---|
| Windows 10/11 | The Power BI connector for agents runs on Windows |
| **Power BI Desktop** (latest) | Where the dashboard is built |
| **VS Code** | Where you chat with the agent |
| **GitHub Copilot** subscription | The AI agent (Agent mode). On a company account, an admin may need to switch on *MCP servers in Copilot* |
| **Node.js LTS** (22 or 24) | Runs Microsoft's report tool |
| **Python 3.10+** | Runs the fake-data tool |

> You can use **Claude Code** instead of GitHub Copilot as the agent. See "Using Claude Code" at the end.

---

## One-time setup (about 20 minutes)

**1. Install the Power BI connector for agents**
In VS Code: **Extensions** → search **"Power BI Authoring MCP"** (by Microsoft) → Install.
Then open **Copilot Chat**, switch to **Agent** mode, click the **tools** icon and make sure **powerbi-modeling-mcp** is ticked.

**2. Install Microsoft's report tool**
```bash
npm install -g @microsoft/powerbi-report-authoring-cli@latest
```

**3. Add Microsoft's report-building skill to this project**
Run this in PowerShell, inside this folder:
```powershell
git clone --depth 1 https://github.com/microsoft/skills-for-fabric.git "$env:TEMP\skills-for-fabric"
Copy-Item -Recurse "$env:TEMP\skills-for-fabric\skills\powerbi-report-cli" ".github\skills\powerbi-report-cli"
```

**4. Install the Python packages**
```bash
pip install -r requirements.txt
```

**5. Keep real data OUTSIDE this project folder**, e.g. `C:\CompanyData\`.
The agent can read anything inside the project folder, so real files must never be put here.

---

## Building a dashboard

**Step 1: Make the fake copy**
```bash
python tools/make_safe_sample.py "C:\CompanyData\<your file>.xlsx"
```
It prints, column by column, what it kept and what it replaced:
- **Replaced:** customer and people names, voucher/job/reference numbers, remarks, and all amounts.
- **Kept:** column names, dates, and short code lists such as INVOICE / CREDIT NOTE or INR / USD, which the formulas need.

Open `sample\FAKE_....xlsx` once and check by eye that nothing real is left.

**Step 2: Start an empty Power BI project**
Open Power BI Desktop → **File → Save as** → type **Power BI project (.pbip)** → save as `report\<Dashboard name>.pbip`. Leave it open.

**Step 3: Ask the agent**
Open this folder in VS Code → start a **new** Copilot Chat in **Agent** mode → paste prompt 1 from `PROMPTS.md` (fill in your file name). When you approve the plan, paste prompt 2.

The agent will:
1. read the fake file's structure;
2. write a plan in `_brief\report-spec.md` and **wait for your OK**;
3. build and clean the data model: remove total and blank rows, fill empty categories with "Not specified" (Power BI asks you to confirm before its first change);
4. build the pages to a fixed design standard: same layout on every page, one number unit (K/M/bn), sorted and labelled bars, Top N sized so no chart scrolls;
5. run an 11-point quality checklist on every page, fix what fails, and show you the checklist table.

> **Your only job while it works:** Power BI must be **open** while the agent builds the data model, and **saved and closed** while it edits the report pages. Otherwise Power BI overwrites the agent's work when it saves. The agent tells you when to close Power BI and when to reopen it. After reopening, click **Refresh**.

**Step 4: Switch to the real data (you do this, not the agent)**
In Power BI Desktop: **Transform data → Edit parameters → DataFile** → paste the path of the real file → OK → **Refresh**.
Then **File → Save As** → save the copy **outside this project folder** (e.g. `C:\CompanyData\`).
Check one total (e.g. net revenue) against the source file to confirm the numbers match.

**Every month after that:** change `DataFile` to the new file (or overwrite the file at the same path) → **Refresh**. You don't need the agent unless you want to change the design.

---

## How your data is protected

| Protection | What it does |
|---|---|
| **Fake copy only** | The agent builds everything from invented data. Real names and numbers never reach the AI. |
| **Real data outside the project** | The agent's workspace contains no real files to open by mistake. |
| **Hidden scale** | Fake amounts are scaled by a hidden random factor, so even totals don't reveal the size of the business. |
| **Rules in `AGENTS.md`** | The agent must not open files outside `sample\`, must run only summary queries, and must never switch to real data itself. |
| **You switch to real data** | The last step happens in Power BI, by you, after the agent has finished. |
| **Confirm before changes** | The Power BI connector asks before its first change to the model. Agent mode in VS Code can also ask before each tool call. |
| **Nothing pushed to Git** | `.gitignore` keeps `sample\`, `report\` and `_brief\` out of the repo. |
| **Business AI plan** | Use the company's GitHub Copilot Business/Enterprise (or Claude business) plan, not a personal free account. |

> After the switch, the **.pbip project and screenshots contain real data**. Don't ask the agent to take new screenshots after switching, and share the project only like any other internal report.

---

## Good to know

- **The rules improve over time.** Every problem I had to fix by hand (double-counted totals, "(Blank)" bars, scrolling charts, mixed M/bn units, repeated subtitles) became a rule or checklist item in `AGENTS.md`, so the agent now gets these right on the first run.

- Microsoft's agent tools for Power BI are **in preview**. Expect the occasional rough edge; the agent is told to stop and explain rather than guess.
- Quality depends on the AI model. Pick a strong reasoning model in the Copilot model menu.
- A hand-kept sheet (like a customer → team list) can't be invented by the AI. The agent will tell you which parts need a human-maintained file.

## Using Claude Code instead of GitHub Copilot
```bash
claude mcp add powerbi-authoring -- npx -y @microsoft/powerbi-modeling-mcp@latest --start
```
Copy the skill to `.claude\skills\powerbi-report-cli` instead of `.github\skills\...`. Claude Code reads `CLAUDE.md`, which points to `AGENTS.md`.

## Files in this kit
```
AGENTS.md                         rules + workflow the agent follows
PROMPTS.md                        ready-to-paste prompts
tools/make_safe_sample.py         makes the fake copy of any Excel/CSV
.github/copilot-instructions.md   points GitHub Copilot to AGENTS.md
CLAUDE.md                         points Claude Code to AGENTS.md
sample/                           fake files go here
report/                           the Power BI project goes here
```
