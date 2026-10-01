# Personal Notes Workspace

Streamlit + Supabase personal notes app with notes CRUD, search, starred notes/passwords, one-line-per-todo notes, file upload/view/download, encrypted password manager, app lock, and storage dashboard.

## Setup
1. Create a Supabase project.
2. Run `supabase/schema.sql` in Supabase SQL Editor.
3. `python -m venv .venv && source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set `SUPABASE_URL` and the server-side `SUPABASE_SERVICE_ROLE_KEY`.
6. Generate password hash: `python -m app.setup_password` and put it in `APP_PASSWORD_HASH`.
7. Generate a stable salt once: `python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(16)).decode())"` and put it in `APP_PASSWORD_SALT`. Do not change it after saving vault entries.
8. Run `streamlit run app.py`.

Never commit `.env` or expose the Supabase service-role key client-side. For deployment use Streamlit secrets.
