import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config import Settings
from infoblox_client import InfobloxClient, InfobloxError

settings = Settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("infoblox-adapter")

app = FastAPI(title="Infoblox IPAM Adapter", version="1.0.0")

# Simple token-based auth for incoming requests (FAST -> adapter)
bearer = HTTPBearer(auto_error=False)


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if settings.api_token:
        if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != settings.api_token:
            raise HTTPException(status_code=401, detail="Invalid or missing API token")
    else:
        # if api_token not set, allow without token (not recommended in prod)
        return True


class AllocateRequest(BaseModel):
    network: str  # network in CIDR form or Infoblox network ref
    hostname: str | None = None
    count: int = 1


class ReleaseRequest(BaseModel):
    address: str


@app.on_event("startup")
def startup_event():
    app.state.client = InfobloxClient(settings)
    logger.info("Infoblox adapter started")


@app.post("/ipam/allocate")
async def allocate(req: AllocateRequest, auth=Depends(require_auth)):
    client: InfobloxClient = app.state.client
    try:
        ips = client.allocate_ips(network=req.network, count=req.count, hostname=req.hostname)
        return {"addresses": ips}
    except InfobloxError as e:
        logger.exception("Allocation failed")
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/ipam/release")
async def release(req: ReleaseRequest, auth=Depends(require_auth)):
    client: InfobloxClient = app.state.client
    try:
        result = client.release_ip(req.address)
        return {"status": "released", "address": req.address, "result": result}
    except InfobloxError as e:
        logger.exception("Release failed")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/ipam/ranges")
async def ranges(auth=Depends(require_auth)):
    client: InfobloxClient = app.state.client
    try:
        nets = client.list_networks()
        return {"networks": nets}
    except InfobloxError as e:
        logger.exception("List networks failed")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
