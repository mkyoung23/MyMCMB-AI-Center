import os
import tempfile

import streamlit as st
import pandas as pd

from loan_processor_new import (
    process_loans,
    generate_realistic_texts,
    save_action_sheet,
    sync_to_jungo,
    OUTPUT_FOLDER,
)


def main() -> None:
    """Simple Streamlit UI for the Previous Client Refi Automation.

    This app allows a loan officer to upload a spreadsheet of previous clients,
    performs a comprehensive refinance analysis using the functions from
    ``loan_processor_new``, displays a summary of the top opportunities, lets
    the user download the full analysis and action sheet, and optionally
    syncs the best leads to Jungo.

    To use the app, run ``streamlit run refi_automation_app.py``. Ensure that
    ``JUNGO_API_KEY`` and ``JUNGO_BASE_URL`` environment variables are set
    appropriately if you wish to enable Jungo syncing.
    """
    st.set_page_config(page_title="Previous Client Refi Automation", layout="wide")
    st.title("Previous Client Refi Automation")
    st.write(
        "Upload a CSV or Excel file containing your previous borrower data. "
        "The app will calculate new loan scenarios, suggest lender‑credit and "
        "with‑points options, generate realistic outreach texts, and provide "
        "downloadable summaries."
    )

    uploaded_file = st.file_uploader(
        "Upload Borrower File", type=["csv", "xlsx", "xls"], help="CSV or Excel file with borrower details"
    )
    officer_name = st.text_input("Your Name", "", help="Full name of the loan officer sending texts")
    company_name = st.text_input("Company", "", help="Name of your mortgage company")

    market_tone = st.selectbox(
        "Market Tone", 
        [
            "rates_rising",
            "rates_falling",
            "rates_stable",
            "opportunity",
            "neutral",
            "urgent",
            "custom",
        ],
        index=4,
        help="Select the general tone for your outreach messages",
    )
    custom_msg = ""
    if market_tone == "custom":
        custom_msg = st.text_input("Custom Market Message", "", help="Custom intro for your messages")

    if uploaded_file and officer_name and company_name:
        # Save uploaded file temporarily to disk for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix="_borrowers") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        # Perform analysis
        with st.spinner("Processing borrower data..."):
            analysis_path, df, errors, warnings = process_loans(tmp_path, officer_name, company_name)
        # Display validation results
        if errors:
            st.error("Errors detected during calculation:")
            for err in errors:
                st.write(f"• {err}")
        if warnings:
            st.warning("Warnings:")
            for warn in warnings:
                st.write(f"• {warn}")
        # Generate recommendations and show top opportunities
        recs = generate_realistic_texts(df, officer_name, company_name, market_tone, custom_msg)
        st.subheader("Top 10 Refinance Opportunities")
        st.dataframe(
            recs[["Borrower Name", "Phone", "Email", "Best Savings"]].set_index("Borrower Name"),
            use_container_width=True,
        )
        # Provide download buttons
        with open(analysis_path, "rb") as f:
            st.download_button(
                label="Download Full Analysis Workbook",
                data=f.read(),
                file_name=os.path.basename(analysis_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        export_stub = os.path.splitext(os.path.basename(analysis_path))[0].replace("_REFI_ANALYSIS", "")
        action_path = save_action_sheet(recs, export_stub)
        with open(action_path, "rb") as f2:
            st.download_button(
                label="Download Action Sheet",
                data=f2.read(),
                file_name=os.path.basename(action_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        # Jungo sync button
        if st.button("Sync Top 10 to Jungo CRM"):
            synced = sync_to_jungo(df)
            if synced:
                st.success(f"Synced {synced} leads to Jungo.")
            else:
                st.info("No leads were synced (check API key and configuration).")


if __name__ == "__main__":
    main()