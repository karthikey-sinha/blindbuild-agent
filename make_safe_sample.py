"""Make a SAFE FAKE copy of a company Excel/CSV file for the AI agent to build with.

    python tools/make_safe_sample.py "C:\\CompanyData\\REVENUE_AS_ON_16TH_NOV_2026.xlsx"

What it does (all on your computer, nothing is sent anywhere):
  - keeps every sheet, every column name and the column types, so the agent can design the dashboard
  - replaces names of customers, people, codes and IDs with fake ones ("Customer 001", "ID-0001")
  - replaces every amount with a random number of a similar size
  - keeps short code lists the dashboard logic depends on (e.g. INVOICE / CREDIT NOTE, INR / USD),
    unless the column looks like people or companies
  - keeps dates (or shifts them with --shift-days)

Writes  sample/FAKE_<file name>.xlsx  and prints what it kept and what it replaced.
"""
import argparse
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# columns that usually hold names of people or companies, contact details, or free text
SENSITIVE = re.compile(r"customer|client|organi[sz]ation|\borg\b|supplier|vendor|consignee|shipper|buyer|seller|"
                       r"employee|person|\bsales\b|salesman|salesperson|executive|manager|contact|email|phone|mobile|"
                       r"address|account no|a/c no|bank|gstin|\bpan\b|remark|\bref\b|ref no|narration|description|"
                       r"party|agent|team|owner|staff|user", re.I)
# columns that hold identifiers (voucher numbers, job numbers, codes)
ID_LIKE = re.compile(r"\bno\.?$|\bno\b|\bnumber\b|\bid\b|\bcode\b|\bref\b|\bawb\b|\bbl\b", re.I)
KEEP_MAX_DISTINCT = 12


def find_header_row(raw: pd.DataFrame) -> int:
    """First row with at least 2 text cells: works for normal sheets and pivot-style sheets."""
    for i in range(min(len(raw), 20)):
        cells = [c for c in raw.iloc[i].tolist() if isinstance(c, str) and c.strip()]
        if len(cells) >= 2:
            return i
    return 0


def fake_number(v, rng, scale=1.0):
    if pd.isna(v):
        return v
    v = float(v)
    if v == 0:
        return 0
    out = abs(v) * rng.uniform(0.4, 1.6) * scale
    if abs(v) < 1000:
        out = round(out) if v.is_integer() else round(out, 2)
    else:
        out = round(out, -1)
    return -out if v < 0 else out


def classify(name: str, s: pd.Series) -> str:
    non_null = s.dropna()
    if pd.api.types.is_datetime64_any_dtype(s) or (len(non_null) and non_null.map(lambda x: isinstance(x, datetime)).all()):
        return "date"
    numeric_share = non_null.map(lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)).mean() if len(non_null) else 0
    if ID_LIKE.search(name):
        return "id"
    if SENSITIVE.search(name):
        return "sensitive"
    if numeric_share >= 0.8:
        return "number"
    if non_null.astype(str).nunique() <= KEEP_MAX_DISTINCT:
        return "keep"
    return "text"


def fake_column(name, s, kind, rng, shift_days, scale=1.0):
    if kind == "number":
        nums = pd.to_numeric(s, errors="coerce").abs()
        k = scale if nums.max() >= 1000 else 1.0  # small counts like days keep their size
        return s.map(lambda v: fake_number(v, rng, k) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
    if kind == "date":
        return s if not shift_days else s.map(lambda d: d + timedelta(days=shift_days) if pd.notna(d) else d)
    if kind == "keep":
        return s
    # replace each distinct real value with the same fake value everywhere (keeps counts and grouping)
    label = "ID" if kind == "id" else (re.sub(r"[^A-Za-z]+", " ", name).strip().title() or "Value")
    mapping, n = {}, 0
    def swap(v):
        nonlocal n
        if pd.isna(v) or (isinstance(v, str) and not v.strip()):
            return v
        key = str(v).strip().upper()
        if key in ("GRAND TOTAL", "TOTAL", "SUM OF REVENUE"):
            return v
        if key not in mapping:
            n += 1
            mapping[key] = f"{label}-{n:04d}" if kind == "id" else f"{label} {n:03d}"
        return mapping[key]
    return s.map(swap)


def main():
    ap = argparse.ArgumentParser(description="Create a fake, safe-to-share copy of a data file.")
    ap.add_argument("file", help="the REAL Excel or CSV file (stays where it is)")
    ap.add_argument("--out", default="sample", help="folder for the fake copy (default: sample)")
    ap.add_argument("--shift-days", type=int, default=0, help="also move all dates by this many days")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    src = Path(a.file)
    rng = random.Random(a.seed)
    # one hidden factor for all money columns, so fake totals don't reveal the real size of the business
    scale = random.SystemRandom().choice([rng.uniform(0.3, 0.7), rng.uniform(1.5, 3.0)])
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / f"FAKE_{src.stem}.xlsx"

    if src.suffix.lower() == ".csv":
        sheets = {"Sheet1": pd.read_csv(src, header=None)}
    else:
        sheets = pd.read_excel(src, sheet_name=None, header=None)

    report = []
    with pd.ExcelWriter(dest, engine="openpyxl") as xw:
        for sheet, raw in sheets.items():
            h = find_header_row(raw)
            header = [str(c).strip() if pd.notna(c) else f"Column{i + 1}" for i, c in enumerate(raw.iloc[h].tolist())]
            body = raw.iloc[h + 1:].copy()
            body.columns = header
            body = body.infer_objects()
            for col in header:
                s = body[col]
                if col.startswith("Column") and s.isna().all():
                    continue
                kind = classify(col, s)
                body[col] = fake_column(col, s, kind, rng, a.shift_days, scale)
                report.append((sheet, col, kind))
            top = raw.iloc[:h].copy()
            top = top.map(lambda v: v if not isinstance(v, (int, float)) or pd.isna(v) else None)
            if h:
                top.to_excel(xw, sheet_name=sheet, header=False, index=False)
            body.to_excel(xw, sheet_name=sheet, index=False, startrow=h)

    words = {"keep": "kept (short code list)", "date": "kept (dates)", "number": "FAKE numbers",
             "id": "FAKE ids", "sensitive": "FAKE names", "text": "FAKE text"}
    print(f"Fake copy written: {dest}\n")
    for sheet, col, kind in report:
        print(f"  [{sheet}] {col:28} {words[kind]}")
    print("\nOpen the fake file once and check nothing real is left before giving it to the AI agent.")


if __name__ == "__main__":
    main()
