# Cloud Deployment Guide for MyMCMB AI Command Center

This guide helps you deploy the app to popular cloud platforms for easy access from anywhere.

## 🌐 Streamlit Community Cloud (Recommended - FREE)

**1. Push to GitHub (if not already done)**
```bash
git add .
git commit -m "Ready for cloud deployment"
git push origin main
```

**2. Deploy to Streamlit Cloud**
- Visit: https://share.streamlit.io/
- Sign in with GitHub
- Click "New app"
- Select your repository: `yourusername/MyMCMB-AI-Center`
- Main file path: `app.py`
- Click "Deploy!"

**3. Add Secrets in Cloud**
- In Streamlit Cloud dashboard, click your app
- Go to "Settings" → "Secrets"
- Add your secrets in TOML format:
```toml
GEMINI_API_KEY = "your-google-gemini-api-key"
APP_PASSWORD = "your-admin-password"
```

**4. Access Your App**
- Your app will be available at: `https://yourapp.streamlit.app`
- Share this link with your team for easy access!

## 🚀 Heroku Deployment

**1. Install Heroku CLI**
```bash
# Download from: https://devcenter.heroku.com/articles/heroku-cli
heroku --version
```

**2. Create Heroku App**
```bash
heroku create your-mymcmb-app
heroku config:set GEMINI_API_KEY="your-api-key"
heroku config:set APP_PASSWORD="your-password"
```

**3. Create Procfile**
```bash
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile
```

**4. Deploy**
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 🐳 Docker Deployment

**Create Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

**Build and Run:**
```bash
docker build -t mymcmb-ai .
docker run -p 8501:8501 mymcmb-ai
```

## 🔗 Quick Access Tips

**1. Create Desktop Shortcuts**
- Windows: Create `.url` file with your Streamlit URL
- Mac: Drag URL from browser to desktop
- Linux: Create `.desktop` file

**2. Bookmark the URL**
- Add to browser bookmarks bar
- Create bookmark folder "MyMCMB Tools"

**3. Share with Team**
- Send the Streamlit Cloud URL to colleagues
- No installation needed - works in any browser
- Mobile-friendly for on-the-go access

**4. QR Code Access**
- Generate QR code for your app URL
- Print and post in office for quick mobile access