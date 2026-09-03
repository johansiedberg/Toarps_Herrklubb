# Changelog - Toarps Herrklubb

All notable changes to the **Toarps Herrklubb** project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.1.1] - 2026-09-03

### 📸 Photo Archive Improvements & Fixes
- **Clickable Album Signature Photo**: Made album cover and signature photo cards clickable in the photo archive overview, navigating directly into the album.
- **Tagged Member Filtering Fix**: Fixed "Foton med mig" and member selection filters to strictly isolate photos where members are tagged, removing unwanted inclusion of non-tagged uploads.
- **Overview-to-Album Filter Forwarding**: Added member filtering to the photo archive overview with real-time tag counts, automatically forwarding and preserving the active filter when opening any album.
- **Interactive Tag Badges**: Lightbox tag toggling dynamically updates photo card badges in the background grid without requiring a page reload.

---

## [v1.1.0] - 2026-09-03

### 🚀 Features & Enhancements
- **📸 Photo Sharing Archive (Fotoarkiv)**:
  - Added dedicated `PhotoAlbum`, `Photo`, and `PhotoLike` models (`0006_photo_photoalbum_photo_album_photolike.py`).
  - Mobile-first multi-photo upload with iOS and Android camera support.
  - Member face-tagging interface with nickname selection chips.
  - Social photo liking (heart reactions) and automated high-res ZIP album archiving.
- **📅 Event Attendance & RSVP Flow**:
  - Direct attendance toggle (`Kommer` / `Kan inte`) and tracking for upcoming events (`0003`, `0004`).
  - Google Calendar integration with explicit busy flag (`trp=true`) in web template links.
- **👤 Member Nicknames & Personalization**:
  - Integrated `UserProfile.nickname` (`0005_userprofile_nickname.py`) and hub greeting standard (`Välkommen, {{ user_nickname }}!`).

---

## [v1.0.0] - 2026-08-27

### 🚀 Features & Architecture
- Initial production release of Toarps Herrklubb social hub and decoupled SSO platform.
- Bound to Port 8981 (HTTPS Port 1981 via Caddy proxy).
- Systemd + Gunicorn production service management integration (`toarps-herrklubb.service`).
- DEV -> PRD release management and automated changelog tracking.
