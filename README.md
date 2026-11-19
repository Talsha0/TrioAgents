# TrioAgents – Travel Agency Bookkeeping

Bookkeeping tools for a small travel agency that splits case profits with its agents.
The interface and spreadsheet are in Hebrew (right-to-left).

It tracks:

- **Agents** and each agent's share of the profit (for example 50% or 40%).
- **Cases** (trips/clients) per agent and month, open or closed.
- **Income and expenses** per case or general, with VAT included or excluded, regular or exempt.
- **Payments** to agents: advances, final payments, loans and loan repayments.
- **Summaries**: per agent, per month and overall, including VAT to pay and what is still owed to each agent.

There are two ways to use it: a browser app and an Excel template.

## Project structure

```
TrioAgents/
├── app/
│   └── index.html                  # The full browser app (HTML + CSS + JavaScript in one file)
├── legacy/
│   └── first-version.html          # First, simpler version (income/expenses + VAT + 50/50, 60/40 split)
├── excel/
│   ├── scripts/
│   │   └── build_excel_template.py # Generates the Excel template with openpyxl
│   └── template/
│       └── bookkeeping-shared.xlsx # Ready-made Excel template with formulas (example data only)
├── requirements.txt                # Python dependencies for the Excel script
├── .gitignore
├── .gitattributes
├── .editorconfig
└── README.md
```

## Browser app

Open `app/index.html` in any modern browser. No server or install needed.

- It loads the Heebo font from Google Fonts and SheetJS (`xlsx` 0.18.5) from cdnjs, so it needs internet access.
- Data is saved in the browser's `localStorage` (key `agents-books-v1`). It stays on that browser and device only;
  clearing site data deletes it.
- The shared database (several people seeing the same data) and the **Excel download** button use the Claude
  artifact runtime (`window.claude`) and only work when the page runs as a Claude artifact.

`legacy/first-version.html` is the original, simpler version, kept for reference.

## Excel template

`excel/template/bookkeeping-shared.xlsx` can be used as is in Excel or LibreOffice. Sheets:

| Sheet | Purpose |
|---|---|
| סיכום כללי | Overall summary: income, expenses, profit, VAT, agents' share |
| הוראות | Instructions |
| הגדרות | VAT rate, summary year, agents and their profit share |
| תיקים | One row per case |
| תנועות | One row per income or expense |
| תשלומים | One row per payment or loan |
| סיכום סוכנים | Per-agent summary (calculated) |
| סיכום חודשי | Monthly summary (calculated) |

Light-yellow cells are for input; grey headers are calculated columns. Rows marked "דוגמה" are examples
and can be cleared. Room is provided for 300 cases and 2,000 transactions/payments.

### Rebuilding the template

Requires Python 3.9+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python excel/scripts/build_excel_template.py                  # writes excel/template/bookkeeping-shared.xlsx
python excel/scripts/build_excel_template.py -o my-copy.xlsx  # or choose another path
```

## Notes

- Profit is calculated before VAT. VAT to pay = output VAT minus input VAT.
- The default VAT rate is 18%. Check it is current before use.
- This is not a replacement for an accountant. Confirm VAT classification for specific transactions with one.
- Don't commit spreadsheets or exports that contain real client data. `exports/` and `*.local.xlsx` are git-ignored for that.
