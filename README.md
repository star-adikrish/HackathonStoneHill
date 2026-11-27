# FamEase

FamEase is a family budgeting and household planning application built with Flask. It brings receipt scanning, shared expense tracking, meal planning, to-do lists, and optional household-helper access into one responsive dashboard.

## Live Website

The latest deployed version is available at:

**https://famease.onrender.com/**

The deployed URL may change when the hosting configuration changes.

## Features

- Create family accounts with hashed passwords
- Add, view, and delete household expenses
- Review monthly and all-time spending
- View spending summaries with charts
- Scan receipts in the browser with Tesseract.js
- Turn recognized receipt items into expense entries
- Plan meals and keep a saved weekly meal table
- Create and manage a browser-saved to-do list
- Create a separate meal-planner account for a househelp
- Use read-only demo mode for local testing
- Use the responsive dashboard on desktop and mobile devices

## Demo

Start the application locally, then visit:

**http://127.0.0.1:5000/demo**

Demo mode uses sample expenses and is read-only. It does not save expense changes.

## Technology Stack

- Python 3.10+
- Flask
- Werkzeug
- Jinja2
- Chart.js
- Tesseract.js
- JSON for local development storage
- PostgreSQL for hosted deployments

## Project Structure

```text
.
├── app.py
├── data.json
├── requirements.txt
├── schema.sql
├── static/
│   ├── auth.css
│   ├── style.css
│   └── images/
│       └── FamEase.png
└── templates/
    ├── index.html
    ├── login.html
    └── register.html
```

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd HackathonStoneHill-main
```
Or from repo Famease

### 2. Create and activate a virtual environment

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Set a Flask secret key for persistent local sessions:

**macOS/Linux**

```bash
export SECRET_KEY="replace-with-a-long-random-value"
```

**Windows PowerShell**

```powershell
$env:SECRET_KEY="replace-with-a-long-random-value"
```

For hosted PostgreSQL storage, also set:

```text
DATABASE_URL=<PostgreSQL connection string>
```

`WEATHER_API_KEY` is optional and enables the weather endpoint when configured.

Never commit real API keys, passwords, or database credentials.

### 5. Run the application

From the repository root:

```bash
python app.py
```

Open **http://127.0.0.1:5000**.

For Flask debug mode, set `FLASK_DEBUG=1` before starting the application.

## Data Storage

### Local development

FamEase stores application accounts and expenses in `data.json` unless `DATABASE_URL` is configured.

Run the application from the repository root so the JSON file is found and updated correctly.

`data.json` is demonstration and local-development data. It should not contain real financial information or credentials.

### Hosted deployments

Set `DATABASE_URL` and `SECRET_KEY` in the hosting service. FamEase will:

- Create the `famease_app_state` table automatically when needed
- Store application data in PostgreSQL
- Refuse account and expense operations if persistent database configuration is missing

The SQL schema is also available in `schema.sql`.

Local JSON accounts and expenses are not automatically migrated to PostgreSQL.

## Meal Planner and To-Do Storage

Meal plans and to-do items are stored in the current browser's local storage. They are not stored in the account database and do not synchronize across browsers or devices.

Clearing browser data removes saved meal plans and to-do items.

## Househelp Account

A household owner can create a separate meal-planner login from the **Househelp** tab.

- Choose a unique username
- Use a password of at least eight characters
- Share the credentials privately

The househelp account can access the meal planner only. Family expenses and other dashboard routes are restricted.

## WhatsApp Contact

The WhatsApp integration is intentionally not connected to a real phone number.

Before using it, replace the placeholder number in the `sendToWhatsApp` function and the WhatsApp link in [templates/index.html](templates/index.html) with the intended public number.