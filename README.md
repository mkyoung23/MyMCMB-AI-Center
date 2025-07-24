# 🏠 MyMCMB AI Command Center

**The ultimate AI-powered refinance intelligence platform for mortgage professionals**

Generate personalized outreach plans, calculate refinance scenarios, and create professional reports in minutes - all powered by advanced AI.

---

## 🚀 **QUICK START - Get Running in 30 Seconds!**

### **Option 1: Easy Launch (Recommended)**

**Windows Users:**
```bash
# Double-click this file or run in Command Prompt:
start_app.bat
```

**Mac/Linux Users:**
```bash
# Make executable and run:
chmod +x start_app.sh
./start_app.sh
```

### **Option 2: Manual Launch**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the app
streamlit run app.py
```

**🌐 The app will automatically open at: http://localhost:8501**

---

## ⚙️ **Configuration Setup**

Before first use, you need to configure your API keys:

1. **Get a Google Gemini API Key**
   - Visit: https://makersuite.google.com/app/apikey
   - Create a new API key
   - Copy the key

2. **Create Configuration File**
   ```bash
   # Create the .streamlit directory
   mkdir .streamlit
   
   # Create secrets.toml file
   nano .streamlit/secrets.toml
   ```

3. **Add Your Keys**
   ```toml
   GEMINI_API_KEY = "your-actual-google-gemini-api-key-here"
   APP_PASSWORD = "your-secure-admin-password"
   ```

---

## 📊 **How to Upload Excel Files**

Your Excel spreadsheet needs these columns (column names are flexible - see variations below):

| **Required Data** | **Accepted Column Names** |
|-------------------|---------------------------|
| **Borrower First Name** | borrower first name, first name, fname, first |
| **Borrower Last Name** | borrower last name, last name, lname, last |
| **Current P&I Payment** | current p&i mtg pymt, current payment, pi payment, current p&i |
| **Original Property Value** | original property value, purchase price, original home value, home value |
| **Original Loan Amount** | total original loan amount, original loan amount, loan amount, original loan balance |
| **Current Interest Rate** | current interest rate, interest rate, rate |
| **Loan Term** | loan term (years), loan term, term |
| **First Payment Date** | first pymt date, first payment date, first payment |
| **City** | city, property city, borrower city |

**✅ The app automatically recognizes these column variations - no need to rename your columns!**

---

## 🎯 **Complete Workflow**

1. **📂 Upload Your Data**
   - Drop your Excel file with borrower data
   - Or manually enter borrower information
   - App validates and maps columns automatically

2. **🔧 Set Parameters**
   - Adjust home appreciation rate (default: 7%)
   - Review data preview

3. **🤖 Generate AI Plans**
   - Click "🚀 Generate AI Outreach Plans"
   - AI analyzes each borrower's situation
   - Creates personalized outreach templates

4. **📥 Download Results**
   - **Excel Report**: Color-coded spreadsheet with all scenarios
   - **PDF Reports**: Individual borrower summaries
   - **Text Export**: Complete outreach templates

---

## ✨ **Key Features**

- **🧠 AI-Powered Outreach**: Personalized SMS and email templates for each borrower
- **📈 Smart Calculations**: Automatic refinance scenario analysis (15yr, 20yr, 30yr, ARM options)
- **💰 Cash-Out Analysis**: Calculate maximum cash-out and "same payment" options
- **🎨 Professional Reports**: Color-coded Excel exports with summary sheets
- **🔄 Flexible Input**: Excel upload or manual entry
- **📱 Mobile-Friendly**: Responsive design works on all devices

---

## 🚨 **Troubleshooting**

**❌ "Could not configure AI models" Error**
- Check that `.streamlit/secrets.toml` exists
- Verify your Google Gemini API key is valid
- Ensure the file format is correct TOML syntax

**❌ "Missing required columns" Error**
- Check your Excel file has all required data columns
- Column names can use any variation listed above
- Make sure there are no completely empty columns

**❌ App won't start**
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (needs 3.8+)
- Try: `python -m streamlit run app.py`

**❌ Calculations seem wrong**
- Verify date format in "First Payment Date" column
- Check that interest rates are in percentage format (e.g., 7.25, not 0.0725)
- Ensure payment amounts don't include taxes/insurance

---

## 🌟 **Pro Tips**

- **📋 Keep Your Spreadsheet As-Is**: No need to rename columns - the app maps them automatically
- **💡 Use Realistic Appreciation Rates**: 7% is the default, but adjust based on your market
- **🎯 Review Before Sending**: Always review AI-generated templates before using with clients
- **📊 Export Multiple Formats**: Use Excel for analysis, PDFs for client presentations
- **🔄 Batch Processing**: Upload multiple borrowers at once for efficiency

---

## 📞 **Need Help?**

- **📖 Documentation**: This README contains all setup instructions
- **🐛 Issues**: Check the troubleshooting section above
- **💬 Questions**: Review the in-app help text and tooltips

---

## 🔒 **Security & Privacy**

- **🔐 API Keys**: Stored locally in your `.streamlit/secrets.toml` file
- **📊 Data Processing**: All calculations happen locally
- **🤖 AI Processing**: Borrower data sent to Google Gemini for outreach generation only
- **💾 No Data Storage**: App doesn't store your borrower data permanently

---

**🎉 Ready to boost your refinance business with AI? Run the app and start generating personalized outreach plans in minutes!**
