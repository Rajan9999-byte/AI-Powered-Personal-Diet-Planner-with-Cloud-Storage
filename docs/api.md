# API contract

All browser requests are same-origin and use JSON unless an upload endpoint is receiving `multipart/form-data`. Protected endpoints require the local `dietly_session` cookie in the demo. Errors return `{ "error": "human-readable message" }` with a non-2xx status.

## Health and auth

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | No | Returns `{status, service, storage}`. |
| GET | `/api/auth/me` | No | Returns `{authenticated, user}`. |
| POST | `/api/auth/register` | No | Body `{name,email,password}`; creates a user and session. |
| POST | `/api/auth/login` | No | Body `{email,password}`; creates a session. |
| POST | `/api/auth/logout` | No | Clears the local session. |

Passwords are never returned. Passwords must be at least eight characters in the local demo.

## Profile and targets

`GET /api/profile` returns `{profile}` or `null`. `PUT /api/profile` accepts:

```json
{
  "name": "Demo Planner",
  "age": 24,
  "sex": "female",
  "height_cm": 165,
  "weight_kg": 62,
  "activity_level": "moderate",
  "dietary_preference": "vegetarian",
  "goal": "balanced",
  "allergies": ["nuts"],
  "cuisines": ["Indian"],
  "budget_per_day": 350,
  "timeline_weeks": 8
}
```

`POST /api/targets` accepts an optional profile body. If omitted, it uses the stored profile and returns:

```json
{
  "targets": {
    "bmr": 1370,
    "tdee": 2124,
    "calories": 2124,
    "macros": { "protein": 159, "carbs": 212, "fat": 71 }
  }
}
```

The calculation is a course-project implementation of Mifflin-St Jeor plus activity multipliers and a broad goal adjustment. It is not a clinical recommendation.

## Plans

`GET /api/plans` returns up to the 20 newest saved plans. `POST /api/plans` optionally accepts `{ "targets": ... }`, reads the stored profile, generates a deterministic rule-based fallback plan, persists it, and returns `{ "plan": ... }`.

Each plan contains `id`, `created_at`, `source`, `disclaimer`, `targets`, `meals`, `totals`, and `hydration`. Each meal contains a label, target calories, item portions, and macro totals. `GET /api/plans/<id>` is ownership-scoped.

## Foods and intake

`GET /api/foods` returns the server-side catalog used by the tracker. `GET /api/intake?date=YYYY-MM-DD` returns `{date, entries, totals}`. `POST /api/intake` accepts `{food_id, grams, date?}` and computes nutrition on the server. `DELETE /api/intake/<id>` removes only an entry owned by the authenticated user.

## Dashboard

`GET /api/dashboard` aggregates the current profile, calculated targets, newest plan, today’s totals, and recent plan metadata. The dashboard deliberately does not treat missing profile data as an error; the UI can guide the user to finish setup.

## Local object-storage simulation

`POST /api/storage/profile-photo` receives a multipart field named `file`. The adapter accepts JPEG, PNG, WEBP, or GIF files up to 3 MB, generates a random object key, stores bytes under `data/uploads/`, and records metadata. It returns an ownership-scoped `/api/storage/<upload_id>` URL.

`GET /api/storage/<upload_id>` streams the file only to the owning authenticated user. In a managed deployment, replace the adapter with a presigned upload flow and store the durable object key/URL in the database.
