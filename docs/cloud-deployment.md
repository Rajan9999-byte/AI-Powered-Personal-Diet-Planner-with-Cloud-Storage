# Cloud deployment and free-tier migration

## Default container deployment

The repository includes a two-stage `Dockerfile`: Node compiles the React/Vite client, and Python runs Flask while serving `frontend/dist` and `/api/*`. Build and run locally first:

```bash
npm ci
npm run build
docker build -t dietly-planner .
docker run --rm -p 8080:8080 \
  -e SECRET_KEY='use-a-long-random-secret' \
  -e DATABASE_PATH='/app/data/dietplanner.sqlite3' \
  dietly-planner
```

For Cloud Run, the conceptual flow is:

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/dietly/dietly-planner
gcloud run deploy dietly-planner \
  --image REGION-docker.pkg.dev/PROJECT/dietly/dietly/dietly-planner \
  --region REGION \
  --allow-unauthenticated \
  --set-env-vars PORT=8080
```

Store `SECRET_KEY` with Secret Manager rather than `--set-env-vars` in a real deployment. Use `/api/health` as the unauthenticated health path.

## Important persistence limitation

The default container demonstrates the architecture but keeps SQLite and uploads on the local filesystem. Cloud Run filesystems are ephemeral and not shared across replicas, so this mode is suitable only for a single-instance course demonstration. Before enabling multiple replicas, replace the repository with Cloud SQL/Postgres/Firestore and replace the local adapter with Firebase Storage, Supabase Storage, S3, or platform object storage. This limitation is an intentional interview point, not a hidden behavior.

## Optional split deployment

A static frontend plus a server API is a good production shape:

1. Run `npm run build` and publish the contents of `frontend/dist` to Firebase Hosting, a CDN, or object storage.
2. Deploy the Flask API container separately.
3. Route `/api/*` to the container before the SPA catch-all.
4. Route `/assets/*` to static files with long-lived immutable caching.
5. Let the SPA catch-all handle only page routes such as `/dashboard`, `/profile`, `/plan`, and `/tracker`.
6. Keep personalized API responses `private, no-store`; never share cached user data.

The Webdev route shape is conceptually:

```json
{
  "routes": [
    { "path": "/api/*", "target": "server" },
    { "path": "/assets/*", "target": "static", "cache": "immutable" },
    { "path": "/*", "target": "static", "spaFallback": true }
  ]
}
```

## Firebase/Supabase mapping

- Local session auth → Firebase Authentication or the environment’s managed OAuth.
- `profiles` and `plans` → Firestore collections under the authenticated user ID, or Supabase Postgres tables with row-level security.
- `intake` → a per-user date document/collection or indexed SQL rows.
- `data/uploads` → Firebase Storage/Supabase Storage/S3, with a database metadata record.
- Flask routes → Firebase callable/HTTP functions or a Cloud Run API, preserving the frontend JSON contract.
- `backend/planner.py` → a server-only function or service; any LLM key remains in secret storage and is never shipped to React.

## Free-tier choices

For a student demo, use local SQLite and uploads, the deterministic planner, Docker locally, or a free-tier host that supports a small container. If a provider requests billing for a managed database or LLM, keep the local adapter and document the cloud boundary instead of committing a secret or blocking the project. Synthetic demo records are sufficient for screenshots and interviews.

## CI/CD outline

A GitHub Actions workflow can install Node/Python dependencies, run `pytest`, run `npm test`, run `npm run build`, and build the Docker image on every pull request. A protected main branch can publish the image after checks pass. Use repository/organization secrets for cloud credentials, never plaintext workflow values, and make deployment a separate environment with review gates.

## Operational checklist

- Use a strong runtime `SECRET_KEY` from secret management.
- Use a managed identity provider and HTTPS secure cookies.
- Move SQLite/uploads to shared durable services.
- Add database backups and retention rules.
- Add rate limiting, CSRF protection, dependency scanning, and structured logs.
- Monitor `/api/health`, error rate, latency, instance count, storage failures, and database connections.
- Confirm API routing before the SPA fallback so a missing API does not return `index.html`.
- Label generated content as general wellness education and keep model prompts/server keys private.
