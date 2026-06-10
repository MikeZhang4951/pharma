# Payout Curve Designer

A dependency-free, browser-based sales incentive modeling tool. The application lets compensation planners reshape TRx and NRx payout curves and immediately see the effect on territory-level payouts, budget utilization, and payout distribution.

## What the application does

- Displays separate editable TRx and NRx payout curves, plus a weighted combined view.
- Supports dragging curve points, editing point coordinates, and adding or removing points.
- Calculates quarterly territory attainment, payout percentages, payouts, budget variance, engagement, and other summary statistics.
- Treats TRx and NRx goals/actuals as prescription volumes and displays them without currency formatting.
- Models TRx and NRx national payout with normalized attainment scenarios as columns and plan-summary metrics as selectable rows, plus typed hypothetical TRx/NRx inputs for the combined national summary.
- Shows a configurable histogram of territory payout percentages.
- Supports sorting territory results by payout percentage.
- Imports tab-separated, CSV, or JSON territory data and provides a sample download.
- Runs entirely in the browser; no application server, database, or API is required.

## Repository structure

| Path | Purpose |
| --- | --- |
| `index.html` | Core user interface, payout calculations, charts, and import/export logic. |
| `national-summary.css` | Styles for the normalized national summary extension. |
| `national-summary.js` | National normalization controls, calculations, and summary rendering. |
| `territories.json` | Seed territory data used to generate deterministic quarterly demo data. |
| `.github/workflows/deploy-pages.yml` | Validates and deploys the static files to GitHub Pages. |

## Run locally

Because the page loads `territories.json` with `fetch`, serve the directory over HTTP rather than opening `index.html` directly:

```bash
python3 -m http.server 8080
```

Then open <http://localhost:8080/>.

## GitHub Pages deployment

The repository deploys automatically from the `master` branch with GitHub Actions.

### One-time repository setting

GitHub requires Pages to be enabled once by a repository administrator:

1. Open **Settings → Pages** in this repository.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Open **Actions → Deploy Payout Curve Designer to GitHub Pages** and run the workflow, or push a commit to `master`.

After a successful deployment, the site is available at:

<https://mikezhang4951.github.io/pharma/>

Future pushes to `master` redeploy automatically. The workflow publishes `index.html`, the national summary CSS/JavaScript assets, and `territories.json`, and includes `.nojekyll` in the Pages artifact.

The core application loads before the national-summary extension. If that optional JavaScript asset is unavailable or stale during a deployment, territory data and the main plan summary continue to render.
The deployment workflow validates only the required static files and their syntax; it does not reject a deployment based on brittle source-text or script-position checks.
It also runs a browser-like smoke test that verifies territory rows, the payout distribution, and the normalized national summary render together before deployment.

## Input formats

The text/CSV importer requires these fields:

- `Territory`
- `Quarter`
- `TRx Goal`
- `TRx Actual`

`NRx Goal` and `NRx Actual` are optional; the application derives fallback values when they are omitted. JSON imports use an object containing a `quarterlyData` array and may optionally include `points` and `nrxPoints` arrays.
