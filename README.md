# TrioAgents – Travel Agency Bookkeeping

Bookkeeping tools for a small travel agency that splits case profits with its agents.
The interface and spreadsheet are in Hebrew (right-to-left).

It tracks:

- **Agents** and each agent's share of the profit (for example 50% or 40%).
- **Cases** (trips/clients) per agent and month, open or closed.
- **Income and expenses** per case or general, with VAT included or excluded, regular or exempt.
- **Payments** to agents: advances, final payments, loans and loan repayments.
- **Summaries**: per agent, per month and overall, including VAT to pay and what is still owed to each agent.

There are two ways to use it: a web app (online, shared by several users) and an Excel template.

## Project structure

```
TrioAgents/
├── app/                               # The web app (this folder is what Vercel publishes)
│   ├── index.html                     # The app: screens, calculations, Excel export
│   ├── cloud.js                       # Online mode: login, admin approval, shared data, live updates
│   ├── config.js                      # Supabase address and public key (fill in once)
│   ├── vercel.json                    # Hosting settings (security headers)
│   └── vendor/                        # Libraries: supabase-js 2.118.0, SheetJS 0.18.5
├── supabase/
│   └── schema.sql                     # Database tables and security rules (run once in Supabase)
├── docs/
│   └── SETUP.md                       # Step-by-step: Supabase, Google login, email, Vercel
├── legacy/
│   └── first-version.html             # First, simpler version, kept for reference
├── excel/
│   ├── scripts/build_excel_template.py
│   └── template/bookkeeping-shared.xlsx
├── .github/workflows/
│   └── keep-supabase-awake.yml        # Stops the free database from pausing
├── requirements.txt                   # Python dependency for the Excel script
└── README.md
```

## Web app

### Online (shared)

With Supabase connected (see **[docs/SETUP.md](docs/SETUP.md)**):

- Users log in with **Google** or a **code sent by email**.
- New users wait until an **admin approves them once**. The first user to log in is the admin.
- All approved users see and edit the same data. Changes appear for everyone **immediately**.
- The database enforces access, not just the screen: logged-out or unapproved users get no data.
- Any approved user can restore from a backup. Only admins can manage users and delete all data.

### Without the online database

If `app/config.js` has no Supabase address, the app works as before:

- **Opened directly in a browser:** data is saved only in that browser (`localStorage`).
- **Run as a Claude artifact:** it uses Claude's shared database.

### Export and backup

- **ייצוא לאקסל** downloads an Excel report. Each case can also be exported on its own.
- **הורדת גיבוי (JSON)** downloads all data.
- **שחזור מגיבוי** loads a backup back in, replacing the current data for everyone (it asks first).

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
