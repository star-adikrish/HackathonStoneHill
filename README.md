# FamEase

FamEase is a family budgeting and household planning application built with Flask. It brings receipt scanning, shared expense tracking, meal planning, to-do lists, and optional household-helper access into one responsive dashboard.
Its not only that but its a wonderful experience also as you can see the website is completly in Editoral styling and i like to keep it subtle with the off white background and the musturdy green buttons and with our Canva Logo it really gives good vibes to the website.

The website is supposed to help you in 

Tracking day to day expenses and also have an account where you can add your children and teach them how to save money on their wants and needs by tracking their spends

Meal planner a really big help for familys as everyone in the house has different craving and can't settle out for one thus if they create a timetable for what should be made on specific days it can stop arguments over different foods.

A TO-DO list is something which helps everyones from the different ranges on basis of age nowdays having a TO-DO list is quite important.

A househelp account must feel like a BIG HELP as you can tell your househelp what to do without even talking to them this helps people who may be outside when their househelp arrives 

ALL FEATURES can be used for various purposes and not only for their fixed purpose so feel free to explore the website

FAMEASE Is for the good of people so do not exploit it 
Hope you enjoy the website with editoral styling

## Live Website

The latest deployed version is available at:

**https://famease.onrender.com/**
You may view demo if run locally by adding  **/demo** to it IF U RUN LOCALLY

Also while checking on render it may take a few seconds to wake up


The deployed URL may change when the hosting configuration changes.

## Brief OF Features

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
## Demo mode uses sample expenses and is read-only. It does not save expense changes.

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
├── data.json              # local only; created/updated by the app and git-ignored
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

## Meal Planner and To-Do Storage

Meal plans and to-do items are stored in the current browser's local storage. They are not stored in the account database and do not synchronize across browsers or devices.

Clearing browser data removes saved meal plans and to-do items.

## Househelp Account

A household owner can create a separate meal-planner login from the **Househelp** tab.

- Choose a unique username
- Use a password of at least eight characters
- Share the credentials privately

The househelp account can access the meal planner only. Family expenses and other dashboard routes are restricted.

## AI USAGE
 
I used AI at different stages of the build sometimes to make small changes and sometimes for even adding stuff.
Less than 30% of my project is vibe coded.

Also used a AI to give me a base for the househelp account.

## Hope You Enjoy the website 

## ALSO though the data.json is uploaded all user data was for testing u will find no real expenses made my some random xyz.


Make good use of the website