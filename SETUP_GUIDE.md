# X-code Setup Guide - Step by Step

## Complete Setup and Demo Recording Guide

### STEP 1: Install Prerequisites

**1.1 Install Python 3.8+**
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify: Open terminal and run `python --version`

**1.2 Install VS Code**
- Download from: https://code.visualstudio.com/
- Install Python extension in VS Code

**1.3 Install Git**
- Download from: https://git-scm.com/downloads
- Verify: Run `git --version`

**1.4 Install ngrok**
- Download from: https://ngrok.com/download
- Extract and add to PATH
- Sign up for free account at https://ngrok.com

---

### STEP 2: Get API Keys

**2.1 Get Groq API Key (FREE)**
1. Go to https://console.groq.com
2. Click "Sign Up" (use Google/GitHub login)
3. Go to "API Keys" section
4. Click "Create API Key"
5. Copy the key (starts with `gsk_...`)
6. Save it somewhere safe

**2.2 Get GitHub Personal Access Token**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "X-code Bot"
4. Select scopes:
   - ✅ repo (all)
   - ✅ write:discussion
5. Click "Generate token"
6. Copy the token (starts with `ghp_...`)
7. Save it somewhere safe

---

### STEP 3: Clone and Setup Project

**3.1 Open VS Code**
- Open a new terminal (Ctrl+` or View → Terminal)

**3.2 Clone the Repository**
```bash
git clone https://github.com/abhi3114-glitch/X-CODE.git
cd X-CODE
```

**3.3 Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

**3.4 Install Dependencies**
```bash
pip install -r requirements.txt
```

Wait for installation to complete (takes 1-2 minutes)

---

### STEP 4: Configure Environment Variables

**4.1 Create .env File**
```bash
# Copy the example file
cp .env.example .env
```

**4.2 Edit .env File**
Open `.env` in VS Code and replace with your actual values:

```env
# GitHub Configuration
GITHUB_TOKEN=ghp_YOUR_ACTUAL_GITHUB_TOKEN_HERE
GITHUB_WEBHOOK_SECRET=my_super_secret_webhook_key_12345

# Groq Configuration
GROQ_API_KEY=gsk_YOUR_ACTUAL_GROQ_API_KEY_HERE
GROQ_MODEL=llama-3.3-70b-versatile

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000

# Review Settings
MAX_FILES_TO_REVIEW=20
MAX_LINES_PER_FILE=500
ENABLE_AUTO_FIX=True
```

**Important:** 
- Replace `ghp_YOUR_ACTUAL_GITHUB_TOKEN_HERE` with your GitHub token
- Replace `gsk_YOUR_ACTUAL_GROQ_API_KEY_HERE` with your Groq API key
- The `GITHUB_WEBHOOK_SECRET` can be any random string you create

**4.3 Save the File**
Press Ctrl+S to save

---

### STEP 5: Test Locally

**5.1 Start the Server**
```bash
python app.py
```

You should see:
```
Configuration validated
Starting X-code AI Code Review Assistant on port 5000
 * Running on http://0.0.0.0:5000
```

**5.2 Test Health Check**
Open browser and go to: http://localhost:5000

You should see:
```json
{
  "status": "running",
  "service": "X-code AI Code Review Assistant",
  "version": "1.0.0"
}
```

**5.3 Keep Server Running**
Leave this terminal running. Open a new terminal in VS Code (click + button)

---

### STEP 6: Expose to Internet with ngrok

**6.1 Start ngrok (in new terminal)**
```bash
ngrok http 5000
```

You'll see output like:
```
Forwarding    https://abc123def456.ngrok.io -> http://localhost:5000
```

**6.2 Copy the HTTPS URL**
Copy the URL that looks like: `https://abc123def456.ngrok.io`

**IMPORTANT:** Keep this terminal running too!

---

### STEP 7: Configure GitHub Webhook

**7.1 Go to Your Repository**
- Open your GitHub repository in browser
- Go to Settings → Webhooks → Add webhook

**7.2 Configure Webhook**
Fill in these fields:

- **Payload URL**: `https://your-ngrok-url.ngrok.io/webhook`
  (Replace with your actual ngrok URL from Step 6.2)
  
- **Content type**: Select `application/json`

- **Secret**: Enter the same value you used for `GITHUB_WEBHOOK_SECRET` in your .env file
  (e.g., `my_super_secret_webhook_key_12345`)

- **Which events?**: Select "Let me select individual events"
  - ✅ Check only "Pull requests"
  - ✅ Uncheck everything else

- **Active**: ✅ Make sure this is checked

**7.3 Click "Add webhook"**

You should see a green checkmark if successful.

---

### STEP 8: Test with a Pull Request

**8.1 Create a Test Branch**
In VS Code terminal:
```bash
git checkout -b test-xcode-review
```

**8.2 Create a Test Python File**
Create a file called `test_code.py`:
```python
# Intentionally bad code for testing
import os

def get_user(user_id):
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    return query

def complex_function(a, b, c, d, e, f, g, h):
    # Too many parameters
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return "nested"
    return "done"
```

**8.3 Commit and Push**
```bash
git add test_code.py
git commit -m "Add test code for X-code review"
git push origin test-xcode-review
```

**8.4 Create Pull Request**
1. Go to your GitHub repository
2. Click "Compare & pull request"
3. Add title: "Test X-code AI Review"
4. Click "Create pull request"

**8.5 Watch X-code Work!**
- Go back to VS Code terminal (where app.py is running)
- You'll see logs showing X-code analyzing the PR
- Go to GitHub PR page
- Refresh after 10-20 seconds
- You should see X-code's review comments!

---

### STEP 9: Record Your Demo

**9.1 Install OBS Studio (Recommended)**
- Download from: https://obsproject.com/
- Install and open OBS Studio

**9.2 Setup Recording**
1. Click "+" under Sources
2. Add "Window Capture" → Select VS Code
3. Add "Window Capture" → Select Browser (GitHub)
4. Arrange windows side by side

**9.3 Demo Script**
Record yourself doing this:

1. **Introduction** (10 seconds)
   - "This is X-code, an AI-powered code review assistant"

2. **Show VS Code** (20 seconds)
   - Show the code running: `python app.py`
   - Show the terminal logs

3. **Show GitHub** (30 seconds)
   - Navigate to your test PR
   - Show the code changes

4. **Show X-code Review** (40 seconds)
   - Point out the inline comments
   - Show security issues detected
   - Show complexity warnings
   - Show auto-fix suggestions

5. **Conclusion** (10 seconds)
   - "X-code uses Groq's Llama 3.3 70B model"
   - "It's fast, accurate, and cost-effective"

**Total Demo Time: ~2 minutes**

---

### STEP 10: Deploy to Production (Optional)

**Option A: Heroku (Easiest)**
```bash
# Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create xcode-review-bot

# Set environment variables
heroku config:set GITHUB_TOKEN=your_token
heroku config:set GROQ_API_KEY=your_key
heroku config:set GITHUB_WEBHOOK_SECRET=your_secret

# Deploy
git push heroku main

# Update GitHub webhook URL to:
# https://xcode-review-bot.herokuapp.com/webhook
```

**Option B: Docker**
```bash
# Build image
docker build -t xcode-bot .

# Run container
docker run -p 5000:5000 --env-file .env xcode-bot
```

---

## Troubleshooting

### Issue: "Module not found"
**Solution:** Make sure virtual environment is activated
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Issue: "Invalid API key"
**Solution:** Check your .env file
- Make sure GROQ_API_KEY is correct
- No extra spaces or quotes
- Key should start with `gsk_`

### Issue: "Webhook not triggering"
**Solution:**
1. Check ngrok is still running
2. Check webhook URL in GitHub settings
3. Check webhook secret matches .env file
4. Look at webhook delivery logs in GitHub

### Issue: "Permission denied" on GitHub
**Solution:**
- Check GitHub token has `repo` and `write:discussion` scopes
- Generate a new token if needed

---

## Quick Reference Commands

```bash
# Start virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run the app
python app.py

# Start ngrok
ngrok http 5000

# Check if server is running
curl http://localhost:5000

# View logs
# Just watch the terminal where app.py is running
```

---

## Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review the terminal logs for error messages
3. Check GitHub webhook delivery logs
4. Verify all API keys are correct in .env file

---

**Congratulations! You now have X-code running and reviewing your code automatically!**