# FamEase

FamEase is a family budgeting and expense-tracking web application built with Flask. It helps families record shared expenses, review spending trends, plan meals, and make better day-to-day financial decisions from one dashboard.

## Features

- User registration and login with hashed passwords
- Family-member setup during registration
- Add and delete expenses with date, item, amount, and payer details
- Monthly and all-time spending summaries
- Charts and spending insights in the dashboard
- Receipt scanning with browser-based OCR and optional expense entry
- Demo mode available at `/demo`
- Responsive interface for desktop and mobile screens

## Technology

- Python 3.10+
- Flask
- Werkzeug
- Jinja2 templates
- Chart.js, Tesseract.js, and Google Fonts via CDN
- Local JSON storage for development; PostgreSQL for Render deployments

## Project structure

```text
.
├── app.py                         # Flask application and routes
├── data.json                      # Local users and expense data
├── requirements.txt               # Python dependencies
├── schema.sql                     # Persistent database table definition
├── static/
│   └── images/FamEase.png         # Application logo
└── templates/
    ├── index.html                 # Main dashboard
    ├── login.html                 # Login page
    └── register.html              # Registration page
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

Set a unique Flask secret before starting the app:

```bash
export SECRET_KEY="replace-with-a-long-random-value"
```

On Windows PowerShell:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
```

> **Security note:** Never commit real API keys, passwords, or production secrets. Use environment variables and rotate any credentials that may have been exposed in local source or sample data.

### 5. Run the application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser.

## Demo mode

Visit [http://127.0.0.1:5000/demo](http://127.0.0.1:5000/demo) to open the dashboard with sample expenses. Demo data is read-only. For normal use, create a new account from the registration page.

## Data storage

Local development uses `data.json`. For Render deployments, configure a persistent PostgreSQL database and set `DATABASE_URL` and `SECRET_KEY` in the service's environment variables. The app refuses account and expense operations if Render is missing `DATABASE_URL`, rather than silently saving data to an ephemeral file. Run [schema.sql](./schema.sql) in the database if you want to create the table before the first request; the app also creates it automatically.

Existing accounts and expenses in local `data.json` are not copied automatically to the deployment database. Back up that file before making changes, and migrate any data you need before switching users to the deployed app.

## Development notes

- Run the app from the repository root so local `data.json` is found correctly.
- The browser loads Chart.js, Tesseract.js, and Google Fonts from public CDNs.
- Receipt OCR runs in the browser and requires an internet connection to load Tesseract.js.

## License

No license has been specified yet. Add a license before distributing or publishing the project.
