# FastAPI Infoblox IPAM Adapter

This package provides a **FastAPI** microservice that adapts F5 FAST IPAM calls to Infoblox WAPI.
It implements endpoints expected by F5 FAST as an **external IPAM provider**:

- `POST /ipam/allocate`  — allocate an IP from a specified network
- `POST /ipam/release`   — release an IP
- `GET  /ipam/ranges`    — (optional) list available networks/ranges
- `GET  /health`         — basic healthcheck

Features:
- Configurable via environment variables (using pydantic `Settings`)
- TLS verification and optional client-cert auth to Infoblox
- Requests session with retry/backoff using `urllib3`'s `Retry`
- Authentication for incoming requests (API token or Basic Auth)
- Safe error handling with clear HTTP responses

See `example-registration.sh` for an example FAST provider registration curl command.

---
