# Project Rules for Toarps Herrklubb

## Development Server
- Always run the Django development server on **port 1981**
- Start command: `./venv/bin/python manage.py runserver` (or `./venv/bin/python manage.py runserver 1981`)
- Access at: http://127.0.0.1:1981 (or https:// in HTTPS-enabled environments)

## HTTPS Security Standards
- Project enforces HTTPS standards (`SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_REFERRER_POLICY`) for encrypted transport.


## Git & Deployment Rules
- Always ask or wait for instruction before committing or updating the server!
- **Production Server**: `johansiedberg@192.168.86.35`
- **Server Project Path**: `/home/johansiedberg/Projects/Toarps_Herrklubb`
- **Deployment Procedure**:
  1. Commit and push local changes to `origin/main` on GitHub.
  2. Connect to the production server via SSH: `ssh johansiedberg@192.168.86.35`
  3. Navigate to the project root directory: `cd /home/johansiedberg/Projects/Toarps_Herrklubb`
  4. Pull the latest commits: `git pull origin main`
  5. Apply any database migrations: `./venv/bin/python manage.py migrate`
  6. If needed, restart server process:
     ```bash
     pkill -f "8981" && nohup ./venv/bin/python manage.py runserver 127.0.0.1:8981 > runserver.log 2>&1 &
     ```


## Suggested Events & Bucket List UI Layout Standards
- **Vertical Stack Structure**:
  - **Top Actions & Points**: Floating top-right badge for total point value (`Värde: XX p`), vote fraction (`X/11`), and quick action buttons (Edit ✏️ & Complete ✔️).
  - **Line 1 (Category & Rank)**: `.badge-category` pill with optional `#Rank` medal/number.
  - **Line 2 (Name / Title)**: Bold title with optional "Planerad" status pill if linked to the upcoming event.
  - **Line 3 (Description)**: Italicized secondary description text.
  - **Line 4 & 5 (Bucket / Black / Green / Red)**: Horizontal row of all 4 markers (🪣 Bucket, ♠ Black 100, ♣ Green 50, ♦ Red 25) with their vote counts centered below (`# / # / # / #`) and clean spacing (`mt-2`).
- **Badge Styling**:
  - Use `.badge-category` for category chips.
  - Use `.badge-tonal-gold` for value badges.




## Monochromatic Tonal Contrast & Legibility Guidelines
When colouring banners, badges, and status notification containers, ensure readable distinct fill/background + font/icon combinations following a monochromatic tonal contrast system.

### Color Mapping Specification
| Role | Token Level | Target Luminance | Purpose / Usage | Example (Green Success Light Mode) | Example (Green Success Dark Mode) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Surface (BG)** | 50 – 100 / 950 | Light (92% – 97%) / Deep (~10%) | Low visual noise; keeps screen scannable | `#F0FDF4` (Green-50) | `#052E16` (Green-950) |
| **Border / Divider** | 200 – 300 / 800 | Mid-Light (75% – 85%) / Mid-Dark | Defines container boundary | `#BBF7D0` (Green-200) | `#15803D` (Green-700/800) |
| **Icon / Accent** | 600 – 700 / 100-200 | Deep (35% – 45%) / Pale tint | High visual weight status indicator | `#15803D` (Green-700) | `#DCFCE7` (Green-100) |
| **Primary Text** | 800 – 900 / 100-200 | Very Dark (15% – 25%) / Pale tint | Maximum contrast & legibility | `#14532D` (Green-900) | `#DCFCE7` (Green-100) |

### Core UI/UX Rules
- **WCAG Contrast Ratios**:
  - **Text**: Minimum **4.5:1** contrast ratio (WCAG AA) against banner surface (aim for **7:1** WCAG AAA).
  - **Icons & Boundaries**: Minimum **3.0:1** contrast against background.
- **Shared Hue Continuity**:
  - Never place pure neutral black (`#000000`) or mid-tone vibrant colors (e.g., `#22C55E`) directly on a light pastel or deep dark background without proper tonal pairing. Tint dark text with 10–15% of background hue to create visual depth and prevent chromatic aberration.
- **Multi-Modal Signaling**:
  - Never rely on color alone to convey state. Every banner/badge must pair color with an explicit status icon (e.g., checkmark for success, shield for security) and descriptive text.
- **Dark Mode Inversion**:
  - Reverse polarity while desaturating backgrounds to prevent eye strain:
    - **Surface**: Deep tone (`#052E16` / Green-950, ~10% lightness)
    - **Border**: Mid-dark tone (`#15803D` / Green-700/800)
    - **Text & Icon**: Pale tint (`#DCFCE7` / Green-100, ~85–90% lightness)


