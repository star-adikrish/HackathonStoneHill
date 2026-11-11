# FamEase persistent storage on Vercel

Vercel's function filesystem is temporary and is not a database. FamEase now uses PostgreSQL whenever `DATABASE_URL` is configured. Supabase PostgreSQL is a convenient option.

## 1. Create the database

1. Create a Supabase project.
2. Open **SQL Editor** and run the contents of `schema.sql`.
3. In **Project Settings → Database → Connection string**, choose the **Transaction pooler** connection string (URI), which is designed for serverless deployments.
4. Copy the URI and replace its password placeholder with your database password. Keep it private.

## 2. Add Vercel environment variables

In Vercel → your FamEase project → **Settings → Environment Variables**, add:

- `DATABASE_URL`: the PostgreSQL connection URI from Supabase.
- `SECRET_KEY`: a long, random, private value that stays the same between deployments.

Add the variables to **Production** (and Preview if you test preview deployments). Do not put these values in source code or commit them to GitHub.

## 3. Deploy

Redeploy the project after adding the variables. The first database request creates the FamEase state row if it does not exist.

## Important notes

- Local development still uses `data.json` when `DATABASE_URL` is not set.
- On Vercel, FamEase refuses to use local JSON storage. This prevents accounts from appearing to register and then disappearing on another serverless request.
- Existing accounts in a local `data.json` are not automatically copied to Supabase. Create test accounts again after deploying, or plan a one-time controlled migration before using real family data.
- This keeps the current FamEase data structure and expense/dashboard features. For a larger production app, split users and expenses into separate relational tables and add database-level constraints/transactions.
- Never commit real family expense data or database credentials.
