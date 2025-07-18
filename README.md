# MyMCMB AI Command Center

This Streamlit app generates refinance analyses and personalized outreach templates for mortgage professionals.

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

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys and Secrets
Create a `.streamlit/secrets.toml` file in your project directory with your API keys:

```toml
GEMINI_API_KEY = "your-google-gemini-api-key-here"
APP_PASSWORD = "your-admin-password-here"
```

**Getting a Gemini API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in your secrets.toml file

### 3. Test Your Setup
Run these commands to verify everything is working:
```bash
python -m py_compile app.py
streamlit run app.py
```

## Running the Application

### Start the Streamlit App
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Using the Application

1. **Admin Rate Panel**: Set current mortgage rates (requires admin password)
2. **Refinance Intelligence Center**: Upload Excel files and generate AI outreach plans
3. **Other Tools**: Additional AI agents (under development)

## Features

### Refinance Intelligence Center
- Upload Excel files with borrower data
- Automatically maps common column name variations
- Calculates refinance scenarios across multiple loan terms
- Generates personalized AI outreach templates (SMS & Email)
- Exports detailed Excel reports with formatting
- Creates individual PDF summaries for each borrower
- Configurable home appreciation rates

### Supported Loan Products
- 30-Year Fixed
- 25-Year Fixed  
- 20-Year Fixed
- 15-Year Fixed
- 10-Year Fixed
- 7/1 ARM
- 5/1 ARM
- HELOC (interest-only payments)

### AI-Generated Outreach Options
1. **Significant Savings Alert** - Focus on monthly payment reduction
2. **Aggressive Payoff Plan** - Emphasize faster loan payoff
3. **Leverage Your Equity** - Highlight cash-out opportunities
4. **Cash with No Payment Shock** - Same payment with cash out

## Troubleshooting

### Common Issues

**"CRITICAL ERROR: API Keys or App Password are not configured"**
- Ensure `.streamlit/secrets.toml` exists in your project directory
- Verify the file contains valid `GEMINI_API_KEY` and `APP_PASSWORD` entries
- Check file formatting matches TOML syntax

**"Missing required columns after header normalization"**
- Review the required columns table above
- Ensure your Excel file contains all required fields
- Column names are case-insensitive and support common variations

**AI content generation failures**
- Check your Gemini API key is valid and has quota remaining
- Verify internet connectivity
- The app will continue processing other borrowers if one fails

### Excel File Requirements
- Must be .xlsx format (Excel 2007+)
- First row should contain column headers
- Required columns must be present (see table above)
- Dates should be in recognizable format (MM/DD/YYYY recommended)
- Currency values can include $ symbols and commas

## Development

### File Structure
```
MyMCMB-AI-Center/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .streamlit/           # Streamlit configuration
│   └── secrets.toml      # API keys (create this)
├── LICENSE              # MIT license
└── .devcontainer/       # Development container config
```

### Dependencies
- streamlit - Web framework
- pandas - Data manipulation
- openpyxl - Excel file handling
- google-generativeai - AI content generation
- fpdf2 - PDF generation

## License

This project is licensed under the MIT License - see the LICENSE file for details.