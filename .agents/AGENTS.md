# Project Rules for Toarps Herrklubb

## Development Server
- Always run the Django development server on **port 1981**
- Start command: `./venv/bin/python manage.py runserver` (or `./venv/bin/python manage.py runserver 1981`)
- Access at: http://127.0.0.1:1981 (or https:// in HTTPS-enabled environments)

## HTTPS Security Standards
- Project enforces HTTPS standards (`SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_REFERRER_POLICY`) for encrypted transport.

## Git & Deployment Rules
- **Milestone-Only Commits (Anti-Noise Policy)**:
  - NEVER make micro-commits for intermediate styling/CSS/line tweaks.
  - Test and iterate freely in local DEV mode (`http://127.0.0.1:1981`).
  - Only commit when a full feature or milestone is completed and verified, using Conventional Commits (`feat:`, `fix:`, `style:`, `refactor:`).
- Always ask or wait for instruction before committing or updating the server!
- **Production Server**: `johansiedberg@192.168.86.35`
- **Server Project Path**: `/home/johansiedberg/Projects/Toarps_Herrklubb`
- **Deployment Procedure**:
  1. Commit and push local changes to `origin/main` on GitHub.
  2. Connect to the production server via SSH: `ssh johansiedberg@192.168.86.35`
  3. Run the automated deploy script:
     ```bash
     cd /home/johansiedberg/Projects/Toarps_Herrklubb && ./deploy.sh
     ```

## Distraction-Free Login Standard
- All login screens and entry points must remain 100% distraction-free authentication portals.
- NEVER display news banners, changelogs, version numbers, or update popups at login.

## Antigravity Agent Permission & Workflow Control Rules

### 1. UI/UX Modification & Gating Policy
- **Direct User Prompt for UI/UX**: If the user's prompt explicitly instructs the agent to perform UI/UX changes (e.g. "redesign banner", "adjust font color", "add icon spacing"), the agent MUST perform them directly without forcing an intermediate plan approval gate (unless an implementation plan was explicitly requested).
- **Collateral / Unrequested UI/UX Changes**: If the agent intends to modify UI/UX as part of a wider code change, backend feature addition, or system refactor (where the user did NOT explicitly request UI/UX changes), the agent MUST present a proposed plan detailing the UI/UX changes and obtain user confirmation (`request_feedback: true`) BEFORE touching UI templates, CSS, or styling files.

### 2. Implementation Plan & Goal Approval Gate
- **Mandatory Goal/Plan Review**: Whenever the user asks for a goal or implementation plan (or when planning mode is activated), the agent MUST ALWAYS stop, create/update `implementation_plan.md` with `request_feedback: true`, and await explicit user review and approval before executing any code changes or shell commands.

### 3. Tool Permission & Autonomous Command Execution
- **Turn Efficiency & Batching**: The agent MUST batch commands logically and minimize turn fragmentation to avoid triggering unnecessary approval prompts for trivial actions.
- **Autonomous Execution in Approved Plans**: Once an implementation plan is approved by the user, the agent should execute the planned steps autonomously without stopping for repetitive turn-by-turn confirmations.

## Icon & Emoji Visual Spacing Standard
- **Mandatory Visual Gap**: All icons (`<i class="...">`) and emojis (e.g. 🏆, ⚽, ⏱️, ✅, 🛡️, 🪣, ♠, ♣, ♦) MUST have a distinct visual gap of **minimum 5px–6px** (or two character spaces / flex gap) separating them from adjacent text elements.
- **No Text Touching**: Emojis and icons must NEVER directly touch alphanumeric text characters without explicit padding/margin or space delimiters.
- **Implementation Methods**:
  - **FontAwesome / SVG Icons**: Apply Bootstrap margin classes like `me-1.5` (6px) or `me-2` (8px), or wrapper class `.icon-gap` / `.gap-icon`.
  - **Flexbox Containers**: Wrap icons and text inside a container with `d-inline-flex align-items-center gap-2` (8px) or `gap-1.5` (6px).
  - **Inline Emoji Text**: Include an explicit non-breaking space `&nbsp;` or a physical space character when concatenating emoji strings in template variables or JS (e.g., `🏆 Event` NOT `🏆Event`).
  - **CSS Helpers**: Utility classes `.icon-gap` (adds `margin-right: 6px`) and `.emoji-gap` (adds `margin-right: 6px; display: inline-block`).

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
When colouring banners, badges, callouts, and status notification containers, ensure readable distinct fill/background + font/icon combinations following a monochromatic tonal contrast system.

### Color Mapping Specification Matrix
| Status Role | Token Level | Target Luminance | Surface (BG) | Border / Divider | Icon / Accent | Primary Text |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Success / Ready** | 50 – 100 / 950 | Light / Deep | Light: `#F0FDF4`<br>Dark: `#052E16` | Light: `#BBF7D0`<br>Dark: `#15803D` | Light: `#15803D`<br>Dark: `#DCFCE7` | Light: `#14532D`<br>Dark: `#DCFCE7` |
| **Warning / Pending** | 50 – 100 / 950 | Light / Deep | Light: `#FFFBEB`<br>Dark: `#451A03` | Light: `#FDE68A`<br>Dark: `#B45309` | Light: `#B45309`<br>Dark: `#FEF3C7` | Light: `#78350F`<br>Dark: `#FEF3C7` |
| **Danger / Error** | 50 – 100 / 950 | Light / Deep | Light: `#FEF2F2`<br>Dark: `#450A0A` | Light: `#FECACA`<br>Dark: `#B91C1C` | Light: `#B91C1C`<br>Dark: `#FEE2E2` | Light: `#7F1D1D`<br>Dark: `#FEE2E2` |
| **Info / Active** | 50 – 100 / 950 | Light / Deep | Light: `#EFF6FF`<br>Dark: `#172554` | Light: `#BFDBFE`<br>Dark: `#1D4ED8` | Light: `#1D4ED8`<br>Dark: `#DBEAFE` | Light: `#1E3A8A`<br>Dark: `#DBEAFE` |
| **Neutral / Slate** | 50 – 100 / 900 | Light / Deep | Light: `#F8FAFC`<br>Dark: `#0F172A` | Light: `#E2E8F0`<br>Dark: `#475569` | Light: `#475569`<br>Dark: `#E2E8F0` | Light: `#0F172A`<br>Dark: `#E2E8F0` |

### Core UI/UX Rules
- **WCAG Contrast Ratios**:
  - **Text**: Minimum **4.5:1** contrast ratio (WCAG AA) against banner surface (aim for **7:1** WCAG AAA).
  - **Icons & Boundaries**: Minimum **3.0:1** contrast against background.
- **Shared Hue Continuity**:
  - Never place pure neutral black (`#000000`) or raw un-paired vibrant colors (e.g., `#22C55E`) directly on a light pastel or deep dark background without proper tonal pairing. Tint dark text with 10–15% of background hue to create visual depth and prevent chromatic aberration.
- **Multi-Modal Signaling**:
  - Never rely on color alone to convey state. Every banner/badge must pair color with an explicit status icon (e.g., checkmark for success, shield for security, clock for pending) and descriptive text.
- **Dark Mode Inversion**:
  - Reverse polarity while desaturating backgrounds to prevent eye strain:
    - **Surface**: Deep tone (~10% lightness)
    - **Border**: Mid-dark tone (~35% lightness)
    - **Text & Icon**: Pale tint (~85–90% lightness)
