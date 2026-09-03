# Toarps Herrklubb

Toarps Herrklubb is a centralized social planning and coordination platform customized for the 11 original members of the club. The platform's primary purpose is to manage social event calendars, identify mutual availability, track shared goals via a custom bucket list voting system, and offer secure Single Sign-On (SSO) integration with the standalone football predictions platform.

---

## 1. Core Objectives & Features

The platform focuses on four main pillars of interaction:

### 📅 Hinderkalender & Golden Weekends
* **Availability Heatmap:** Members log periods of unavailability (dates and optional descriptions) directly on a centralized calendar.
* **Golden Weekend Scanner:** The platform automatically scans upcoming weekend dates to identify "Golden Weekends" — three-day weekend blocks (Friday through Sunday) where all 11 members are fully available.
* **Event Coordinators:** Members can schedule next events, assign locations, set details, track participant RSVPs, and volunteer as event coordinators.

### 🪣 Herrklubbens Bucket List
* **Marker Voting System:** Members organize shared bucket list items by category and cast votes using distinct Pokermarkers:
  * **Svart Marker:** Highest priority (adds 100 points)
  * **Grön Marker:** Medium priority (adds 50 points)
  * **Röd Marker:** Standard support (adds 25 points)
* **Högsta Dröm (Highest Dream):** Each member can select exactly one active bucket item as their ultimate dream.
* **Planning Promotion:** Any bucket list proposal that receives at least 6 out of 11 votes is automatically promoted from the "Idébanken" queue to "Planerade Aktiviteter."
* **Archiving & Completion:** Completing a bucket item archives the record and automatically frees up members' markers to be spent on other active proposals.

### 📸 Fotoarkiv & Delade Minnen
* **Chronological Photo Albums:** Dedicated event photo albums (`PhotoAlbum`) with cover photos, date tagging, and descriptions.
* **Mobile-First Photo Upload:** Direct upload from iOS and Android devices supporting high-res photography and automatic client-side / backend format handling.
* **Member Tagging & Social Reactions:** Tag club members in specific photos with quick nickname chips, toggle photo likes (heart reactions), and download entire albums as high-res ZIP archives.

### 🔑 Cryptographic Single Sign-On (SSO)
* **Credentials-Free Prediction Entry:** The tournament prediction features have been fully decoupled into the standalone **Prediction Engine** (running on port `2028`).
* **Redirection Flow:** From the Toarps Herrklubb Hub, members can click "Mästerskapstips" to access the predictions page. The platform generates a short-lived (60-second), cryptographically signed SSO token (via Django's `TimestampSigner` and a shared secret key) and redirects the user to the Prediction Engine. The engine verifies the signature, registers the user if they do not yet exist, and logs them in immediately.

---

## 2. Project Architecture & Directories

The codebase is organized under a standard Django structure, following the rename from `tournament` to `herrklubb`:

```text
Toarps_Herrklubb/
│
├── core/
│   ├── settings.py           # Contains global settings, database configuration, and SSO secret
│   ├── urls.py               # Root url routing pointing to herrklubb app
│   └── wsgi.py / asgi.py     # Deployment entry points
│
├── templates/
│   ├── admin/                # Overrides for Django administration panels
│   └── herrklubb/            # User-facing Swedish templates
│       ├── base.html         # Base site layouts and navigation bar
│       ├── hub.html          # Entry hub directing to Social Hub or Predictions
│       ├── herrklubb.html    # The Bucket list, voting panel, and events coordinator
│       ├── calendar.html     # Hinderkalender visual heat map and Golden Weekends
│       ├── photo_gallery.html # Photo albums archive overview & album creation
│       ├── album_detail.html # Photo album gallery, mobile upload, and face tagging
│       └── login.html        # Secure entry page
│
├── herrklubb/
│   ├── management/           # App-specific management commands
│   │   ├── commands/
│   │   │   ├── runserver.py  # Forces server to run on port 1981 by default
│   │   │   ├── seed_members.py
│   │   │   └── seed_herrklubb_bucketlist.py
│   ├── static/
│   │   └── herrklubb/        # Local static stylesheets, images (chips/backdrops), and scripts
│   ├── admin.py              # Social models registration (UserProfile, Bucket items, etc.)
│   ├── apps.py               # App configuration (HerrklubbConfig)
│   ├── forms.py              # Extended user authentication form (email lookup support)
│   ├── models.py             # Relational schema for social hub data (UserProfile, Events, Bucket, PhotoAlbum, Photo, PhotoLike)
│   ├── tests.py              # Test suite for events and marker votes logic
│   ├── urls.py               # View endpoints routing
│   └── views.py              # Event calendars logic, bucket voting, photo archives, and SSO signer
│
├── media/                    # User-uploaded photo albums and high-res event photography
├── db.sqlite3                # Local SQLite database
├── manage.py                 # Django command-line utility
└── requirements.txt          # Python packages listing
```

---

## 3. Development Conventions

To preserve readability and code quality, all modifications must adhere to the following developer rules:

* **Language Rules:**
  * **Code & Comments:** Written exclusively in **English**.
  * **User Interface & Output:** Written exclusively in **Swedish** (to align with the childhood friends target group).
* **Port Conventions:**
* **Toarps Herrklubb:** Always runs on port `1981` (can be launched with `./venv/bin/python manage.py runserver 1981`).
  * Access at: `https://127.0.0.1:1981` (or `http://` in local dev)
  * **Prediction Engine:** Always runs on port `2028` (can be launched with `./venv/bin/python manage.py runserver 2028`).
  * Access at: `https://127.0.0.1:2028` (or `http://` in local dev)
* **HTTPS Security:** Both projects enforce HTTPS standards in production (`SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_REFERRER_POLICY`). SSO redirects dynamically use `https://` when behind a TLS-terminating proxy.
* **Database Migrations:**
  Always apply pending migrations after pulling code or modifying models:
  `./venv/bin/python manage.py migrate`

* **Database Rebuilding:**
  To reset and seed the database environment clean:
  1. Delete `db.sqlite3`.
  2. Run migration compilation: `python manage.py makemigrations herrklubb` and `python manage.py migrate`.
  3. Run seeders:
     * `python manage.py seed_members`
     * `python manage.py seed_herrklubb_bucketlist`
* **Antigravity Agent Permission & Workflow Control Rules:**
  * **Direct UI/UX Execution**: When the user explicitly requests UI/UX changes, the agent executes them directly without intermediate plan gating.
  * **Collateral UI/UX Review Gate**: When UI/UX modifications are part of a wider code feature/refactor (not explicitly requested as UI/UX by the user), the agent MUST present a proposed plan detailing the UI changes and await user confirmation before modifying UI files.
  * **Mandatory Plan Review**: Any prompt requesting a goal or implementation plan requires creating `implementation_plan.md`, setting `request_feedback: true`, and waiting for explicit user approval before execution.
  * **Autonomous Command Execution**: Once a plan is approved by the user, tool calls and background operations execute autonomously in batched sequences without turn-by-turn permission prompts.
* **Icon & Emoji Visual Spacing Standard:**
  * All icons (`<i class="...">`) and emojis (e.g. 🏆, ⚽, ⏱️, ✅, 🛡️, 🪣, ♠, ♣, ♦) MUST maintain a minimum **5px–6px** visual gap (or two space units / flex gap) from adjacent text elements.
  * Emojis and icons must NEVER directly touch text characters without explicit padding/margin or space delimiters.
  * Use utility classes `.icon-gap`, `.emoji-gap`, `me-1.5`, `me-2`, or `d-inline-flex align-items-center gap-2`.
* **Monochromatic Tonal Contrast & Legibility System:**
  * All banners, cards, badges, and alert notifications use strict monochromatic tonal contrast token sets for maximum readability (minimum 4.5:1 text WCAG AA contrast ratio).
  * Status states (Success, Warning, Danger, Info, Neutral) utilize paired background, border, text, and icon tokens in both Light and Dark mode.
  * Dark mode uses reversed polarity with deep tone surfaces (~10% lightness), mid-dark borders (~35% lightness), and pale tint text/icons (~85–90% lightness) to avoid glare and chromatic aberration.
  * Multi-modal signaling pairs visual color with explicit status icons and descriptive text labels.

---

## 4. Deployment & Production Operations

* **Production Host**: `johansiedberg@192.168.86.35`
* **Server Project Path**: `/home/johansiedberg/Projects/Toarps_Herrklubb`
* **Updating Production Server**:
  ```bash
  ssh johansiedberg@192.168.86.35
  cd /home/johansiedberg/Projects/Toarps_Herrklubb
  git pull origin main
  ./venv/bin/python manage.py migrate
  pkill -f "8981" && nohup ./venv/bin/python manage.py runserver 127.0.0.1:8981 > runserver.log 2>&1 &
  ```

* **Git Commit & Deployment Rules**:
  * Always confirm and verify with the team before executing production commits and server updates.