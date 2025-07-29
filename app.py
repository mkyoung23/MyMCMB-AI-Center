
import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime
import re
import io
from fpdf import FPDF
import os

# --- CONFIG & API KEY SETUP ---
st.set_page_config(page_title="MyMCMB AI Center", layout="wide")


# Load API keys from .streamlit/secrets.toml
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else None
APP_PASSWORD = "RealRefi#23"

# --- GLOBAL PASSWORD PROTECTION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("🔒 MyMCMB AI Center Login")
    password_input = st.text_input("Enter Password to Access App", type="password")
    login_attempt = st.button("Login")
    if login_attempt:
        if password_input == APP_PASSWORD:
            st.session_state.authenticated = True
        else:
            st.error("Incorrect password. Please try again.")
    if not st.session_state.authenticated:
        st.stop()

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("MyMCMB AI Command Center")
app_mode = st.sidebar.selectbox(
    "Select an AI Agent",
    [
        "Refinance Intelligence Center",
        "Admin Rate Panel",
        "Guideline & Product Chatbot",
        "Social Media Automation"
    ]
)


# --- REFINANCE INTELLIGENCE CENTER ---
def calculate_amortization(principal, annual_rate, term_years):
    """Return amortization schedule as DataFrame and final balance."""
    monthly_rate = annual_rate / 12 / 100
    n_payments = term_years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
    schedule = []
    balance = principal
    for i in range(1, n_payments + 1):
        interest = balance * monthly_rate
        principal_paid = payment - interest
        balance -= principal_paid
        schedule.append({
            "Month": i,
            "Payment": payment,
            "Principal": principal_paid,
            "Interest": interest,
            "Balance": max(balance, 0)
        })
    df = pd.DataFrame(schedule)
    return df, max(balance, 0)

def clean_currency(val):
    try:
        return float(re.sub(r"[^0-9.]+", "", str(val)))
    except:
        return 0.0

def refinance_intelligence_center():
    st.title("Refinance Intelligence Center")
    st.markdown("### Input borrower data to generate hyper-personalized outreach plans.")
    input_method = st.radio(
        "Select Data Input Method:",
        ["📁 Upload Excel File", "✏️ Manual Entry"],
        horizontal=True
    )
    df = None
    if input_method == "📁 Upload Excel File":
        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls", "csv"])
        if uploaded_file:
            if uploaded_file.name.endswith("csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
    else:
        st.markdown("#### Manual Entry")
        if "manual_borrowers" not in st.session_state:
            st.session_state.manual_borrowers = []
        with st.form("manual_entry_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                city = st.text_input("City")
                home_value = st.number_input("Estimated Home Value", min_value=0.0, value=400000.0)
            with col2:
                current_payment = st.number_input("Current Monthly P&I", min_value=0.0, value=2500.0)
                balance = st.number_input("Remaining Balance", min_value=0.0, value=350000.0)
                rate = st.number_input("Current Interest Rate (%)", min_value=0.0, max_value=15.0, value=6.5)
                term = st.number_input("Loan Term (years)", min_value=1, max_value=40, value=30)
            submitted = st.form_submit_button("Add Borrower")
            if submitted:
                st.session_state.manual_borrowers.append({
                    "Borrower First Name": first_name,
                    "Borrower Last Name": last_name,
                    "City": city,
                    "Estimated Home Value": home_value,
                    "Current P&I Mtg Pymt": current_payment,
                    "Remaining Balance": balance,
                    "Current Interest Rate": rate,
                    "Loan Term (years)": term
                })
        if st.session_state.manual_borrowers:
            df = pd.DataFrame(st.session_state.manual_borrowers)

    if df is not None and not df.empty:
        st.success("Borrower data loaded!")
        # Calculate scenarios for each borrower
        results = []
        for idx, row in df.iterrows():
            principal = clean_currency(row.get("Remaining Balance", 0))
            input_rate = float(row.get("Current Interest Rate", 0))
            input_term = int(row.get("Loan Term (years)", 30))
            payment = clean_currency(row.get("Current P&I Mtg Pymt", 0))
            home_value = clean_currency(row.get("Estimated Home Value", 0))
            payments_made = int(row.get("Payments Made", 0)) if "Payments Made" in row else 0
            # For now, use input rate/term for refi scenario (can be replaced with admin rates)
            calc_rate = input_rate
            calc_term = input_term
            # Calculate amortization for original loan
            orig_amort_df, _ = calculate_amortization(principal, input_rate, input_term)
            # Calculate new loan amount after payments made
            if payments_made > 0 and payments_made < len(orig_amort_df):
                new_loan_amount = orig_amort_df.iloc[payments_made]["Balance"]
            else:
                new_loan_amount = principal
            new_home_value = home_value
            new_ltv = new_loan_amount / new_home_value * 100 if new_home_value else 0
            # Calculate payment for refi scenario
            refi_amort_df, _ = calculate_amortization(new_loan_amount, calc_rate, calc_term)
            refi_payment = refi_amort_df.iloc[0]["Payment"] if len(refi_amort_df) > 0 else 0.0
            n_and_i = refi_payment
            # --- AI-powered outreach campaigns ---
            campaigns = []
            if GOOGLE_API_KEY:
                prompt = (
                    f"You are a friendly loan officer reaching out to a previous client. "
                    f"Client name: {row.get('Borrower First Name','')} {row.get('Borrower Last Name','')}. "
                    f"City: {row.get('City','')}. "
                    f"New loan amount: ${new_loan_amount:.2f}. "
                    f"Estimated payment: ${n_and_i:.2f}/mo at {calc_rate:.2f}% for {calc_term} years. "
                    f"Create 3 unique, personal, and friendly outreach messages for text or email that will get the most response."
                )
                try:
                    response = genai.generate_text(model="gemini-pro", prompt=prompt, temperature=0.7, max_output_tokens=500)
                    if hasattr(response, 'result') and response.result:
                        raw_msgs = response.result.split('\n')
                        for msg in raw_msgs:
                            msg = msg.strip()
                            if msg:
                                campaigns.append(msg)
                        if len(campaigns) < 3:
                            campaigns += ["[AI message not returned]"] * (3 - len(campaigns))
                    else:
                        campaigns = ["[AI message not returned]"] * 3
                except Exception as e:
                    campaigns = [f"[AI error: {e}]"] * 3
            else:
                campaigns = [
                    f"Hi {row.get('Borrower First Name','')}, it’s your loan officer at MyMCMB. Just checking in to see how you’re enjoying your home! If you have any questions or want to explore new options, I’m here to help.",
                    f"Hey {row.get('Borrower First Name','')}, rates have changed and there may be new opportunities for you! Let’s chat about how you could save or access cash for your next project. Text or call me anytime!",
                    f"Hi {row.get('Borrower First Name','')}, just a quick note—I appreciate you trusting me with your mortgage. If you ever need advice or want to review your options, I’m always available for you and your family."
                ]
            results.append({
                "Borrower First Name": row.get("Borrower First Name", ""),
                "Borrower Last Name": row.get("Borrower Last Name", ""),
                "City": row.get("City", ""),
                "Original Home Value": home_value,
                "New Estimated Home Value": new_home_value,
                "Current P&I Mtg Pymt": payment,
                "Remaining Balance": principal,
                "Payments Made": payments_made,
                "Rate Used": calc_rate,
                "Term Used": calc_term,
                "New Loan Amount": new_loan_amount,
                "Current Interest Rate": input_rate,
                "Loan Term (years)": input_term,
                "New LTV": new_ltv,
                "N&I (New Payment)": n_and_i,
                "Campaign 1": campaigns[0],
                "Campaign 2": campaigns[1],
                "Campaign 3": campaigns[2]
            })
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)
        st.markdown("#### AI-Powered Outreach Campaigns")
        for idx, row in results_df.iterrows():
            st.write(f"**Campaign 1:** {row['Campaign 1']}")
            st.write(f"**Campaign 2:** {row['Campaign 2']}")
            st.write(f"**Campaign 3:** {row['Campaign 3']}")
            st.info(f"Best for: {row['Borrower First Name']} {row['Borrower Last Name']}")

        # --- EXPORT OPTIONS ---
        st.markdown("#### 📥 Export Options")
        col1, col2, col3 = st.columns(3)

        # Excel Export
        with col1:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                results_df.to_excel(writer, index=False, sheet_name="Borrower Scenarios")
            st.download_button(
                label="📊 Download Excel",
                data=excel_buffer.getvalue(),
                file_name="borrower_scenarios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Text Export
        with col2:
            text_lines = []
            for idx, row in results_df.iterrows():
                text_lines.append(f"Borrower: {row['Borrower First Name']} {row['Borrower Last Name']}")
                text_lines.append(f"City: {row['City']}")
                text_lines.append(f"Current Payment: ${row['Current P&I Mtg Pymt']:.2f}")
                text_lines.append(f"New Payment (N&I): ${row['N&I (New Payment)']:.2f}")
                text_lines.append(f"New LTV: {row['New LTV']:.2f}%")
                text_lines.append(f"Campaign 1: {row['Campaign 1']}")
                text_lines.append(f"Campaign 2: {row['Campaign 2']}")
                text_lines.append(f"Campaign 3: {row['Campaign 3']}")
                text_lines.append("-"*40)
            st.download_button(
                label="📄 Download Text",
                data="\n".join(text_lines),
                file_name="borrower_scenarios.txt",
                mime="text/plain"
            )

        # PDF Export
        with col3:
            class SimplePDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 12)
                    self.cell(0, 10, 'Borrower Scenarios Report', 0, 1, 'C')
                def borrower_section(self, row):
                    self.set_font('Arial', '', 10)
                    self.cell(0, 8, f"Borrower: {row['Borrower First Name']} {row['Borrower Last Name']}", 0, 1)
                    self.cell(0, 8, f"City: {row['City']}", 0, 1)
                    self.cell(0, 8, f"Current Payment: ${row['Current P&I Mtg Pymt']:.2f}", 0, 1)
                    self.cell(0, 8, f"Calculated Payment: ${row['N&I (New Payment)']:.2f}", 0, 1)
                    self.cell(0, 8, f"Estimated LTV: {row['New LTV']:.2f}%", 0, 1)
                    outreach = f"Campaign 1: {row['Campaign 1']}\nCampaign 2: {row['Campaign 2']}\nCampaign 3: {row['Campaign 3']}"
                    self.multi_cell(0, 8, f"Outreach: {outreach}")
                    self.cell(0, 8, "-"*40, 0, 1)
            pdf = SimplePDF()
            pdf.add_page()
            for idx, row in results_df.iterrows():
                pdf.borrower_section(row)
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            st.download_button(
                label="📋 Download PDF",
                data=pdf_bytes,
                file_name="borrower_scenarios.pdf",
                mime="application/pdf"
            )


# --- ADMIN RATE PANEL ---
def admin_rate_panel():
    st.title("Admin Rate Panel")
    st.markdown("#### Set Current Mortgage Rates (Saved for All Users)")
    rates_file = "rates.json"
    # Load rates from file if exists
    if "rates" not in st.session_state:
        if os.path.exists(rates_file):
            with open(rates_file, "r") as f:
                st.session_state.rates = json.load(f)
        else:
            st.session_state.rates = {
                "30yr_fixed": 6.5,
                "25yr_fixed": 6.5,
                "20yr_fixed": 6.25,
                "15yr_fixed": 5.75,
                "10yr_fixed": 5.75,
                "5yr_arm": 6.25,
                "jeloc": 8.5,
                "no_cost_adj": 0.25
            }
    with st.form("rate_form"):
        col1, col2 = st.columns(2)
        with col1:
            rate_30 = st.number_input("30-Year Fixed Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["30yr_fixed"], step=0.01)
            rate_25 = st.number_input("25-Year Fixed Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["25yr_fixed"], step=0.01)
            rate_20 = st.number_input("20-Year Fixed Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["20yr_fixed"], step=0.01)
        with col2:
            rate_15 = st.number_input("15-Year Fixed Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["15yr_fixed"], step=0.01)
            rate_10 = st.number_input("10-Year Fixed Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["10yr_fixed"], step=0.01)
            rate_arm = st.number_input("5-Year ARM Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["5yr_arm"], step=0.01)
            rate_jeloc = st.number_input("Interest-Only HELOC (JELOC) Rate (%)", min_value=0.0, max_value=15.0, value=st.session_state.rates["jeloc"], step=0.01)
            no_cost_adj = st.number_input("No-Cost/Cash-Out Rate Adj (%)", min_value=0.0, max_value=2.0, value=st.session_state.rates["no_cost_adj"], step=0.01)
        submitted = st.form_submit_button("Save Rates")
        if submitted:
            st.session_state.rates = {
                "30yr_fixed": rate_30,
                "25yr_fixed": rate_25,
                "20yr_fixed": rate_20,
                "15yr_fixed": rate_15,
                "10yr_fixed": rate_10,
                "5yr_arm": rate_arm,
                "jeloc": rate_jeloc,
                "no_cost_adj": no_cost_adj
            }
            with open(rates_file, "w") as f:
                json.dump(st.session_state.rates, f)
            st.success("Rates updated and saved for all users!")
    st.write("### Current Rates:")
    st.json(st.session_state.rates)


# --- GUIDELINE & PRODUCT CHATBOT ---
def guideline_product_chatbot():
    st.title("Guideline & Product Chatbot")
    st.markdown("### Ask questions about mortgage guidelines, products, and underwriting requirements.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    knowledge_base = {
        "credit score": "Conventional: 620+, FHA: 580+, VA: 620+, USDA: 640+.",
        "down payment": "Conventional: 3%+, FHA: 3.5%+, VA/USDA: 0%.",
        "dti": "Conventional: 45-50%, FHA: 57%, VA: flexible, USDA: 41%.",
        "loan limits": "Conventional: $766,550 (2024), FHA/VA/USDA vary by county.",
        "refinance": "Rate & Term, Cash-Out, Streamline, HARP/FHFA. Max LTV 80% for cash-out.",
        "special programs": "First-time buyer, down payment assistance, renovation, physician, bank statement."
    }
    def get_answer(q):
        ql = q.lower()
        for k, v in knowledge_base.items():
            if k in ql:
                return v
        return "Sorry, I don't have an answer for that. Please ask about credit score, down payment, DTI, loan limits, refinance, or special programs."
    with st.form("chat_form"):
        user_q = st.text_input("Your Question", placeholder="E.g. What is the minimum credit score for FHA?")
        submit = st.form_submit_button("Ask")
        if submit and user_q.strip():
            answer = get_answer(user_q)
            st.session_state.chat_history.append({
                "question": user_q,
                "answer": answer,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    if st.session_state.chat_history:
        st.markdown("#### Chat History")
        for entry in st.session_state.chat_history[-10:]:
            st.write(f"**Q:** {entry['question']}")
            st.write(f"**A:** {entry['answer']}")
            st.caption(entry['timestamp'])
        chat_export = "\n".join([
            f"Q: {e['question']}\nA: {e['answer']}\nTime: {e['timestamp']}\n{'-'*40}" for e in st.session_state.chat_history
        ])
        st.download_button(
            label="📄 Export Chat History",
            data=chat_export,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


# --- SOCIAL MEDIA AUTOMATION ---
def social_media_automation():
    st.title("Social Media Automation")
    st.markdown("### Generate engaging social media content for mortgage professionals.")
    content_type = st.selectbox(
        "Select Content Type:",
        [
            "📊 Market Update Post",
            "💡 Educational Content",
            "🏠 Home Buying Tips",
            "📈 Rate Alert",
            "🎯 First-Time Buyer Guide",
            "💰 Refinance Opportunity",
            "📝 Client Testimonial Template",
            "🎉 Closing Celebration"
        ]
    )
    platforms = st.multiselect(
        "Select Social Media Platforms:",
        ["📘 Facebook", "📸 Instagram", "🐦 Twitter/X", "💼 LinkedIn", "🎵 TikTok"],
        default=["📘 Facebook", "📸 Instagram"]
    )
    with st.expander("📝 Personalization (Optional)"):
        loan_officer_name = st.text_input("Loan Officer Name", placeholder="John Smith")
        company_name = st.text_input("Company Name", placeholder="MyMCMB Mortgage")
        phone_number = st.text_input("Phone Number", placeholder="(555) 123-4567")
        website = st.text_input("Website", placeholder="www.mymcmb.com")
    if st.button("🚀 Generate Social Media Content", type="primary"):
        # Stub: Replace with AI content generation
        posts = []
        for platform in platforms:
            posts.append({
                "platform": platform,
                "content": f"[{content_type}] by {loan_officer_name or 'Loan Officer'} at {company_name or 'Company'} - Call {phone_number or 'N/A'} | {website or 'N/A'}",
                "hashtags": ["mortgage", "realestate", "refinance"],
                "character_count": 120,
                "tips": f"Post on {platform} at optimal times."
            })
        st.session_state.generated_posts = posts
        st.success("Content generated!")
    if "generated_posts" in st.session_state and st.session_state.generated_posts:
        st.markdown("#### Generated Posts")
        for post in st.session_state.generated_posts:
            st.write(f"**{post['platform']}**: {post['content']}")
            st.write(f"Hashtags: {' '.join(['#'+tag for tag in post['hashtags']])}")
            st.caption(f"Characters: {post['character_count']}")
            st.info(post['tips'])
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            text_export = "\n\n".join([
                f"Platform: {p['platform']}\nContent: {p['content']}\nHashtags: {' '.join(['#'+tag for tag in p['hashtags']])}\nTips: {p['tips']}" for p in st.session_state.generated_posts
            ])
            st.download_button(
                label="📄 Download as Text File",
                data=text_export,
                file_name=f"social_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        with col2:
            import csv
            import tempfile
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=["platform", "content", "hashtags", "character_count", "tips"])
            writer.writeheader()
            for p in st.session_state.generated_posts:
                writer.writerow({
                    "platform": p["platform"],
                    "content": p["content"],
                    "hashtags": ", ".join(p["hashtags"]),
                    "character_count": p["character_count"],
                    "tips": p["tips"]
                })
            st.download_button(
                label="📊 Download as CSV",
                data=csv_buffer.getvalue(),
                file_name=f"social_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# --- MAIN APP ROUTER ---
if app_mode == "Refinance Intelligence Center":
    refinance_intelligence_center()
elif app_mode == "Admin Rate Panel":
    admin_rate_panel()
elif app_mode == "Guideline & Product Chatbot":
    guideline_product_chatbot()
elif app_mode == "Social Media Automation":
    social_media_automation()
