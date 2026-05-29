# Sankalpa Interiors Kanban — Deployment Guide
## GitHub Pages + Firebase Firestore + Google Sign-In

*(Updated for the current Firebase Console UI — May 2026)*

---

## What you get

| Layer | What it does |
|---|---|
| **GitHub Pages** | Free HTTPS hosting at `yourname.github.io/sankalpa` |
| **Firebase Firestore** | Real-time cloud database — changes sync across all devices instantly |
| **Google Sign-In** | Each family member logs in with their own Google account |
| **Email allowlist** | Only the emails you approve can open the board |

---

## STEP 1 — Create the Firebase project

1. Go to **https://console.firebase.google.com**
2. Click **"Create a project"** (or **"Add project"**)
3. Enter a name: `sankalpa-interiors` → Continue
4. On the Google Analytics screen, toggle it **OFF** (not needed) → **Create project**
5. Wait ~30 seconds → **Continue**

> **Note on the new UI:** Firebase now sometimes opens with a "Gemini in Firebase" / "App Hosting" landing view. Ignore those. Use the **left sidebar** to navigate — that's where Firestore, Authentication, and Project Settings live.

---

## STEP 2 — Register a Web App (this is the step that moved)

In the **current UI**, the web-app button is on the **Project Overview** page, not inside Settings.

1. Click **"Project Overview"** at the very top of the left sidebar (the home icon)
2. On the main panel you'll see a row of icons to "add an app": **iOS · Android · Web `</>` · Unity · Flutter**
3. Click the **Web icon `</>`**

   *If you don't see the icons:* click the ⚙️ gear next to "Project Overview" → **Project settings** → scroll down to **"Your apps"** → click the **`</>`** button there. Both paths lead to the same place.

4. App nickname: `sankalpa-web`
5. **Do NOT** tick "Firebase Hosting" (we're using GitHub Pages) → click **Register app**
6. The next screen shows your **`firebaseConfig`** object. Copy these six values:
   ```
   apiKey, authDomain, projectId, storageBucket, messagingSenderId, appId
   ```
   *(You can always retrieve these later from ⚙️ → Project settings → Your apps.)*
7. Click **Continue to console**

> **Heads-up:** `storageBucket` in new projects now ends in **`.firebasestorage.app`** (older ones used `.appspot.com`). Copy whatever your console shows — don't hand-edit it.

---

## STEP 3 — Enable Firestore

1. Left sidebar → **Build → Firestore Database**
2. Click **"Create database"**
3. **Location**: pick `asia-south1 (Mumbai)` → Next
4. **Rules**: choose **"Start in test mode"** for now → **Create**
   *(We'll lock it down in Step 5.)*

---

## STEP 4 — Enable Google Sign-In

1. Left sidebar → **Build → Authentication**
2. Click **"Get started"**
3. Go to the **"Sign-in method"** tab
4. Under **"Additional providers"**, click **Google**
5. Toggle **Enable**
6. Set a **"Project support email"** (pick your own email from the dropdown)
7. Click **Save**

---

## STEP 5 — Lock down Firestore Security Rules

Go back to **Firestore Database → Rules** tab. Replace everything with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /kanban_cards/{docId} {
      // Only signed-in users whose email is in the allowlist can read/write
      allow read, write: if request.auth != null
        && request.auth.token.email in [
          "soumyo@example.com"
          // , "dona@example.com"
          // , "baba@example.com"
        ];
    }
  }
}
```

Replace the emails with your family's real Gmail addresses. Click **Publish**.

> This is the real security layer. Even though the Firebase API key is visible in your page source (that's normal and expected for web apps), nobody can read or write your data unless they sign in with one of these exact Google accounts.

---

## STEP 6 — Edit the HTML file

Open `sankalpa-kanban.html` in any text editor. Near the top, fill in **two** blocks:

### a) Firebase config (from Step 2)
```js
const FIREBASE_CONFIG = {
  apiKey:            "AIzaSy...",
  authDomain:        "sankalpa-interiors.firebaseapp.com",
  projectId:         "sankalpa-interiors",
  storageBucket:     "sankalpa-interiors.firebasestorage.app",
  messagingSenderId: "123456789",
  appId:             "1:123456789:web:abc123"
};
```

### b) Email allowlist (the same emails as in your rules)
```js
const ALLOWED_EMAILS = [
  "soumyo@example.com",
  "dona@example.com",
];
```

Save the file.

---

## STEP 7 — Publish to GitHub Pages

### Via GitHub website (no command line)
1. Go to **https://github.com/new**
2. Repository name: `sankalpa` → set to **Private** → **Create repository**
3. Click **"uploading an existing file"**
4. Drag in `sankalpa-kanban.html`, then **rename it to `index.html`**
5. **Commit changes**
6. Repo **Settings → Pages**
7. **Source**: Deploy from a branch · Branch: `main` · Folder: `/ (root)` → **Save**
8. Wait ~2 min. Your site is live at:
   **`https://YOUR_USERNAME.github.io/sankalpa/`**

### Via Git command line (alternative)
```bash
git init sankalpa && cd sankalpa
cp /path/to/sankalpa-kanban.html index.html
git add index.html && git commit -m "Initial deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/sankalpa.git
git push -u origin main
# then enable Pages in Settings → Pages
```

---

## STEP 8 — Authorise your GitHub Pages domain (important!)

Google Sign-In popups are blocked on unknown domains. You must whitelist your Pages URL:

1. Firebase Console → **Authentication → Settings** tab
2. Scroll to **"Authorized domains"**
3. Click **"Add domain"**
4. Enter exactly: `YOUR_USERNAME.github.io`
5. Save

*(`localhost` is already authorised, so testing on your machine works out of the box.)*

---

## STEP 9 — Test

1. Open `https://YOUR_USERNAME.github.io/sankalpa/`
2. Click **Sign in with Google** → choose your account
3. Board loads with all tasks; the seed data auto-populates on first run
4. Open the same URL on your phone, sign in → changes sync live between devices

---

## Security summary

| Threat | Protection |
|---|---|
| Stranger finds the URL | Sees only a Google Sign-In button — no data visible |
| Stranger signs in with their own Google account | Blocked by the email allowlist (both in-app and in Firestore rules) |
| Someone reads the page source & copies the API key | Useless without an allowlisted Google login — Firestore rules reject them |
| GitHub repo discovery | Repo is Private |

### Why the API key being visible is OK
Firebase web API keys are **public identifiers, not secrets** — they only tell the browser which project to talk to. Your actual security is the **Firestore Rules + Google Auth** combination. This is the standard, documented Firebase web model.

---

## Adding family members later

To give someone access you must add their email in **two** places:
1. `ALLOWED_EMAILS` in `index.html` (then push the change to GitHub)
2. The `allow read, write` list in your Firestore Rules (then Publish)

Both must match. Then they just sign in with that Google account.

---

## Updating tasks or features later

- **GitHub website:** open `index.html` → pencil icon → edit → commit
- **Git:** `git add index.html && git commit -m "Update" && git push`

GitHub Pages redeploys automatically within ~60 seconds.

---

## Quick troubleshooting

| Symptom | Fix |
|---|---|
| "auth/unauthorized-domain" | Do Step 8 — add your `.github.io` domain in Authentication → Settings |
| Sign-in popup closes instantly | Allow popups for the site; try again |
| "Missing or insufficient permissions" | Your email isn't in the Firestore Rules allowlist (Step 5) |
| Board is empty / red sync dot | Open browser console (F12) → read the Firestore error; usually a rules or config typo |
| Config "missing" message on login | The `FIREBASE_CONFIG` values weren't filled in (Step 6a) |
