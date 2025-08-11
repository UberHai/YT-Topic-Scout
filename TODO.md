## YT Topic-Scout — Ordered TODO for Agentic Programmers

This checklist is ordered for safe, atomic changes that preserve behavior. Complete tasks sequentially. Each task includes files, exact edits, acceptance criteria, risk, and rollback.

### Global Safety Rules
- Preserve public APIs, request/response shapes, env vars, and startup scripts.
- Make small, atomic edits (≤150 LOC per change). Commit each task separately.
- Do not remove code unless confidence is High. If unsure, mark Low Confidence and skip.
- After each task: run backend and frontend locally and smoke test.

### Prerequisites
- Python 3.9+, Node 18+, pnpm or npm.
- Backend: `uvicorn app.main:app --reload` from `backend` directory (local venv only; no Docker).
- Frontend: `npm run dev` from `frontend`.

---

### 1) Frontend: Fix trend data shape
- Status: DONE
- Files: `frontend/src/components/TrendChart.jsx`
- Edit:
  ```diff
  -        const result = await response.json();
  -        setData(result);
  +        const result = await response.json();
  +        setData(Array.isArray(result) ? result : (result?.trend_data || []));
  ```
- Acceptance:
  - Searching a topic renders a line chart without JS errors.
  - Network tab: GET `/api/trends/<topic>` returns `{ topic, trend_data }`; chart uses `trend_data`.
- Risk: None. Rollback: revert the two changed lines.

### 2) Frontend: Align ChannelAnalysis with backend response
- Status: DONE
- Files: `frontend/src/components/ChannelAnalysis.jsx`
- Edits:
  1) Store only `analysis`:
  ```diff
  -                const data = await response.json();
  -                setAnalysis(data);
  +                const data = await response.json();
  +                setAnalysis(data?.analysis || null);
  ```
  2) Topics array name:
  ```diff
  -                    {analysis.topics && analysis.topics.length > 0 ? (
  -                        analysis.topics.map((topic, index) => <li key={index}>{topic}</li>)
  +                    {Array.isArray(analysis.most_common_topics) && analysis.most_common_topics.length > 0 ? (
  +                        analysis.most_common_topics.map((topic, index) => <li key={index}>{topic}</li>)
  ```
  3) Average length key:
  ```diff
  -                <p>{analysis.average_video_length ? formatDuration(analysis.average_video_length) : 'N/A'}</p>
  +                <p>{typeof analysis.average_video_length_seconds === 'number' ? formatDuration(analysis.average_video_length_seconds) : 'N/A'}</p>
  ```
  4) Most viewed mapping:
  ```diff
  -                    {analysis.most_viewed_videos && analysis.most_viewed_videos.length > 0 ? (
  -                        analysis.most_viewed_videos.map((video) => (
  -                            <li key={video.video_id}>
  -                                <a href={`https://www.youtube.com/watch?v=${video.video_id}`} target="_blank" rel="noopener noreferrer">
  -                                    {video.title}
  -                                </a>
  -                                <span> - {video.views.toLocaleString()} views</span>
  -                            </li>
  -                        ))
  +                    {Array.isArray(analysis.most_viewed_videos) && analysis.most_viewed_videos.length > 0 ? (
  +                        analysis.most_viewed_videos.map((video, idx) => (
  +                            <li key={idx}>
  +                                <a href={video.url} target="_blank" rel="noopener noreferrer">
  +                                    {video.title}
  +                                </a>
  +                                <span> - {Number(video.view_count || 0).toLocaleString()} views</span>
  +                            </li>
  +                        ))
  ```
- Acceptance:
  - Entering a channel ID renders topics, average video length, and list of most viewed videos.
  - No `undefined` property accesses in console.
- Risk: Low. Rollback: revert changed lines.

### 3) Frontend: Correct export file extension
- Status: DONE
- Files: `frontend/src/components/SearchHistory.jsx`
- Edit:
  ```diff
  -      link.setAttribute('download', `search-export-${searchId}.csv`);
  +      link.setAttribute('download', `search-export-${searchId}.txt`);
  ```
- Acceptance: Exported file downloads as `.txt` and opens in a text editor.
- Risk: None. Rollback: revert the line.

### 4) Backend: Remove logger shadowing in summarizer
- Status: DONE
- Files: `backend/app/summarizer.py`
- Edit:
  ```diff
  -from .logger import logger
  -
  -# Configure logging
  -logger = logging.getLogger(__name__)
  +logger = logging.getLogger(__name__)
  ```
- Acceptance: Module imports without duplicate logger instances; behavior unchanged.
- Risk: None. Rollback: restore import and variable if desired.

### 5) Backend: DRY fetch constants via config and use batch size
- Status: DONE
- Files: `backend/app/fetch.py`
- Edits:
  1) Replace local constants with imports from config:
  ```diff
  -# Configuration constants
  -MAX_RESULTS = 10
  -CACHE_TTL = 3600  # seconds
  -API_RETRY_ATTEMPTS = 3
  -API_RETRY_DELAY = 1  # seconds
  -
  -# Load API key from config
  -from . import config
  +from . import config
  +from .config import MAX_RESULTS, CACHE_TTL, API_RETRY_ATTEMPTS, API_RETRY_DELAY, BATCH_SIZE
  ```
  2) Use `BATCH_SIZE` in `_details`:
  ```diff
  -    batch_size = 50  # YouTube API limit
  +    batch_size = BATCH_SIZE or 50  # YouTube API limit
  ```
- Acceptance: Fetch still works; batch size respects `BATCH_SIZE` when configured.
- Risk: Low (defaults preserved). Rollback: reintroduce local constants and `50` literal.

### 6) Backend: Hoist DB timeout and retention to config
- Status: DONE
- Files: `backend/app/config.py`, `backend/app/database.py`
- Edits:
  1) Add retention constant (config):
  ```diff
  +MAX_VIDEOS_RETAINED = config.get_int('MAX_VIDEOS_RETAINED', 1000)
  ```
  2) Use `DB_TIMEOUT` in `_conn`GPT54parameterize retention (database):
  ```diff
  +from .config import DB_TIMEOUT
  -    timeout = timeout or 30
  +    timeout = timeout or DB_TIMEOUT or 30
  ```
  ```diff
  +from .config import MAX_VIDEOS_RETAINED
  -        c.execute(
  -            "DELETE FROM videos WHERE rowid IN (SELECT rowid FROM videos ORDER BY rowid DESC LIMIT -1 OFFSET 1000)"
  -        )
  +        c.execute(
  +            "DELETE FROM videos WHERE rowid IN (SELECT rowid FROM videos ORDER BY rowid DESC LIMIT -1 OFFSET ?)",
  +            (MAX_VIDEOS_RETAINED,),
  +        )
  ```
- Acceptance: DB initializes and vacuum/cleanup still run; no errors; retention is configurable.
- Risk: Low. Rollback: revert to literals (30s timeout, 1000 offset).

### 7) Optional: Trim unused dependencies (confirm before applying)
- Files: `requirements.txt`, root `package.json`
- Candidates:
  - Python High Confidence: `rich`, `python-dotenv`, `hdbscan`, `bertopic` — DONE
  - Python Low Confidence: `accelerate` (may be installed implicitly by transformers) — KEPT
  - Root JS High Confidence: dependency `docker` (unused) — DONE (and Docker files removed)
  - Frontend JS: remove `axios` and replace with `fetch` where used — DONE
- Steps:
  - Removed lines from `requirements.txt` (High Confidence set), re-install, boot app.
  - Update root `package.json` dependencies to `{}` if only `docker` existed. — DONE
- Acceptance: Backend runs; summarizer and sentiment still work.
- Risk: Medium (transitive model/tooling). Rollback: restore lines and reinstall.

### 8) Optional: UI/Config polish
- Files: `frontend/index.html`
  - Change `<title>` to "YouTube Topic Scout". — DONE
- Files: `frontend/src/App.css` or `frontend/src/App.jsx`
  - Either remove unused `.App` style or apply class to a wrapper in `App.jsx`. — DONE (applied class)
- Files: `backend/app/main.py`
  - CORS: allow local dev origin only (no Docker). — DONE
- Acceptance: No functional changes; improved clarity.
- Risk: None. Rollback: revert cosmetic edits.

### 9) Future (tracked, not required for parity)
- Replace axios with fetch across frontend to unify HTTP client; remove `axios` dep.
- Consider splitting `database.py` into logical modules if it grows (CRUD/FTS vs. maintenance).
- Add unit tests for endpoints and React components.
- Add CI (lint, type check, build) for backend and frontend.

---

### Validation Checklist (run after each task)
- Backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`.
- Frontend: `npm --prefix frontend run dev` and manually test:
  - Topic search renders results and trends.
  - Channel analysis loads and displays.
  - Export from history downloads `.txt`.
- Logs: No new errors in terminal or browser console.


