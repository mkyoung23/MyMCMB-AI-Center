# MyMCMB AI Command Center

🚀 **AI-Powered Mortgage Automation Platform** for loan officers and mortgage professionals.

## 🎯 What It Does

This comprehensive Streamlit application provides four powerful AI agents to streamline your mortgage business:

### 1. 📊 Refinance Intelligence Center
Generate hyper-personalized outreach campaigns for your borrower database:
- **Bulk Analysis**: Upload Excel files with borrower data
- **Manual Entry**: Add individual borrowers with guided forms  
- **AI Outreach**: Generate 4 personalized templates per borrower (SMS + Email)
- **Financial Scenarios**: Calculate payments for multiple loan terms
- **Export Options**: Professional Excel, PDF, and text reports

### 2. ⚙️ Admin Rate Panel
Secure rate management system for loan officers:
- Password-protected access
- Real-time rate updates for all loan products
- Support for conventional, ARM, and HELOC rates
- No-cost refinance adjustments

### 3. 💬 Guideline & Product Chatbot
Interactive mortgage expertise at your fingertips:
- Comprehensive knowledge base (FHA, VA, Conventional, USDA, Jumbo loans)
- Real-time Q&A with mortgage guidelines
- Chat history with export capabilities
- Quick-access buttons for popular questions

### 4. 📱 Social Media Automation
Create engaging content for all major platforms:
- **Multi-Platform**: Facebook, Instagram, Twitter/X, LinkedIn, TikTok
- **Content Types**: Market updates, educational posts, rate alerts, tips
- **Personalization**: Add your contact info and branding
- **Export Ready**: Text and CSV formats for content calendars

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation
```bash
# Clone the repository
git clone https://github.com/mkyoung23/MyMCMB-AI-Center.git
cd MyMCMB-AI-Center

# Install dependencies
pip install -r requirements.txt

# Set up your API keys
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml with your actual API key and admin password

# Launch the application
streamlit run app.py
```

Your AI Command Center will be available at `http://localhost:8501`

## 📋 Required Data Columns (for Refinance Intelligence)

The Refinance Intelligence Center expects the following columns. Header names are matched case-insensitively and may use any of the listed variations:

| Required Column | Accepted Variations |
|----------------|--------------------|
| Borrower First Name | borrower first name, first name, fname, first |
| Borrower Last Name | borrower last name, last name, lname, last |
| Current P&I Mtg Pymt | current p&i mtg pymt, current payment, pi payment, current p&i |
| Original Property Value | original property value, purchase price, original home value, home value |
| Total Original Loan Amount | total original loan amount, original loan amount, loan amount, original loan balance |
| Current Interest Rate | current interest rate, interest rate, rate |
| Loan Term (years) | loan term (years), loan term, term |
| First Pymt Date | first pymt date, first payment date, first payment |
| City | city, property city, borrower city |

## 🔧 Configuration

### Environment Setup
Create a `.streamlit/secrets.toml` file:
```toml
GEMINI_API_KEY = "your-google-gemini-api-key"
APP_PASSWORD = "your-secure-admin-password"
```

### Testing Your Setup
```bash
# Verify Python compilation
python -m py_compile app.py

# Check dependencies
pip install -r requirements.txt
```

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions including:
- Streamlit Cloud (recommended)
- Heroku
- Docker
- AWS/GCP/Azure

## ✨ Features

### 🎨 Professional UI/UX
- Modern dark theme design
- Responsive layout for all devices
- Intuitive navigation and workflow
- Professional styling and branding

### 🤖 AI-Powered Intelligence
- Powered by Google Gemini AI
- Context-aware content generation
- Personalized outreach templates
- Expert mortgage guidance

### 📊 Advanced Analytics
- Financial scenario modeling
- LTV and cash-out calculations
- Payment comparison tools
- Market trend analysis

### 🔒 Security & Privacy
- Secure API key management
- Password-protected admin areas
- No permanent data storage
- Privacy-first design

### 📈 Business Impact
- **Increase Conversion**: Personalized outreach templates
- **Save Time**: Automated content generation
- **Stay Current**: Real-time rate management
- **Build Authority**: Professional social media presence

## 🎯 Use Cases

### For Loan Officers
- Generate personalized refinance campaigns
- Create social media content to build your brand
- Access mortgage guidelines instantly
- Manage rates and products efficiently

### For Mortgage Companies
- Scale outreach efforts across large databases
- Standardize communication templates
- Improve loan officer productivity
- Enhance client experience

### For Marketing Teams
- Create consistent social media content
- Generate educational materials
- Automate campaign development
- Track engagement opportunities

## 📞 Support

The application is fully functional and production-ready. The **Assumed Annual Home Appreciation Rate (%)** input defaults to 7% and drives home value and LTV calculations.

Once the AI analysis finishes, you can download:
- 📊 Enhanced Excel workbook with summary sheet
- 📋 Individual PDF summaries with personalized templates
- 📄 Comprehensive text reports

## 🚀 What's New

### ✅ Completed Features
- ✅ **Refinance Intelligence Center**: Full automation with AI outreach
- ✅ **Admin Rate Panel**: Complete rate management system  
- ✅ **Guideline & Product Chatbot**: Interactive mortgage expertise
- ✅ **Social Media Automation**: Multi-platform content generation

### 🔧 Technical Improvements
- Enhanced error handling and validation
- Professional export formats with styling
- Responsive design and mobile optimization
- Comprehensive deployment documentation

---

**Ready to transform your mortgage business with AI?** 🚀

Navigate to the **Refinance Intelligence Center** tab, upload your Excel sheet or enter borrower data manually, and click **Generate AI Outreach Plans** to get started!
