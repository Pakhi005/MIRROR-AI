# 🚀 Your Next Steps – Action Plan

Everything is coded. Here's what **you** need to do now to get it running.

---

## Step 1: Install New Python Dependencies
Open a terminal in `backend-python/` and run:
```bash
cd backend-python
.\venv\Scripts\activate        # Windows
pip install langchain langgraph langchain-google-genai openai boto3
```

---

## Step 2: Update Your `.env` File
Open `backend-python/.env` and add these keys:

```env
# Already have this one:
GEMINI_API_KEY=your_gemini_key_here

# NEW — For Whisper audio transcription:
OPENAI_API_KEY=your_openai_api_key_here

# NEW — For sending email reports via AWS SES:
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
SES_SENDER_EMAIL=your_verified_email@example.com
```

### Where to get these:
| Key | Where to get it |
|-----|----------------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `AWS_ACCESS_KEY_ID` / `SECRET` | AWS Console → IAM → Create User → Generate Access Key |
| `SES_SENDER_EMAIL` | AWS Console → SES → Verified Identities → Verify your email |

> [!IMPORTANT]
> **AWS SES Sandbox**: By default, SES is in sandbox mode. You can only send emails **to verified email addresses**. Either verify the recipient email too, or request production access in SES console.

---

## Step 3: Test Locally
```bash
# Terminal 1 — Start Python backend
cd backend-python
.\venv\Scripts\activate
python app.py

# Terminal 2 — Start Node backend  
cd backend-node
node server.js

# Terminal 3 — Serve frontend (any simple server)
cd frontend
python -m http.server 8080
```
Then open `http://localhost:8080/mock.html` in Chrome.

### What to test:
- [ ] Paste a JD and enter your email → Click "Start Interview"
- [ ] Click 🎤 to record → Speak → Click 🛑 Stop
- [ ] Click "Submit Answer" → Check that transcript appears and feedback loads
- [ ] Complete all 5 questions → Verify the email arrives via SES

---

## Step 4: Deploy to EC2

### 4a. Frontend → Netlify / Vercel
1. Go to [netlify.com](https://netlify.com) or [vercel.com](https://vercel.com)
2. Drag & drop the `frontend/` folder (Netlify) or connect your GitHub repo (Vercel)
3. **After deploying**, update the API URLs in `mock.html` from `http://localhost:5000` to your EC2 public IP (e.g., `http://YOUR_EC2_IP:5000`)

### 4b. Both Backends → EC2
1. Launch an EC2 instance (Ubuntu 22.04, t2.medium recommended)
2. Install Docker & Docker Compose:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker $USER
   ```
3. Clone your repo on EC2:
   ```bash
   git clone https://github.com/YOUR_REPO.git
   cd AI-MOCK-INTERVIEW
   ```
4. Create your `.env` files on EC2 with the same keys as Step 2
5. Run:
   ```bash
   docker-compose up -d --build
   ```
6. Open EC2 Security Group to allow ports **3000** and **5000** inbound

---

## Quick Summary

| # | Task | Time Est. |
|---|------|-----------|
| 1 | Install pip packages | 2 min |
| 2 | Add API keys to `.env` | 5 min |
| 3 | Test locally | 10 min |
| 4 | Deploy frontend to Netlify/Vercel | 5 min |
| 5 | Deploy backends to EC2 via Docker | 15 min |

> [!TIP]
> Start with Steps 1-3 first to make sure everything works locally before deploying.
