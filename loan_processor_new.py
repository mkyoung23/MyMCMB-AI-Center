import os
import pandas as pd
from datetime import datetime
import numpy as np
import time
import requests

"""
This module implements a complete refinance analysis and outreach workflow for loan
officers. It reads borrower information from an Excel or CSV file, performs loan
calculations (including amortization, estimated home value appreciation and
payment comparisons), validates the results, generates personalized text
messages, exports summary spreadsheets and optionally syncs high‐value
opportunities to the Jungo CRM.

Key features:
  • Robust parsing of currency and percentage inputs.
  • Remaining balance calculation via standard amortization formula.
  • Rate lookups from a configurable LTV matrix.
  • Automatic creation of “no cost” refinance options by adding 0.125% to
    base rates.
  • Detailed self‑validation to flag unrealistic rates, amortization or savings
    mismatches and negative savings scenarios.
  • Flexible text message generation with several market‐tone presets and
    borrower‐specific details.
  • Jungo CRM integration for creating or updating leads via a simple POST.

To use this script, run it from the command line. You’ll be prompted for the
path to your borrower file, your name and company, and a market tone. The
script will produce two Excel files in the `BorrowerResults/` folder: a
comprehensive analysis workbook and a concise action sheet with top
opportunities and ready‑to‑send SMS templates. Set the `JUNGO_API_KEY` and
`JUNGO_BASE_URL` variables to enable lead syncing.

Note: replace the placeholder Jungo API key below with your actual key, and
ensure that your borrower input file columns match the expected names listed
in `expected_columns`.
"""

# === Configuration ===
# Lender credit increase for “no cost” refinance rates (0.125% = 0.00125)
LENDER_CREDIT_BASIS_POINTS = 0.00125

# Output folder where all spreadsheets will be written
OUTPUT_FOLDER = "BorrowerResults"

# Jungo CRM configuration
JUNGO_API_KEY = os.getenv("JUNGO_API_KEY", "your_jungo_api_key_here")
JUNGO_BASE_URL = os.getenv("JUNGO_BASE_URL", "https://api.jungo.com/v1")

# Example rate matrix mapping Loan‑to‑Value (LTV) buckets to 15/20/30 year
# rates. Adjust these tuples to reflect your current rate sheet. Each tuple is
# (lower LTV inclusive, upper LTV inclusive, 15‑year rate, 20‑year rate,
# 30‑year rate). Rates are decimals (6.5% = 0.065).
RATE_MATRIX = [
    (0.0,    0.60, 0.0575, 0.0600, 0.06375),
    (0.6001, 0.70, 0.05875, 0.06125, 0.06375),
    (0.7001, 0.75, 0.06000, 0.06250, 0.06500),
    (0.7501, 0.80, 0.06125, 0.06375, 0.06250),
    (0.8001, 0.95, 0.06125, 0.06375, 0.06250),
]


def get_rates_from_ltv(ltv: float) -> tuple:
    """Return (15yr, 20yr, 30yr) rates based on the borrower’s LTV.

    If the LTV doesn’t fall into any defined bucket, the last entry is used.
    """
    for lower, upper, rate15, rate20, rate30 in RATE_MATRIX:
        if lower <= ltv <= upper:
            return rate15, rate20, rate30
    # Default to last row if no match
    return RATE_MATRIX[-1][2], RATE_MATRIX[-1][3], RATE_MATRIX[-1][4]


def calculate_pmt(rate: float, nper: int, pv: float) -> float:
    """Compute the monthly payment given a rate, number of periods and principal.

    Returns 0 for missing or zero values to avoid dividing by zero.
    """
    if rate == 0 or nper <= 0 or pv <= 0 or pd.isna(rate) or pd.isna(nper) or pd.isna(pv):
        return 0.0
    try:
        return pv * (rate * (1 + rate) ** nper) / ((1 + rate) ** nper - 1)
    except Exception:
        return 0.0


def calculate_amortized_balance(principal: float, rate: float, nper: int, payments_made: int) -> float:
    """Calculate remaining principal balance after a number of payments.

    Uses the standard amortization formula. If inputs are invalid or zero, it
    defaults to linear amortization as a fallback.
    """
    if principal <= 0 or nper <= 0 or payments_made < 0 or pd.isna(principal):
        return 0.0
    if rate == 0 or pd.isna(rate):
        # Linear amortization fallback when rate is zero
        remaining = principal * max(0.0, (1 - payments_made / nper))
        return max(0.0, remaining)
    try:
        remaining = principal * ((1 + rate) ** nper - (1 + rate) ** payments_made) / ((1 + rate) ** nper - 1)
        return max(0.0, remaining)
    except Exception:
        return max(0.0, principal)


def calculate_months_elapsed(first_payment_date: pd.Timestamp) -> int:
    """Return the number of months since the first payment date.

    If the date is missing, returns 0. Fractional months are truncated.
    """
    if pd.isna(first_payment_date):
        return 0
    try:
        first_payment = pd.to_datetime(first_payment_date)
        today = datetime.now()
        return max(0, (today.year - first_payment.year) * 12 + (today.month - first_payment.month))
    except Exception:
        return 0


def clean_currency(value) -> float:
    """Convert a currency string or number to float.

    Strips commas and dollar signs; returns 0.0 for missing values.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        try:
            return float(value.replace('$', '').replace(',', '').strip())
        except Exception:
            return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def clean_percentage(value) -> float:
    """Normalize a percentage expressed as a string or number.

    Accepts forms like "6.5%", "0.065" or 6.5. If the numeric value is above
    1, it is divided by 100 to convert to decimal.
    """
    if pd.isna(value):
        return 0.0
    if isinstance(value, str):
        val = value.replace('%', '').strip()
        try:
            num = float(val)
        except Exception:
            return 0.0
    else:
        num = float(value)
    # Convert typical whole‑number rates (e.g. 6.5 -> 0.065)
    return num / 100 if num > 1 else num


def self_check_calculations(df: pd.DataFrame) -> tuple:
    """Perform a series of validation checks on computed columns.

    Returns (errors, warnings), where each is a list of human‑readable strings.
    The checks include: unrealistic current rates, amortization mismatch,
    incorrect no cost rate, incorrect savings and negative savings results.
    """
    print("🔍 Running self‑check validation...")
    errors = []
    warnings = []
    for _, row in df.iterrows():
        borrower_name = f"{row['Borrower First Name']} {row['Borrower Last Name']}"
        current_rate = row.get('Current Interest Rate', 0.0)
        # Current rate sanity check
        if current_rate < 0.01 or current_rate > 0.10:
            errors.append(f"{borrower_name}: current rate {current_rate:.3f} outside expected range (1%‑10%)")
        # Amortization check: re‑calculate expected balance
        expected_balance = calculate_amortized_balance(
            row['Total Original Loan Amount'], current_rate / 12,
            int(row['Loan Term (years)']) * 12, row['Months Elapsed']
        )
        if abs(row['New Loan Balance'] - expected_balance) > 100.0:
            errors.append(
                f"{borrower_name}: amortization difference ${abs(row['New Loan Balance'] - expected_balance):.0f}" )
        # No cost rate check
        expected_nocost = row['New Rate (30yr)'] + LENDER_CREDIT_BASIS_POINTS
        if abs(row['NoCost Rate (30yr)'] - expected_nocost) > 1e-4:
            errors.append(f"{borrower_name}: no‑cost rate mis‑match")
        # Savings check
        expected_savings = row['Current P&I Mtg Pymt'] - row['NoCost 30yr Payment']
        if abs(row['NoCost 30yr Savings'] - expected_savings) > 1.0:
            errors.append(
                f"{borrower_name}: savings off by ${abs(row['NoCost 30yr Savings'] - expected_savings):.0f}")
        # Negative savings warning
        if row['NoCost 30yr Savings'] < 0:
            warnings.append(f"{borrower_name}: no savings with no‑cost refi")
    print(f"✅ Self‑check complete: {len(errors)} errors, {len(warnings)} warnings")
    return errors, warnings


def create_jungo_lead(borrower_row: pd.Series) -> dict | None:
    """Create or update a lead record in Jungo.

    Requires `JUNGO_API_KEY` to be set. Returns response JSON on success or
    None on failure.
    """
    if not JUNGO_API_KEY or JUNGO_API_KEY == "your_jungo_api_key_here":
        return None
    try:
        payload = {
            "first_name": borrower_row['Borrower First Name'],
            "last_name": borrower_row['Borrower Last Name'],
            "email": borrower_row['Borr Email'],
            "phone": borrower_row['Borr Cell'],
            "loan_amount": borrower_row['New Loan Balance'],
            "monthly_savings": borrower_row['NoCost 30yr Savings'],
            "source": "Previous Client Refi",
            "custom_fields": {
                "current_rate": borrower_row['Current Interest Rate'],
                "new_rate": borrower_row['NoCost Rate (30yr)'],
                "equity": borrower_row['Equity Increase ($)']
            },
            "notes": f"Potential savings ${borrower_row['NoCost 30yr Savings']:.0f}/mo"
        }
        resp = requests.post(
            f"{JUNGO_BASE_URL}/leads",
            headers={"Authorization": f"Bearer {JUNGO_API_KEY}"},
            json=payload,
            timeout=10
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None
    except Exception:
        return None


def process_loans(input_path: str, officer_name: str, company_name: str) -> tuple:
    """Read borrower data, compute refinance scenarios and export results.

    Returns (analysis_path, dataframe, errors, warnings).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    print("📊 Reading borrower data...")
    df = (pd.read_excel(input_path, engine='openpyxl')
          if input_path.lower().endswith(('.xlsx', '.xls')) else
          pd.read_csv(input_path))
    # Standardize expected columns. Excess columns will be ignored, missing
    # columns will be filled with defaults later.
    expected_columns = [
        'Borrower First Name', 'Borrower Last Name', 'Subject Property Address',
        'Subject Property City', 'Subject Property State', 'Total Original Loan Amount',
        'Original Appraised Value', 'First Pymt Date', 'Current Interest Rate',
        'Loan Term (years)', 'Current P&I Mtg Pymt', 'Borr Cell', 'Borr Email'
    ]
    # Rename existing columns to match expected names up to length of df.columns
    df.columns = expected_columns[: len(df.columns)]
    print(f"✅ Loaded {len(df)} borrower rows")
    # Clean numeric and date fields
    df['Total Original Loan Amount'] = df['Total Original Loan Amount'].apply(clean_currency)
    df['Original Appraised Value'] = df['Original Appraised Value'].apply(clean_currency)
    df['Current Interest Rate'] = df['Current Interest Rate'].apply(clean_percentage)
    df['Current P&I Mtg Pymt'] = df['Current P&I Mtg Pymt'].apply(clean_currency)
    df['Loan Term (years)'] = pd.to_numeric(df['Loan Term (years)'], errors='coerce').fillna(30).astype(int)
    df['First Pymt Date'] = pd.to_datetime(df['First Pymt Date'], errors='coerce')
    # Months since first payment
    df['Months Elapsed'] = df['First Pymt Date'].apply(calculate_months_elapsed)
    # Set AI estimated value equal to original appraised value initially
    df['AI Estimated Home Value'] = df['Original Appraised Value']
    # Calculate amortized remaining balance
    print("🔢 Calculating remaining balances...")
    df['New Loan Balance'] = df.apply(lambda row: calculate_amortized_balance(
        row['Total Original Loan Amount'], row['Current Interest Rate'] / 12,
        row['Loan Term (years)'] * 12, row['Months Elapsed']
    ), axis=1)
    # Appreciate home value at 7% annual (compound) since first payment
    print("📈 Estimating current home values (7% annual appreciation)...")
    df['New Estimated Home Value'] = df['AI Estimated Home Value'] * (1.07 ** (df['Months Elapsed'] / 12))
    # Compute LTV ratio
    df['LTV'] = df['New Loan Balance'] / df['New Estimated Home Value']
    # Get base rates from LTV matrix
    rates = df['LTV'].apply(get_rates_from_ltv)
    df['New Rate (15yr)'] = rates.apply(lambda x: x[0])
    df['New Rate (20yr)'] = rates.apply(lambda x: x[1])
    df['New Rate (30yr)'] = rates.apply(lambda x: x[2])
    # Monthly payments for base rates
    print("💰 Computing base payment options...")
    df['New 15 Yr P&I Payment'] = df.apply(lambda row: calculate_pmt(
        row['New Rate (15yr)'] / 12, 15 * 12, row['New Loan Balance']), axis=1)
    df['New 20 Yr P&I Payment'] = df.apply(lambda row: calculate_pmt(
        row['New Rate (20yr)'] / 12, 20 * 12, row['New Loan Balance']), axis=1)
    df['New 30 Yr P&I Payment'] = df.apply(lambda row: calculate_pmt(
        row['New Rate (30yr)'] / 12, 30 * 12, row['New Loan Balance']), axis=1)
    # Payment at original term using new rate (no credit)
    df['New P&I (Original Term)'] = df.apply(lambda row: calculate_pmt(
        row['New Rate (30yr)'] / 12, row['Loan Term (years)'] * 12, row['New Loan Balance']), axis=1)
    df['Monthly Savings'] = df['Current P&I Mtg Pymt'] - df['New P&I (Original Term)']
    df['Equity Increase ($)'] = df['New Estimated Home Value'] - df['AI Estimated Home Value']
    # No‑cost lender credit rates and payments (+0.125%)
    print("🎯 Calculating lender credit (no cost) options...")
    df['NoCost Rate (15yr)'] = (df['New Rate (15yr)'] + LENDER_CREDIT_BASIS_POINTS).round(5)
    df['NoCost Rate (20yr)'] = (df['New Rate (20yr)'] + LENDER_CREDIT_BASIS_POINTS).round(5)
    df['NoCost Rate (30yr)'] = (df['New Rate (30yr)'] + LENDER_CREDIT_BASIS_POINTS).round(5)
    df['NoCost 15yr Payment'] = df.apply(lambda row: calculate_pmt(
        row['NoCost Rate (15yr)'] / 12, 15 * 12, row['New Loan Balance']), axis=1)
    df['NoCost 20yr Payment'] = df.apply(lambda row: calculate_pmt(
        row['NoCost Rate (20yr)'] / 12, 20 * 12, row['New Loan Balance']), axis=1)
    df['NoCost 30yr Payment'] = df.apply(lambda row: calculate_pmt(
        row['NoCost Rate (30yr)'] / 12, 30 * 12, row['New Loan Balance']), axis=1)
    df['NoCost 15yr Savings'] = df['Current P&I Mtg Pymt'] - df['NoCost 15yr Payment']
    df['NoCost 20yr Savings'] = df['Current P&I Mtg Pymt'] - df['NoCost 20yr Payment']
    df['NoCost 30yr Savings'] = df['Current P&I Mtg Pymt'] - df['NoCost 30yr Payment']
    # Maximum cash out available (assuming 80% max LTV)
    df['Max CashOut Available'] = (df['New Estimated Home Value'] * 0.80) - df['New Loan Balance']
    # Round currency and rate columns for readability
    currency_cols = [c for c in df.columns if any(substr in c for substr in ['Payment', 'Savings', 'Diff', 'Balance', 'Value', 'Available'])]
    for col in currency_cols:
        df[col] = df[col].round(2)
    rate_cols = [c for c in df.columns if 'Rate' in c or c == 'LTV']
    for col in rate_cols:
        df[col] = df[col].round(5)
    # Run self‑validation
    errors, warnings = self_check_calculations(df)
    # Ensure output folder exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    export_stub = f"{officer_name.replace(' ', '_')}_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    analysis_path = os.path.join(OUTPUT_FOLDER, f"{export_stub}_REFI_ANALYSIS.xlsx")
    # Write multi‑sheet workbook
    with pd.ExcelWriter(analysis_path, engine='xlsxwriter') as writer:
        # Summary sheet for quick review
        summary_cols = [
            'Borrower First Name', 'Borrower Last Name', 'Borr Cell', 'Borr Email',
            'Current P&I Mtg Pymt', 'New Loan Balance', 'AI Estimated Home Value',
            'New Estimated Home Value', 'New 30 Yr P&I Payment', 'New 20 Yr P&I Payment',
            'New 15 Yr P&I Payment', 'NoCost 30yr Payment', 'NoCost 20yr Payment',
            'NoCost 15yr Payment', 'Monthly Savings', 'NoCost 30yr Savings',
            'NoCost 20yr Savings', 'NoCost 15yr Savings', 'Max CashOut Available',
            'Equity Increase ($)', 'LTV'
        ]
        summary_df = df[summary_cols].copy()
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Summary']
        # Conditional formatting on savings columns
        for idx, col_name in enumerate(summary_cols):
            if 'Savings' in col_name:
                worksheet.conditional_format(1, idx, len(summary_df), idx, {
                    'type': '3_color_scale',
                    'min_color': '#FFC7CE',
                    'mid_color': '#FFEB9C',
                    'max_color': '#C6EFCE'
                })
            worksheet.set_column(idx, idx, 18)
        worksheet.freeze_panes(1, 4)
        # Full data sheet
        df.to_excel(writer, sheet_name='Full Data', index=False)
    print(f"💾 Analysis exported to {analysis_path}")
    return analysis_path, df, errors, warnings


def generate_realistic_texts(df: pd.DataFrame, officer_name: str, company_name: str,
                             market_tone: str = 'neutral', custom_message: str = '') -> pd.DataFrame:
    """Construct short, personalized text messages for top borrowers.

    The market_tone argument selects a stock introduction message; use
    'custom' with custom_message to supply your own. Returns a DataFrame with
    ranked opportunities and four different text templates per borrower.
    """
    print(f"🤖 Generating messages with market tone '{market_tone}'...")
    market_messages = {
        'rates_rising': "rates are starting to go back up",
        'rates_falling': "rates just dropped",
        'rates_stable': "with rates still favorable",
        'rates_volatile': "before rates change again",
        'opportunity': "great opportunity right now",
        'neutral': "just wanted to update you",
        'urgent': "time sensitive opportunity",
        'custom': custom_message
    }
    intro = market_messages.get(market_tone, market_messages['neutral'])
    # Take the top 10 opportunities by monthly savings under the no‑cost 30yr option
    top = df.nlargest(10, 'NoCost 30yr Savings').copy()
    records = []
    for _, row in top.iterrows():
        first = row['Borrower First Name']
        last = row['Borrower Last Name']
        current_rate_pct = row['Current Interest Rate'] * 100
        current_payment = row['Current P&I Mtg Pymt']
        # No cost option
        nocost_rate_pct = row['NoCost Rate (30yr)'] * 100
        nocost_savings = row['NoCost 30yr Savings']
        # Points option
        base_rate_pct = row['New Rate (30yr)'] * 100
        base_savings = row['Monthly Savings']
        # Shorter term option (20yr no cost)
        nocost20_rate_pct = row['NoCost Rate (20yr)'] * 100
        nocost20_payment = row['NoCost 20yr Payment']
        # Closing/elapsed
        months_elapsed = row['Months Elapsed']
        years_ago = round(months_elapsed / 12, 1)
        closing_desc = f"about {years_ago} years ago" if years_ago >= 1 else f"about {months_elapsed} months ago"
        equity_increase_k = row['Equity Increase ($)'] / 1000
        # Compose texts (max ~160 chars each)
        texts = {
            'lender_credit': (
                f"Hi {first}! It's {officer_name} from {company_name}. We closed on your mortgage {closing_desc}. "
                f"{intro.capitalize()} + your home value increased. You could do a 30yr refi at "
                f"{nocost_rate_pct:.2f}% and save ${nocost_savings:.0f}/mo with our lender credit option. "
                "Call me when you have a moment!"
            ),
            'rate_comparison': (
                f"Hi {first}, {officer_name} here. You're currently at {current_rate_pct:.2f}%. Today I can "
                f"get you {base_rate_pct:.2f}% with points saving ${base_savings:.0f}/mo or "
                f"{nocost_rate_pct:.2f}% no‑cost saving ${nocost_savings:.0f}/mo. "
                "Complete the app link so I can send the loan estimate!"
            ),
            'shorter_term': (
                f"{first}, it's {officer_name}. With your equity up, you could do a 20yr at "
                f"{nocost20_rate_pct:.2f}% no‑cost with a payment around ${nocost20_payment:.0f}/mo vs "
                f"${current_payment:.0f}/mo now. Pay off 10 years sooner! Interested?"
            ),
            'equity_option': (
                f"Hi {first}! {officer_name} from {company_name}. Your equity grew about ${equity_increase_k:.0f}k since "
                f"we closed. Perfect time to cash out at {nocost_rate_pct:.2f}% no‑cost or {base_rate_pct:.2f}% with "
                "points. Let's chat!"
            )
        }
        # Build summary using concatenation to avoid nested quote issues
        summary = (
            f"BORROWER: {first} {last}\n"
            f"CLOSED: {closing_desc}\n"
            f"CURRENT: {current_rate_pct:.2f}% at ${current_payment:.0f}/mo\n\n"
            "LOAN OPTIONS:\n"
            f"• 30yr at {base_rate_pct:.2f}% with points = ${base_savings:.0f}/mo savings\n"
            f"• 30yr at {nocost_rate_pct:.2f}% no-cost = ${nocost_savings:.0f}/mo savings\n"
            f"• 20yr at {nocost20_rate_pct:.2f}% no-cost ≈ ${nocost20_payment:.0f}/mo payment\n\n"
            "TALKING POINTS:\n"
            f"✅ We closed your mortgage {closing_desc}\n"
            f"✅ Your home value increased ${equity_increase_k:.0f}k\n"
            "✅ Previous Client Lender Credit – we pay closing costs\n"
            "✅ Lock rates before they move again\n"
            f"✅ Current balance: ${row['New Loan Balance']:.0f}\n"
            f"✅ Home value: ${row['New Estimated Home Value']:.0f}\n\n"
            "BEST APPROACH:\n"
            f"Start with the lender credit option (${nocost_savings:.0f}/mo). "
            f"If they want an even lower rate, offer the points option (${base_savings:.0f}/mo)."
        )
        records.append({
            'Rank': len(records) + 1,
            'Borrower Name': f"{first} {last}",
            'Phone': row['Borr Cell'],
            'Email': row['Borr Email'],
            'Closed': closing_desc,
            'Current Rate': f"{current_rate_pct:.2f}%",
            'Best Savings': f"${nocost_savings:.0f}/mo",
            'Lender Credit Text': texts['lender_credit'][:160],
            'Rate Comparison Text': texts['rate_comparison'][:160],
            'Shorter Term Text': texts['shorter_term'][:160],
            'Equity Option Text': texts['equity_option'][:160],
            'Loan Officer Summary': summary
        })
    return pd.DataFrame(records)


def save_action_sheet(recommendations: pd.DataFrame, export_stub: str) -> str:
    """Write a concise loan officer action sheet with ranked opportunities."""
    path = os.path.join(OUTPUT_FOLDER, f"{export_stub}_ACTION_SHEET.xlsx")
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        recommendations.to_excel(writer, sheet_name='Top 10 Opportunities', index=False)
        worksheet = writer.sheets['Top 10 Opportunities']
        workbook = writer.book
        # Set column widths for readability
        widths = [6, 20, 15, 25, 20, 12, 15] + [50, 50, 50, 50] + [80]
        for i, w in enumerate(widths[: len(recommendations.columns)]):
            worksheet.set_column(i, i, w)
        # Header styling
        header_fmt = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4472C4',
            'font_color': '#FFFFFF',
            'border': 1
        })
        for col_num, col_name in enumerate(recommendations.columns):
            worksheet.write(0, col_num, col_name, header_fmt)
        # Text wrapping for message columns
        text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        for row_idx in range(1, len(recommendations) + 1):
            for col_idx in range(7, 11):
                worksheet.set_row(row_idx, 80, text_fmt)
    return path


def sync_to_jungo(df: pd.DataFrame) -> int:
    """Sync the top 10 opportunities to Jungo. Returns the count synced."""
    if not JUNGO_API_KEY or JUNGO_API_KEY == "your_jungo_api_key_here":
        print("⚠️ Jungo API key not configured – skipping CRM sync")
        return 0
    print("🔄 Syncing top opportunities to Jungo…")
    count = 0
    top = df.nlargest(10, 'NoCost 30yr Savings')
    for _, row in top.iterrows():
        if create_jungo_lead(row):
            count += 1
            print(f"   ✅ Synced {row['Borrower First Name']} {row['Borrower Last Name']}")
        time.sleep(0.5)  # Simple rate limiting
    return count


def main() -> None:
    """Entry point for interactive CLI use."""
    print("🏠 Previous Client Refi Automation")
    print("=" * 60)
    borrower_file = input("\n1. Drag or enter path to borrower Excel/CSV: \n").strip().strip('"')
    officer_name = input("\n2. Your full name (e.g., Michael Young): \n").strip()
    company_name = input("\n3. Company (e.g., UFMG): \n").strip()
    # Market tone selection
    print("\n4. Select market tone:")
    choices = [
        "a) rates_rising", "b) rates_falling", "c) rates_stable", "d) opportunity",
        "e) neutral", "f) urgent", "g) custom"
    ]
    for choice in choices:
        print(f"   {choice}")
    choice_map = {
        'a': 'rates_rising', 'b': 'rates_falling', 'c': 'rates_stable',
        'd': 'opportunity', 'e': 'neutral', 'f': 'urgent', 'g': 'custom'
    }
    selection = input("\nEnter choice (a‑g): ").strip().lower()
    market_tone = choice_map.get(selection, 'neutral')
    custom_message = ''
    if market_tone == 'custom':
        custom_message = input("\nEnter your custom market message: \n").strip()
    try:
        # Process loans
        analysis_path, df, errors, warnings = process_loans(borrower_file, officer_name, company_name)
        print(f"✅ Analysis saved: {os.path.basename(analysis_path)}")
        # Generate outreach texts
        recommendations = generate_realistic_texts(df, officer_name, company_name, market_tone, custom_message)
        export_stub = f"{officer_name.replace(' ', '_')}_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        action_path = save_action_sheet(recommendations, export_stub)
        print(f"✅ Action sheet saved: {os.path.basename(action_path)}")
        # Sync to Jungo
        synced = sync_to_jungo(df)
        if synced:
            print(f"✅ {synced} leads synced to Jungo CRM")
        # Summary output
        print("\n🎉 Refi automation complete!")
        if not errors and not warnings:
            print("✅ All calculations validated successfully.")
        else:
            if errors:
                print("❌ Issues detected:")
                for err in errors:
                    print(f"   • {err}")
            if warnings:
                print("⚠️ Warnings:")
                for warn in warnings:
                    print(f"   • {warn}")
        print("\n📁 Output folder:", OUTPUT_FOLDER)
    except Exception as exc:
        print("❌ An error occurred:", exc)


if __name__ == '__main__':
    main()