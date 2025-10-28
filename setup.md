# FilePulse Setup Guide

## 🔐 Environment Configuration

### Step 1: Create `.env` file

Copy the example file and add your API key:

```bash
cp .env.example .env
```

### Step 2: Add your Resend API Key

Open `.env` and replace the placeholder:

```env
RESEND_API_KEY=re_your_actual_api_key_here
```

**Get your API key from:** https://resend.com/api-keys

### Step 3: Verify `.env` is ignored by Git

Check that `.env` is listed in `.gitignore`:

```bash
cat .gitignore | grep ".env"
```

You should see `.env` in the output.

---

## 📦 Installation

### Install dependencies:

```bash
pip install -r requirements.txt
```

### Run the application:

```bash
python main.py
```

### Development mode (with auto-reload):

```bash
python rundev.py
```

---

## 🚀 Building EXE

When building the EXE, the `.env` file will be **bundled** with the executable:

```bash
pyinstaller --onefile --windowed --add-data ".env;." main.py
```

**Note:** The `.env` file will be included in the EXE, so make sure you're using a production API key!

---

## ⚠️ Security Notes

1. **Never commit `.env`** - It's in `.gitignore` for safety
2. **Keep `.env.example`** - Safe to commit (no real keys)
3. **Rotate keys** - If accidentally exposed, regenerate on Resend dashboard
4. **Production builds** - Use separate API keys for dev vs production

---

## 🧪 Testing Email Configuration

1. Go to **Tab 3** (Settings)
2. Enter your email in the **Recipients** field
3. Click **"Send Test Email"** button
4. Check your inbox!

---

## 📁 Project Structure

```
FilePulse/
├── .env                # ⚠️ SECRET - Your API keys (NOT in git)
├── .env.example        # ✅ Template (safe to commit)
├── .gitignore          # ✅ Protects secrets
├── main.py             # Entry point
├── scheduler.py        # Email & scheduling logic
├── tab3.py             # Settings UI
├── requirements.txt    # Dependencies
└── ...
```