# Putting the app online

This puts the bookkeeping app on the internet so several people can log in and work on the
same data, with changes showing for everyone straight away. Everything here uses free plans.

| Piece | What it does | Cost |
|---|---|---|
| **Supabase** | Database, login, live updates | Free plan |
| **Vercel** | Hosts the web page | Free (Hobby) plan |
| **Google Cloud** | "Sign in with Google" | Free |
| **Brevo** (optional) | Sends login-code emails | Free plan (300 emails/day) |

It takes about 30–45 minutes. Do the steps in order.

---

## 1. Create the Supabase project

1. Sign up at [supabase.com](https://supabase.com) and click **New project**.
2. Pick a name (for example `trioagents`), set a database password and save it somewhere safe.
   For **Region**, choose one close to Israel, such as **Central EU (Frankfurt)**.
3. Wait a minute or two for the project to be created.

## 2. Create the tables and security rules

1. In the project, open **SQL Editor** → **New query**.
2. Paste the whole contents of [`supabase/schema.sql`](../supabase/schema.sql) and click **Run**.
   You should see "Success. No rows returned".

This creates:
- the user list with **approved** and **admin** flags;
- the data table;
- the rules that block anyone who isn't logged in and approved;
- live updates.

**The first person to log in becomes the admin automatically.** Make sure that's you (step 8).

## 3. Connect the app to Supabase

1. In Supabase, click **Connect** at the top (or **Project Settings → API Keys**).
2. Copy:
   - the **Project URL**, which looks like `https://abcdefghijkl.supabase.co`;
   - the **Publishable key** (`sb_publishable_...`). On older projects it's called the **anon public** key.
3. Put them in [`app/config.js`](../app/config.js):
   ```js
   supabaseUrl: 'https://abcdefghijkl.supabase.co',
   supabaseKey: 'sb_publishable_...',
   ```
   Commit and push.

These two values are meant to be public. The login and the database rules protect the data.
**Never use the `secret` or `service_role` key here.** That key bypasses all the rules.

## 4. Put the site on Vercel

1. Sign up at [vercel.com](https://vercel.com) with your GitHub account.
2. **Add New → Project** and import the `TrioAgents` repository.
3. On the setup screen:
   - **Root Directory:** click **Edit** and choose `app`.
   - **Framework Preset:** `Other`.
   - Leave the build settings empty. There is nothing to build.
4. Click **Deploy**. You get an address like `https://trioagents.vercel.app`.

Vercel publishes the `main` branch. Every push to `main` updates the site within a minute.

## 5. Tell Supabase your site's address

In Supabase: **Authentication → URL Configuration**.

- **Site URL:** your Vercel address, for example `https://trioagents.vercel.app`.
- **Redirect URLs:** add `https://trioagents.vercel.app/**`.

Without this step, Google login and email links send people to the wrong place.

## 6. Sign in with Google

**In Google Cloud:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project (any name).
2. Open **Google Auth Platform** (in older consoles, **APIs & Services → OAuth consent screen**):
   - **Branding:** app name (for example "הנהלת חשבונות"), your email as support and contact email.
   - **Audience:** **External**. Then click **Publish app**.
     If you skip this, only people you list as "test users" can log in.
     The app only asks for name and email, so Google doesn't need to review it.
3. **Clients → Create client → Web application**:
   - **Authorized JavaScript origins:** `https://trioagents.vercel.app`
   - **Authorized redirect URIs:** `https://<your-project>.supabase.co/auth/v1/callback`.
     Supabase shows this exact address on its Google provider page.
4. Copy the **Client ID** and **Client secret**.

**In Supabase:** **Authentication → Sign In / Providers → Google**. Turn it on and paste the
Client ID and Client secret. Save.

## 7. Login by email code (optional but recommended)

This is for users without a Google account.

### 7a. Use a real email sender

Supabase's built-in email is for testing only. It sends just a couple of emails an hour, and
only to members of your Supabase team. To send codes to your users, connect a free sender. Brevo is
the simplest because it doesn't need your own domain:

1. Sign up at [brevo.com](https://www.brevo.com) (free plan).
2. **Senders, Domains & Dedicated IPs → Senders** → add and verify the address emails should come from.
3. **SMTP & API → SMTP** → note the server, port, login, and create an **SMTP key**.
4. In Supabase: **Authentication → Emails → SMTP Settings** → **Enable custom SMTP**:
   - Sender email: the address you verified.
   - Sender name: for example "הנהלת חשבונות".
   - Host `smtp-relay.brevo.com`, port `587`, username = your Brevo SMTP login, password = the SMTP key.
5. Still in Supabase, **Authentication → Rate Limits**: raise "emails per hour" to around 30.

### 7b. Put the code in the email

The app asks users to type the code from the email. In Supabase,
**Authentication → Emails → Templates**, edit **both** "Magic Link" and "Confirm signup" so they contain the code.
For example:

```html
<h2>קוד כניסה</h2>
<p>הקוד שלך: <strong style="font-size:24px">{{ .Token }}</strong></p>
<p>או לחצו כאן: <a href="{{ .ConfirmationURL }}">כניסה</a></p>
```

If you don't want email login at all, set `loginWithEmail: false` in `app/config.js` and skip step 7.

## 8. First login: become the admin

1. Open your Vercel address and log in. **You must be the first person to log in.**
2. You go straight in as the admin.
3. If you already have data in the old version, use **ייצוא וגיבוי → הורדת גיבוי (JSON)** there,
   then **שחזור מגיבוי** in the new site to load it.

## 9. Add your users

1. Send the site address to your 4 users.
2. They log in with Google or email and see "ממתין לאישור".
3. You click **ניהול משתמשים** (top of the page), then **אישור** next to each name.
   Their screen opens by itself within about 20 seconds.

You can later remove access (**ביטול גישה**), make someone an admin, or remove them.
Removing access takes effect immediately in the database.

---

## Good to know

- **Staying logged in:** users stay logged in on each device until they press **התנתקות**.
- **iPhone:** works in Safari with Google or email login. To make it feel like an app, use
  Share → **Add to Home Screen**.
- **Sign in with Apple** is not included. Apple requires a paid developer account ($99/year).
- **Pausing:** free Supabase projects pause after 7 days without any use. The GitHub workflow
  `.github/workflows/keep-supabase-awake.yml` pings the database every 3 days to prevent this, once
  `app/config.js` has your details and the workflow is on `main`. If it does pause, open the project in
  the Supabase dashboard and click **Restore**. No data is lost.
- **Backups:** the free plan has no automatic backups. Download **הורדת גיבוי (JSON)** regularly
  (for example monthly) and keep it somewhere safe.
- **Two people editing the same record at the same moment:** the last save wins.
  Different records never conflict.
- **Vercel Hobby plan** terms are for non-commercial use. If that becomes a problem, the same
  `app` folder can be hosted on Cloudflare Pages or Netlify without code changes.
