import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime
import re
import io
from fpdf import FPDF

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MyMCMB AI Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
<style>
    .stApp {
        background-color: #020617; /* Slate 950 */
        color: #e2e8f0; /* Slate 200 */
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #ffffff; 
        font-weight: 700;
    }
    .stButton>button {
        background-color: #2563eb; /* Blue 600 */
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #1d4ed8; /* Blue 700 */
        transform: translateY(-2px);
    }
    .st-expander, .st-emotion-cache-18ni7ap {
        background-color: #0f172a; /* Slate 900 */
        border: 1px solid #1e293b; /* Slate 800 */
        border-radius: 0.5rem;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1e293b; /* Slate 800 */
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# --- API & MODEL SETUP ---
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    APP_PASSWORD = st.secrets.get("APP_PASSWORD")
    if not GEMINI_API_KEY or not APP_PASSWORD:
        st.error("CRITICAL ERROR: API Keys or App Password are not configured. Please ensure they are set in your Streamlit Secrets in the correct TOML format.")
        st.stop()
        
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Could not configure AI models. Error: {e}")
    st.stop()

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("MyMCMB AI Command Center")
app_mode = st.sidebar.selectbox(
    "Select an AI Agent",
    ["Refinance Intelligence Center", "Admin Rate Panel", "Guideline & Product Chatbot", "Social Media Automation"]
)

# --- ROBUST SHARED FUNCTIONS ---
def clean_currency(value):
    if pd.isna(value): return 0.0
    try:
        return float(re.sub(r'[$,]', '', str(value)).strip())
    except (ValueError, TypeError):
        return 0.0

def clean_percentage(value):
    if pd.isna(value): return 0.0
    try:
        val = float(str(value).replace('%', '').strip())
        return val / 100 if val > 1 else val
    except (ValueError, TypeError):
        return 0.0

def calculate_new_pi(principal, annual_rate, term_years):
    try:
        principal = clean_currency(principal)
        annual_rate = clean_percentage(annual_rate)
        term_years = int(term_years)
        monthly_rate = annual_rate / 12
        num_payments = term_years * 12
        if monthly_rate <= 0 or num_payments <= 0: return 0.0
        payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        return round(payment, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def calculate_amortized_balance(principal, annual_rate, term_years, first_payment_date):
    try:
        principal = clean_currency(principal)
        annual_rate = clean_percentage(annual_rate)
        term_years = int(clean_currency(term_years))
        if pd.isna(first_payment_date): return principal
        
        first_payment = pd.to_datetime(first_payment_date)
        months_elapsed = (datetime.now().year - first_payment.year) * 12 + (datetime.now().month - first_payment.month)
        payments_made = max(0, months_elapsed)
        if payments_made == 0: return principal
        
        monthly_rate = annual_rate / 12
        total_payments = term_years * 12
        if monthly_rate <= 0: return principal * (1 - (payments_made / total_payments))
        
        balance = principal * ( ((1 + monthly_rate)**total_payments - (1 + monthly_rate)**payments_made) / ((1 + monthly_rate)**total_payments - 1) )
        return max(0, round(balance, 2))
    except Exception:
        return principal

# --- PDF EXPORT FUNCTION ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'MyMCMB Refinance Opportunity Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 242, 246)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body.encode('latin-1', 'replace').decode('latin-1'))
        self.ln()

def create_pdf_report(data):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"For: {data['Borrower First Name']} {data.get('Borrower Last Name', '')}", 0, 1)
    
    pdf.chapter_title("Financial Snapshot")
    for key, value in data['snapshot'].items():
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(80, 8, f"{key}:", 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, str(value), 1)
        pdf.ln()
    
    pdf.ln(10)
    pdf.chapter_title("AI-Generated Outreach Options")
    if data.get('outreach'):
        for option in data['outreach']:
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, option.get('title', 'N/A'), 0, 1)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "SMS Template:", 0, 1)
            pdf.chapter_body(option.get('sms', 'N/A'))
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Email Template:", 0, 1)
            pdf.chapter_body(option.get('email', 'N/A'))
            pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

# --- ADMIN RATE PANEL ---
if app_mode == "Admin Rate Panel":
    st.title("Admin Rate Panel")
    password = st.text_input("Enter Admin Password", type="password")
    if password == APP_PASSWORD:
        st.success("Access Granted")
        st.write("Set the current mortgage rates. Leave a rate at 0 to disable that option for loan officers.")

        if 'rates' not in st.session_state:
            st.session_state.rates = {
                '30yr_fixed': 6.875, '25yr_fixed': 6.750, '20yr_fixed': 6.625, '15yr_fixed': 6.000, '10yr_fixed': 5.875,
                '7yr_arm': 7.125, '5yr_arm': 7.394, 'heloc': 8.500, 'no_cost_adj': 0.250
            }

        with st.form("rate_form"):
            st.subheader("Current Market Rates (%)")
            rates = st.session_state.rates
            col1, col2 = st.columns(2)
            with col1:
                rates['30yr_fixed'] = st.number_input("30-Year Fixed", value=rates['30yr_fixed'], format="%.3f")
                rates['25yr_fixed'] = st.number_input("25-Year Fixed", value=rates['25yr_fixed'], format="%.3f")
                rates['20yr_fixed'] = st.number_input("20-Year Fixed", value=rates['20yr_fixed'], format="%.3f")
                rates['15yr_fixed'] = st.number_input("15-Year Fixed", value=rates['15yr_fixed'], format="%.3f")
                rates['10yr_fixed'] = st.number_input("10-Year Fixed", value=rates['10yr_fixed'], format="%.3f")
            with col2:
                rates['7yr_arm'] = st.number_input("7/1 ARM", value=rates['7yr_arm'], format="%.3f")
                rates['5yr_arm'] = st.number_input("5/1 ARM", value=rates['5yr_arm'], format="%.3f")
                rates['heloc'] = st.number_input("HELOC Rate", value=rates['heloc'], format="%.3f")
                rates['no_cost_adj'] = st.number_input("No-Cost Adj.", value=rates['no_cost_adj'], format="%.3f", help="Amount to add for a no-cost option.")
            
            submitted = st.form_submit_button("Save Rates")
            if submitted:
                st.session_state.rates = rates
                st.success("Rates updated successfully!")
    elif password:
        st.error("Incorrect Password")

# --- REFINANCE INTELLIGENCE CENTER ---
elif app_mode == "Refinance Intelligence Center":
    st.title("Refinance Intelligence Center")
    st.markdown("### Upload a borrower data sheet to generate hyper-personalized outreach plans.")

    uploaded_file = st.file_uploader("Choose a borrower Excel file", type=['xlsx'])

    if uploaded_file:
        try:
            df_original = pd.read_excel(uploaded_file, engine='openpyxl')
            st.success(f"Successfully loaded {len(df_original)} borrowers from '{uploaded_file.name}'.")

            if st.button("🚀 Generate AI Outreach Plans"):
                with st.spinner("Initiating AI Analysis... This will take a few moments."):
                    df = df_original.copy()
                    rates = st.session_state.get('rates', {'30yr_fixed': 6.875, '20yr_fixed': 6.625, '15yr_fixed': 6.000, '10yr_fixed': 5.875, '25yr_fixed': 6.750, '7yr_arm': 7.125, '5yr_arm': 7.394, 'heloc': 8.500, 'no_cost_adj': 0.250})

                    progress_bar = st.progress(0, text="Calculating financial scenarios...")
                    df['Remaining Balance'] = df.apply(lambda row: calculate_amortized_balance(row.get('Total Original Loan Amount'), row.get('Current Interest Rate'), row.get('Loan Term (years)'), row.get('First Pymt Date')), axis=1)
                    df['Months Since First Payment'] = df['First Pymt Date'].apply(lambda x: max(0, (datetime.now().year - pd.to_datetime(x).year) * 12 + (datetime.now().month - pd.to_datetime(x).month)) if pd.notna(x) else 0)
                    df['Estimated Home Value'] = df.apply(lambda row: round(clean_currency(row.get('Original Property Value', 0)) * (1.046 ** (row['Months Since First Payment'] / 12)), 2), axis=1)
                    df['Estimated LTV'] = (df['Remaining Balance'] / df['Estimated Home Value']).fillna(0).replace([float('inf'), -float('inf')], 0)
                    df['Max Cash-Out Amount'] = (df['Estimated Home Value'] * 0.80) - df['Remaining Balance']
                    df['Max Cash-Out Amount'] = df['Max Cash-Out Amount'].apply(lambda x: max(0, round(x, 2)))
                    
                    for term, rate_key in [('30yr', '30yr_fixed'), ('25yr', '25yr_fixed'), ('20yr', '20yr_fixed'), ('15yr', '15yr_fixed'), ('10yr', '10yr_fixed')]:
                        rate = rates.get(rate_key, 0) / 100
                        if rate > 0:
                            df[f'New P&I ({term})'] = df.apply(lambda row: calculate_new_pi(row['Remaining Balance'], rate, int(term.replace('yr',''))), axis=1)
                            df[f'Savings ({term})'] = df.apply(lambda row: clean_currency(row['Current P&I Mtg Pymt']) - row[f'New P&I ({term})'], axis=1)
                    
                    outreach_results = []
                    for i, row in df.iterrows():
                        progress_bar.progress((i + 1) / len(df), text=f"Generating AI outreach for {row['Borrower First Name']}...")
                        
                        current_payment = clean_currency(row['Current P&I Mtg Pymt'])
                        new_rate = rates.get('30yr_fixed', 0) / 100
                        try:
                            max_loan_for_same_payment = (current_payment * (((1 + new_rate/12)**360) - 1)) / ((new_rate/12) * (1 + new_rate/12)**360) if new_rate > 0 else 0
                            cash_out_same_payment = max(0, max_loan_for_same_payment - row['Remaining Balance'])
                        except (ZeroDivisionError, ValueError):
                            cash_out_same_payment = 0

                        prompt = f"""
                        You are an expert mortgage loan officer assistant for MyMCMB. Your task is to generate a set of personalized, human-sounding outreach messages for a past client named {row['Borrower First Name']}. The tone must be professional, helpful, and sound like it came from a real person.

                        **Borrower's Financial Snapshot:**
                        - Property City: {row.get('City', 'their city')}
                        - Current Monthly P&I: ${clean_currency(row['Current P&I Mtg Pymt']):.2f}
                        - Estimated Home Value: ${row['Estimated Home Value']:.2f}
                        
                        **Calculated Refinance Scenarios:**
                        1.  **30-Year Fixed:** New Payment: ${row.get('New P&I (30yr)', 0):.2f}, Monthly Savings: ${row.get('Savings (30yr)', 0):.2f}
                        2.  **15-Year Fixed:** New Payment: ${row.get('New P&I (15yr)', 0):.2f}, Monthly Savings: ${row.get('Savings (15yr)', 0):.2f}
                        3.  **Max Cash-Out:** You can offer up to ${row['Max Cash-Out Amount']:.2f} in cash.
                        4.  **"Same Payment" Cash-Out:** You can offer approx. ${cash_out_same_payment:.2f} in cash while keeping their payment nearly the same.

                        **Task:**
                        Generate a JSON object with four distinct outreach options. Each option should have a 'title', a concise 'sms' template, and a professional 'email' template.
                        1.  **"Significant Savings Alert"**: Focus on the 30-year option's direct monthly savings.
                        2.  **"Aggressive Payoff Plan"**: Focus on the 15-year option, highlighting owning their home faster.
                        3.  **"Leverage Your Equity"**: Focus on the maximum cash-out option for home improvements or debt consolidation.
                        4.  **"Cash with No Payment Shock"**: Focus on the 'same payment' cash-out option.
                        Make the messages sound authentic. For one of the emails, mention a positive local event or trend in {row.get('City', 'their area')} to personalize it further.
                        """
                        try:
                            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
                            outreach_results.append(json.loads(response.text))
                        except Exception as e:
                            st.warning(f"AI content generation failed for {row['Borrower First Name']}. Error: {e}")
                            outreach_results.append({"outreach_options": []})

                    df['AI_Outreach'] = outreach_results
                    st.session_state.df_results = df
                    st.success("Analysis complete! View the outreach plans below.")

        except Exception as e:
            st.error(f"An error occurred while processing the file. Please check your Excel sheet for correct column names and data types. Error: {e}")

        if 'df_results' in st.session_state:
            st.markdown("---")
            st.header("Generated Outreach Blueprints")
            df_results = st.session_state.df_results
            
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                export_df = df_results.copy()
                for i, row in export_df.iterrows():
                    if row['AI_Outreach'] and row['AI_Outreach'].get('outreach_options'):
                        for j, option in enumerate(row['AI_Outreach']['outreach_options']):
                            export_df.at[i, f'Option_{j+1}_Title'] = option.get('title')
                            export_df.at[i, f'Option_{j+1}_SMS'] = option.get('sms')
                            export_df.at[i, f'Option_{j+1}_Email'] = option.get('email')
                export_df.drop('AI_Outreach', axis=1).to_excel(writer, index=False, sheet_name='AI_Outreach_Plan')

            st.download_button(
                label="📥 Download Full Data Report (Excel)",
                data=output_buffer.getvalue(),
                file_name="AI_Outreach_Plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            for index, row in df_results.iterrows():
                with st.expander(f"👤 **{row['Borrower First Name']} {row.get('Borrower Last Name', '')}** | Max Savings: **${row.get('Savings (30yr)', 0):.2f}/mo**"):
                    st.subheader("Financial Snapshot")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Current P&I", f"${clean_currency(row['Current P&I Mtg Pymt']):,.2f}")
                    col2.metric("Est. New P&I (30yr)", f"${row.get('New P&I (30yr)', 0):.2f}", delta=f"{-row.get('Savings (30yr)', 0):.2f}")
                    col3.metric("Max Cash-Out", f"${row['Max Cash-Out Amount']:,.2f}")

                    st.subheader("AI-Generated Outreach Options")
                    if row['AI_Outreach'] and row['AI_Outreach'].get('outreach_options'):
                        pdf_data = {
                            "Borrower First Name": row['Borrower First Name'],
                            "Borrower Last Name": row.get('Borrower Last Name', ''),
                            "snapshot": {
                                "Current P&I": f"${clean_currency(row['Current P&I Mtg Pymt']):,.2f}",
                                "Est. New P&I (30yr)": f"${row.get('New P&I (30yr)', 0):.2f}",
                                "Max Cash-Out": f"${row['Max Cash-Out Amount']:,.2f}"
                            },
                            "outreach": row['AI_Outreach']['outreach_options']
                        }
                        st.download_button(
                            label="📄 Download PDF Summary",
                            data=create_pdf_report(pdf_data),
                            file_name=f"{row['Borrower First Name']}_Report.pdf",
                            mime="application/pdf",
                            key=f"pdf_{index}"
                        )
                        for option in row['AI_Outreach']['outreach_options']:
                            st.markdown(f"#### {option.get('title', 'Outreach Option')}")
                            st.text_area("SMS", value=option.get('sms'), height=100, key=f"sms_{index}_{option.get('title')}", help="Copy this template for SMS outreach.")
                            st.text_area("Email", value=option.get('email'), height=200, key=f"email_{index}_{option.get('title')}", help="Copy this template for email outreach.")
                    else:
                        st.warning("Could not generate outreach content for this borrower.")

# --- OTHER AGENTS (Placeholders) ---
elif app_mode == "Guideline & Product Chatbot":
    st.title("Guideline & Product Chatbot")
    st.info("This AI Agent is under construction. The next phase will involve building a RAG pipeline to query your guideline documents.")

elif app_mode == "Social Media Automation":
    st.title("Social Media Automation")
    st.info("This AI Agent is under construction. The next phase will involve integrating with the InVideo API to generate videos from AI-created scripts.")
