# MyMCMB AI Command Center

This Streamlit app generates refinance analyses and personalized outreach templates.

## Required Data Columns
The **Refinance Intelligence Center** expects the following columns. Header names are matched case-insensitively and may use any of the listed variations.

| Required Column | Accepted Variations |
|-----------------|--------------------|
| Borrower First Name | borrower first name, first name, fname, first |
| Borrower Last Name | borrower last name, last name, lname, last |
| Current P&I Mtg Pymt | current p&i mtg pymt, current payment, pi payment, current p&i |
| Original Property Value | original property value, purchase price, original home value, home value |
| Total Original Loan Amount | total original loan amount, original loan amount, loan amount, original loan balance |
| Current Interest Rate | current interest rate, interest rate, rate |
| Loan Term (years) | loan term (years), loan term, term |
| First Pymt Date | first pymt date, first payment date, first payment |
| City | city, property city, borrower city |

Run `pip install -r requirements.txt` and `python -m py_compile app.py` to verify the environment.

## Running the App
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `.streamlit/secrets.toml` file containing your `GEMINI_API_KEY` and `APP_PASSWORD`:
   ```toml
   GEMINI_API_KEY = "your-api-key"
   APP_PASSWORD = "your-admin-password"
   ```
3. Launch Streamlit:
   ```bash
   streamlit run app.py
   ```

Navigate to the Refinance Intelligence Center tab, upload your Excel sheet, and click **Generate AI Outreach Plans** to produce downloadable reports and templated messages.

The app automatically maps common column names to the required headers, so you can keep your spreadsheet as-is. The **Assumed Annual Home Appreciation Rate (%)** input defaults to 4.6% and drives the new home value and LTV calculations. Once the AI analysis finishes, you can download a polished Excel workbook with outreach plans plus individual PDF summaries containing personalized outreach templates for each borrower.

## Features
- **Admin Rate Panel**: Set current mortgage rates with admin password protection
- **Refinance Intelligence Center**: Upload borrower data and generate AI-powered outreach plans
- **Column Mapping**: Automatically normalizes common Excel header variations
- **PDF Reports**: Generate individual PDF summaries for each borrower
- **Excel Export**: Download comprehensive reports with all calculations and outreach options
- **AI-Generated Content**: Personalized SMS and email templates for each borrower
- **Multiple Loan Products**: Support for 30yr, 25yr, 20yr, 15yr, 10yr fixed, 7yr ARM, 5yr ARM, and HELOC options

## Testing
```bash
pip install -r requirements.txt
python -m py_compile app.py
```