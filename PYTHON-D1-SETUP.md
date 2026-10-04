# Active Hire Solutions Test — Python Worker + D1

This adds a working contact enquiry form and a separate Python Cloudflare Worker API backed by a D1 database. It is intended for your **Test** site only. It does not connect to the production database or deploy anything automatically.

## Architecture

- Existing site: Cloudflare Pages (static HTML/CSS/JS)
- API: Cloudflare Python Worker in `backend/`
- Database: Cloudflare D1, binding name `DB`
- API routes: `GET /api/health` and `POST /api/contact`

## Before you start

1. Keep your production Active Hire Solutions project and database separate. Do not bind this Worker to a production database.
2. Install Node.js LTS, Git, and `uv` on your Windows PC. Cloudflare's Python Workers tooling also requires Node.js.
3. Extract this ZIP. The website files are in the `test/` directory. You can commit these files to the GitHub repository connected to your Test Pages project. Do not upload the `backend/` directory as if it were a static Pages Function; deploy it as a separate Worker as described below.

Official references:
- Python Workers: https://developers.cloudflare.com/workers/languages/python/
- Query D1 from Python: https://developers.cloudflare.com/d1/examples/query-d1-from-python-workers/
- D1 getting started: https://developers.cloudflare.com/d1/get-started/

## Step 1 — Create a separate D1 database

1. Sign in to the Cloudflare dashboard.
2. Open **Storage & databases → D1 SQL Database** (dashboard labels may vary).
3. Choose **Create database**.
4. Name it `active-hire-test-db` and create it.
5. Copy the database ID shown in the dashboard. Keep this database dedicated to Test.

## Step 2 — Configure the Worker

1. Open `backend/wrangler.jsonc` in a code editor.
2. Replace `REPLACE_WITH_YOUR_D1_DATABASE_ID` with the actual database ID.
3. Replace `https://YOUR-TEST-PAGES-DOMAIN.pages.dev` with the exact origin of your Test website, with no trailing slash. Example format: `https://your-test-project.pages.dev`.
4. Keep `binding` set to `DB`, and `database_name` set to `active-hire-test-db` unless you deliberately used another name.

## Step 3 — Install Python Worker tooling on Windows

Open PowerShell in the `backend` folder. Install Node.js LTS and `uv` first if not installed. Then run:

```powershell
uv sync
```

If `uv sync` reports that the project does not have a lock file, run:

```powershell
uv lock
uv sync
```

## Step 4 — Apply the database migration

From the `backend` folder, run:

```powershell
uv run pywrangler d1 migrations apply active-hire-test-db --remote
```

If the installed `pywrangler` version does not expose the D1 command, use Wrangler directly:

```powershell
npx wrangler d1 migrations apply active-hire-test-db --remote
```

Confirm the prompt to apply the migration. This creates the `enquiries` table.

## Step 5 — Test locally

From the `backend` folder:

```powershell
uv run pywrangler dev
```

Follow the local URL shown in the terminal. Note: the contact form on your deployed Pages site calls the deployed Worker, not localhost. For the live form test, continue to Step 7.

## Step 6 — Deploy the Worker

From the `backend` folder, run:

```powershell
uv run pywrangler deploy
```

Follow any Cloudflare login/authorization prompts. Copy the deployed `https://...workers.dev` URL printed by the command.

If your CLI reports that `pywrangler` is unavailable, check the current official Python Workers guide for the supported setup commands: https://developers.cloudflare.com/workers/languages/python/ .

## Step 7 — Connect the website form to the Worker

1. Open `assets/js/backend-config.js` in the website folder.
2. Replace `https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev` with the exact Worker URL from Step 6. Do not add `/api/contact` at the end.
3. Commit and push the website changes to the GitHub repository connected to the Test Pages project. Cloudflare Pages should rebuild automatically.
4. Visit `https://YOUR-TEST-PAGES-DOMAIN.pages.dev/contact/`.
5. Fill in the form and submit a test enquiry.
6. Visit `https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/api/health`. It should return JSON showing `ok: true` and `database: connected`.

## Step 8 — Verify the saved enquiry

In Cloudflare Dashboard → D1 → `active-hire-test-db` → Console, run:

```sql
SELECT id, name, email, enquiry_type, subject, created_at
FROM enquiries
ORDER BY id DESC
LIMIT 20;
```

Avoid sharing the result publicly; enquiries contain personal data.

## Troubleshooting

- **CORS / Origin not allowed:** `ALLOWED_ORIGIN` in `backend/wrangler.jsonc` must exactly match the Test Pages origin, including `https://` and without a trailing slash. Redeploy the Worker after changing it.
- **Database not available:** confirm the D1 database ID/name in `wrangler.jsonc`, and that the migration ran against the remote database.
- **Form says not connected:** check `assets/js/backend-config.js`; replace both `YOUR-WORKER` and `YOUR-SUBDOMAIN` placeholders.
- **Pages site doesn't update:** confirm you committed the updated website files to the exact GitHub repository and branch linked to Test Pages, then check the latest deployment in Cloudflare Pages.

## Current scope and security notes

- The public contact form can insert enquiries only; it has no public endpoint to list, edit, or delete enquiries.
- Input length and basic email validation are checked server-side. A hidden honeypot field helps deter simple bots but is not a complete spam defence.
- There is no admin dashboard, email notification, CAPTCHA, or rate limiting yet. Add these before relying on the form for high-volume production traffic.
- This first version does not accept CV/resume uploads. Add Cloudflare R2 with strict upload validation and access controls if you later want candidates to upload files.
- Do not add passwords, API tokens, or secrets to the website JavaScript or public GitHub repository.
