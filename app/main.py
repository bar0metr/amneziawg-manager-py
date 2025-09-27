from fastapi import Request
from fastapi.responses import JSONResponse
from . import app, templates
from .awg import generate_keypair, list_peers, get_interface, add_peer_cmd, remove_peer_cmd
from .utils import load_peers, save_peer, remove_peer, generate_client_config, config_to_datauri_png, find_free_ip, check_manager_type, check_backend_interface

from pydantic import BaseModel
from typing import Optional

class PeerKey(BaseModel):
    pubkey: str

class AddPeerRequest(BaseModel):
    privkey: Optional[str] = None
    pubkey: Optional[str] = None
    ipaddr: Optional[str] = None

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/interface-status")
async def interface_status():
    return check_backend_interface()

@app.get("/api/manager-type")
async def manager_type():
    return check_manager_type()

@app.get("/api/peers")
def api_peers():
    awg_peers = list_peers()
    local_peers = {p["pubkey"]: p for p in load_peers()}
    result = []
    for p in awg_peers:
        pubkey = p["PublicKey"]
        entry = p.copy()
        entry["has_config"] = pubkey in local_peers
        result.append(entry)
    return result

@app.get("/api/interface")
def api_interface():
    return get_interface()

@app.get("/api/next-peer")
def api_next_peer():
    priv, pub = generate_keypair()
    peers = list_peers()
    ip = find_free_ip(peers)
    cfg = generate_client_config(get_interface(), priv, pub, ip)
    qr = config_to_datauri_png(cfg)
    return {"privkey": priv, "pubkey": pub, "ipaddr": ip, "config": cfg, "qr": qr}

@app.post("/api/peers")
def api_add_peer(req: AddPeerRequest):
    if req.privkey and req.pubkey:
        priv = req.privkey
        pub = req.pubkey
    else:
        priv, pub = generate_keypair()

    peers = load_peers()
    ip = req.ipaddr or find_free_ip(list_peers())

    used_ips = {p["ip"] for p in peers}
    if ip in used_ips:
        return JSONResponse({"error": "IP already in use", "ip": ip}, status_code=409)

    add_peer_cmd(pub, ip)
    cfg = generate_client_config(get_interface(), priv, pub, ip)
    save_peer({"pubkey": pub, "privkey": priv, "ip": ip, "cfg": cfg,
               "endpoint": f"{pub}:{get_interface().get('ListenPort','50822')}"})
    qr = config_to_datauri_png(cfg)
    return {"PublicKey": pub, "PrivateKey": priv, "AllowedIPs": f"{ip}/32", "config": cfg, "qr": qr}

@app.delete("/api/peers")
def api_remove_peer(peer: PeerKey):
    remove_peer_cmd(peer.pubkey)
    remove_peer(peer.pubkey)
    return {"status": "ok"}

@app.get("/api/peer-config")
def api_peer_config(pubkey: str):
    peers = load_peers()
    peer = next((p for p in peers if p["pubkey"] == pubkey), None)
    if not peer:
        return JSONResponse({"error": "Peer config not found"}, status_code=404)
    qr = config_to_datauri_png(peer["cfg"])
    return {"cfg": peer["cfg"], "qr": qr}
