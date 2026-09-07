# PostHog Connector — Executed Validation Evidence

**Target:** PostHog US Cloud (`https://us.posthog.com/api`)
**Date:** 2026-09-07
**Credential type:** PostHog Personal API Key, configured with the permissions required by the exercised endpoints. The key value is not stored in this repository.

## Part A — Authentication and connection lifecycle

| Scenario | Result | Evidence |
|---|---|---|
| A1: Authenticate against PostHog US Cloud | Passed | `GET /api/users/@me/` returned HTTP 200 for the authenticated Bluebeeweb user. |
| A2: Resolve active project | Passed | `GET /api/projects/@current/` returned HTTP 200 and project ID `597925`. |
| A3: Connect lifecycle | Passed | `connect_posthog_connector` validated the live key, saved one mock Document-store connection, and returned a masked key only. |
| A4: List and disconnect lifecycle | Passed | `list_connections` returned the saved connection; `disconnect_posthog_connector` removed it from the mock Document store; the subsequent list was empty. |

## Part B — Live read operations

| Scenario | Result | Evidence |
|---|---|---|
| B1: List events | Passed | `GET /api/projects/597925/events/` returned HTTP 200 and the captured `connector_test_event`. |
| B2: Get event | Passed | `GET /api/projects/597925/events/{event_id}/` returned HTTP 200 for the listed event. |
| B3: Connector handlers | Passed | The local handler suite executed `list_events`, `get_event`, and `audit_event_health` using the live PostHog API and mock Document-store lifecycle. |

## Part C — Safe write and cleanup

| Scenario | Result | Evidence |
|---|---|---|
| C1: Create Action | Passed | `POST /api/projects/597925/actions/` created temporary Action `Imperal Live Test Action` with HTTP 201. |
| C2: Read created Action | Passed | The action was listed and fetched by ID with HTTP 200. |
| C3: Cleanup Action | Passed | PostHog does not accept DELETE on this endpoint (HTTP 405); the Action was safely soft-deleted via `PATCH` with `{"deleted": true}` (HTTP 200). A following list returned zero Actions. |

## Part D — Regression and deployment gates

- [x] Connector source compiles with Python `py_compile`.
- [x] Local mock-store lifecycle suite passes while making live, read-only PostHog API calls.
- [x] Credentials are masked in connector results and never committed.
- [ ] Deployed persistent-store lifecycle must be verified after deployment; the local suite uses a mock Document store.
- [ ] Marketplace review readiness is not asserted by this document.
