# FollowUp Flow — Next Founders MVP

Small shops often receive customer inquiries across multiple chats and forget to follow up. FollowUp Flow puts those requests in one simple pipeline. 

## Run (Python 3.9+, no dependencies)

```bash
python app.py
```

Open http://localhost:8000. Run tests with `python -m unittest -v test_app.py`.

## Demonstrated features
- Capture customer/contact/request/potential USD value
- Persist inquiries in SQLite
- Move each inquiry from new → contacted → won/lost
- Show incoming volume, pending follow-ups and open opportunity value
- Export all inquiries as CSV
- Server validation and safe SQL parameters; user-provided strings rendered as text, not HTML

## Architecture
Single HTML/CSS/JS frontend → Python standard-library HTTP API → SQLite database (`leads.sqlite3`, generated locally). Endpoints: `GET/POST /api/inquiries`, `POST /api/inquiries/{id}/status`, `GET /api/export`.

## Business hypothesis (not validated)
Target: independent retail shops and service providers that handle orders by WhatsApp. Hypothetical pricing: free up to 25 leads/month; $9/month for unlimited leads and exports. Needs interviews, pricing validation and data protection before commercial use.

## Real limitations
Single-machine/local prototype. No login, multi-tenancy, integrations, automated follow-up, reminders, encryption-at-rest or access controls. Do not deploy publicly or enter real customer personal data. Scaling would require authentication, separate tenant data, managed database, rate limiting, retention rules and backup strategy. Currency fixed to USD for demo clarity.

## Contribution and proof
AI generated the initial implementation. Do not describe it as independently human-written code. To prove human competence, have each duo member implement and explain an unseen change without AI, document commit and tests, and record a supervised technical walkthrough. Credit each contributor accurately.
