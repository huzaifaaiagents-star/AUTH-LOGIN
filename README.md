# AUTH-LOGIN

A FastAPI auth system built on Supabase. Signup, login, protected routes, token verification, and Swagger docs — built stage by stage, each one checkpointed before moving on.

## Setup

```bash
python -m venv venv
venv\\Scripts\\activate
pip install fastapi uvicorn python-dotenv supabase
```

Create a `.env` file with:

```
SUPABASE\_URL=your\_supabase\_url
SUPABASE\_KEY=your\_supabase\_key
```

Run it:

```bash
py main.py
```

Docs live at `http://localhost:3000/docs`.

## What's in here

### Stage 1 — Signup \& Login

Built `/auth/signup` and `/auth/login`. Used Pydantic optional fields plus manual `if not` checks, scoped to just these two routes — not a global exception handler. Kept the blast radius small.

Learned the real difference between 400 and 401: 400 is a malformed request, 401 is a well-formed request with bad credentials. Wrong password on login returns 401, not 400.

Debugged three real bugs along the way — a missing `JSONResponse` import, a `datetime` object that wasn't JSON-serializable (fixed with `model\_dump(mode="json")`), and a Supabase rate-limit/reserved-domain rejection that had nothing to do with my code.

Checkpoint: signup returns 201, login returns 200 with tokens, wrong password returns 401. All verified.

### Stage 2 — Public \& Protected Gates

First pass at telling public routes and protected routes apart. Worked through why `None.startswith()` crashes, why `not header` has to be checked first, and how to pull the token out of `"Bearer <token>"` with `.split(" ")\[1]`.

Checkpoint: tested all three failure shapes — missing header, no "Bearer" prefix, "Bearer" with nothing after it — plus the public route's happy path. All passed.

### Stage 3 — Real Token Verification

`/protected/profile` stopped just checking header shape and started actually verifying tokens against Supabase. Used `try/except` around `supabase.auth.get\_user(token)`: a real token returns 200 with id, email, and created\_at. A bad token gets caught as `AuthApiError` and returns 401.

Tested real-vs-fake token behavior with a standalone script before touching the route, so I wasn't debugging the route and the logic at the same time. Also fixed a PowerShell `curl` quoting issue along the way.

Checkpoint: real token → 200, tampered token → 401. Committed and pushed.

### Stage 4 — Auth Middleware \& Logout

Pulled the verification logic out of the route and into a reusable dependency: `get\_current\_user`, built with `HTTPBearer` to extract the token and `supabase.auth.get\_user(token)` to check it. Returns the user on success, raises `HTTPException(401)` on failure.

`/protected/profile` got simpler — no more manual header parsing or try/except sitting in the route. It just declares `Depends(get\_current\_user)`.

Added `/protected/dashboard` as proof the dependency works on any route, not just profile.

`/auth/logout` is gated behind the same dependency. It returns 204 with no body. It does **not** call Supabase's sign-out — that's a real limitation of stateless JWTs, and I'm not pretending otherwise. The token stays valid until it expires; logout here just requires that you're authenticated to hit the endpoint.

Checkpoint: all five scenarios verified. Committed and pushed.

### Stage 5 — Swagger UI

No new security code needed here — that's the whole point. `HTTPBearer` was already wired into `get\_current\_user` back in Stage 4, and FastAPI auto-generates the padlock icon in Swagger from that. This stage was just clicking through it.

Configured `/docs`, clicked Authorize, pasted a real JWT, and ran `/protected/profile` straight from the browser.

Checkpoint: padlock icon shows on all three protected routes (`/protected/profile`, `/protected/dashboard`, `/auth/logout`). Authorized and tested successfully. Screenshot below.

!\[Swagger UI with bearer auth](Auth-Login-Fast-API-Setup.png)

## Known limitation

Logout doesn't invalidate the token server-side — it's a stateless JWT setup, so the token just lives until it expires. Documenting it here instead of hiding it.

