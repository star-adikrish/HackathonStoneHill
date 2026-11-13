# FamEase

FamEase is a family budgeting and expense-tracking web application built with Flask. It helps families record shared expenses, monitor spending trends, plan meals, and make better day-to-day financial decisions through a single dashboard.

## Live Website

[https://famease.onrender.com/](https://famease.onrender.com/)
Website link may change in a few weeks, close to 4 to 8 weeks

## Important Notice


Please read the following notes before using this project.

**WhatsApp Integration:**  
The WhatsApp number in the `sendToWhatsApp` function is currently a placeholder (`#########`). Replace it with the intended WhatsApp number before using this feature.

**Public Testing Data:**  
The `data.json` file has been included in the public GitHub repository temporarily for Hack Club review and testing purposes.

- Do not add sensitive, personal, or real financial information to this file.
- The repository is intended to become private after the Hack Club review and testing process.
- Making the repository private does not guarantee that previously exposed data or copies are removed.
- For actual use, replace public JSON-based storage with a secure database and appropriate access controls.

## Features

- User registration and login with hashed passwords
- Family-member setup during registration
- Add and delete expenses with date, item, amount, and payer details
- Monthly and all-time spending summaries
- Dashboard charts and spending insights
- Receipt scanning using browser-based OCR
- Optional expense entry from scanned receipts
- Demo mode available at `/demo`
- Responsive interface for desktop and mobile screens

## Technology Stack

- Python 3.10+
- Flask
- Werkzeug
- Jinja2
- Chart.js
- Tesseract.js
- Google Fonts
- JSON for local development storage
- PostgreSQL for Render deployments

## Project Structure

```text
.
├── app.py
├── data.json
├── requirements.txt
├── schema.sql
├── static/
│   └── images/
│       └── FamEase.png
└── templates/
    ├── index.html
    ├── login.html
    └── register.html
```

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HackathonStoneHill-main
```

### 2. Create and Activate a Virtual Environment

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Set a unique Flask secret key before starting the application.

**macOS / Linux:**

```bash
export SECRET_KEY="replace-with-a-long-random-value"
```

**Windows PowerShell:**

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
```

Never commit real API keys, passwords, database credentials, or production secrets. Store sensitive configuration in environment variables.

### 5. Run the Application

```bash
python app.py
```

Open the following URL in your browser:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Demo Mode

Visit the following URL to access the dashboard with sample expenses:

[http://127.0.0.1:5000/demo](http://127.0.0.1:5000/demo)

Demo data is read-only. To use the application normally, create a new account through the registration page.

## Data Storage

FamEase uses different storage methods depending on the environment.

**Local Development**

- Uses `data.json` for storing users and expense information.
- Run the application from the repository root to ensure the file can be located correctly.

**Render Deployment**

- Uses PostgreSQL for persistent data storage.
- Configure `DATABASE_URL` and `SECRET_KEY` in the Render service's environment variables.
- The application refuses account and expense operations if Render is missing `DATABASE_URL`, rather than silently saving data to an ephemeral file.

The database table can be created by running `schema.sql` against your PostgreSQL database. The application also creates it automatically.

Existing accounts and expenses in your local `data.json` file are not automatically transferred to the deployment database. Back up the file and migrate any required data before switching users to the deployed application.

## Development Notes

- Run the application from the repository root to ensure local JSON storage works correctly.
- Chart.js, Tesseract.js, and Google Fonts are loaded through public CDNs.
- Receipt OCR runs directly in the browser.
- An internet connection is required to load Tesseract.js and other external CDN resources.

## License

No license has been specified for this project yet. A suitable license should be added before distributing or publishing the project.