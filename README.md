# FamEase

FamEase is a family budgeting and expense-tracking web application built with Flask. It helps families record shared expenses, review spending trends, plan meals, and make better day-to-day financial decisions from one dashboard.

## Features

- User registration and login with hashed passwords
- Family-member setup during registration
- Add and delete expenses with date, item, amount, and payer details
- Monthly and all-time spending summaries
- Charts and spending insights in the dashboard
- Receipt scanning with browser-based OCR
- Travel-cost calculator
- Weather lookup for planning and daily decisions
- Gemini-powered assistance when a Gemini API key is configured
- Demo mode available at `/demo`
- Responsive interface for desktop and mobile screens

## Technology

- Python 3.10+
- Flask
- Werkzeug
- Google Generative AI SDK
- Jinja2 templates
- Chart.js, Tesseract.js, and Google Fonts via CDN
- JSON file storage (`data.json`)

## Project structure

```text
.
├── app.py                         # Flask application and routes
├── data.json                      # Local users and expense data
├── requirements.txt               # Python dependencies
├── static/
│   └── images/
│       └── FamEase.png            # Application logo
└── templates/
    ├── index.html                 # Main dashboard
    ├── login.html                 # Login page
    ├── register.html              # Registration page
    └── FINAL BYTE BATTLE WORKING.html
```

## Getting started

### 1. Clone the repository

```bash
git clone <repository-url>
cd HackathonStoneHill-main
```

### 2. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Set a unique Flask secret and add optional service keys before starting the app:

```bash
export SECRET_KEY="replace-with-a-long-random-value"
export WEATHER_API_KEY="your-weatherapi-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

On Windows PowerShell:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
$env:WEATHER_API_KEY = "your-weatherapi-key"
$env:GEMINI_API_KEY = "your-gemini-api-key"
```

The weather and Gemini integrations are optional. The core expense tracker works without them.

> **Security note:** Never commit real API keys, passwords, or production secrets. Use environment variables and rotate any credentials that may have been exposed in local source or sample data.

### 5. Run the application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser.

## Demo mode

Visit [http://127.0.0.1:5000/demo](http://127.0.0.1:5000/demo) to open the dashboard in demo mode. For normal use, create a new account from the registration page.

## Data storage

FamEase currently stores users and expenses in `data.json`. This is convenient for local demos and hackathon deployments, but it is not intended for concurrent production workloads. Back up this file before making changes, and use a database with proper migrations and access controls for production.

## Development notes

- Run the app from the repository root so `data.json` is found correctly.
- The browser loads Chart.js, Tesseract.js, and Google Fonts from public CDNs.
- Receipt OCR runs in the browser and depends on a modern browser with JavaScript enabled.
- Optional integrations fail gracefully when their dependencies or API keys are unavailable.

## License

No license has been specified yet. Add a license before distributing or publishing the project.
