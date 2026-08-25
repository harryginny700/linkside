# API Contracts — Reklam Sitesi (kara8 clone)

## Auth (JWT, username/password)
- POST /api/auth/login  {username, password} -> {token}
- GET  /api/auth/me     (Bearer) -> {username}
- Seed admin: admin / admin123 (pbkdf2_sha256 hashed in DB)

## Banners
Model: {id, section("top"|"grid"), image, url, title, orient, span, order, active, clicks}
- GET    /api/banners             -> active banners (public, ordered)
- GET    /api/banners?all=true    -> all banners (auth)
- POST   /api/banners             (auth) create
- PUT    /api/banners/{id}        (auth) update
- DELETE /api/banners/{id}        (auth) delete
- POST   /api/banners/reorder     (auth) {ids:[...]} set order
- POST   /api/banners/{id}/click  (public) +1 click, +1 daily click

## Settings
Model: {siteTitle, gridColumns, ageGateEnabled}
- GET /api/settings        (public)
- PUT /api/settings        (auth)

## Views & Stats
- POST /api/view                 (public) +1 daily view
- GET  /api/stats/overview       (auth) {totalViews, totalClicks, activeBanners, ctr}
- GET  /api/stats/daily          (auth) [{date, views, clicks}] last 14 days

## Upload
- POST /api/upload  (auth, multipart file) -> {url}  saved to /app/backend/uploads, served at /api/uploads/{name}

## Frontend integration
- Replace src/mock.js localStorage functions with axios calls to `${REACT_APP_BACKEND_URL}/api/...`
- Create src/api.js with all endpoints. Keep function names similar so components change minimally.
- Home: fetch settings + active banners; POST /view on mount; POST click on banner click.
- Admin: login stores JWT in localStorage; all admin calls send Bearer header.
- Mocked-in-frontend that becomes real: banners, settings, stats, auth, uploads.
