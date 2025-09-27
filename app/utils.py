import ipaddress
import subprocess
import qrcode
import io
import base64
import json
from pathlib import Path

CONFIG = None

def load_config(config: dict):
    global CONFIG
    CONFIG = config

def get_app_config():
    return CONFIG.get("app", {}) if CONFIG else {}

def get_client_defaults():
    return CONFIG.get("client_defaults", {}) if CONFIG else {}

def load_peers():
    peers_file = Path(get_app_config().get("peers_file", "data/peers.json"))
    if not peers_file.exists():
        return []
    with peers_file.open("r") as f:
        return json.load(f)

def save_peer(peer):
    peers_file = Path(get_app_config().get("peers_file", "data/peers.json"))
    peers = load_peers()
    peers.append(peer)
    with peers_file.open("w") as f:
        json.dump(peers, f, indent=2)

def remove_peer(pubkey):
    peers_file = Path(get_app_config().get("peers_file", "data/peers.json"))
    peers = load_peers()
    peers = [p for p in peers if p["pubkey"] != pubkey]
    with peers_file.open("w") as f:
        json.dump(peers, f, indent=2)

def find_free_ip(peers_from_awg):
    client_conf = get_client_defaults()
    network_cidr = client_conf.get("network_cidr", "192.168.6.0/24")
    server_ip = client_conf.get("server_ip", "192.168.6.1")

    used = set()
    for p in peers_from_awg:
        if "AllowedIPs" in p:
            for ip in p["AllowedIPs"].split(","):
                used.add(ip.split("/")[0].strip())

    net = ipaddress.ip_network(network_cidr)
    for host in net.hosts():
        s = str(host)
        if s == server_ip:
            continue
        if s not in used:
            return s

    raise RuntimeError("No free IPs available in subnet")

def generate_client_config(interface: dict, peer_priv: str, peer_pub: str, ip: str) -> str:
    client_conf = get_client_defaults()
    app_conf = get_app_config()
    dns_list = ",".join(client_conf.get("dns", []))
    server_endpoint = client_conf.get("server_endpoint", "127.0.0.1")
    persistent_keepalive = client_conf.get("persistent_keepalive", 15)
    backend = app_conf.get("backend", "awg")  # default to awg

    awg_interface_fields = ""
    if backend.lower() == "awg":
        awg_interface_fields = f"""
Jc = {interface.get("Jc","")}
Jmin = {interface.get("Jmin","")}
Jmax = {interface.get("Jmax","")}
S1 = {interface.get("S1","")}
S2 = {interface.get("S2","")}
H1 = {interface.get("H1","")}
H2 = {interface.get("H2","")}
H3 = {interface.get("H3","")}
H4 = {interface.get("H4","")}
"""

    cfg = f"""[Interface]
Address = {ip}/32
DNS = {dns_list}
PrivateKey = {peer_priv}{awg_interface_fields}

[Peer]
AllowedIPs = 0.0.0.0/0
Endpoint = {server_endpoint}:{interface.get("ListenPort","58222")}
PersistentKeepalive = {persistent_keepalive}
PublicKey = {interface.get("PublicKey","")}
"""
    return cfg

def config_to_datauri_png(cfg_text: str) -> str:
    img = qrcode.make(cfg_text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return "data:image/png;base64," + b64

def check_backend_interface():
    app_conf = get_app_config()
    backend = app_conf.get("backend", "awg").lower()
    interface = app_conf.get("interface")
    result = {
        "backend_name": "AmneziaWG" if backend == "awg" else "Wireguard",
        "interface": interface or ("awg0" if backend == "awg" else "wg0"),
        "status": False
    }

    try:
        if backend == "awg":
            out = subprocess.check_output(["awg", "show"], text=True)
            for line in out.splitlines():
                if line.strip() == f"interface: {result['interface']}":
                    result["status"] = True
                    break
        elif backend == "wg":
            out = subprocess.check_output(["wg", "show", "interfaces"], text=True)
            interfaces = out.split()
            if result["interface"] in interfaces:
                result["status"] = True
    except Exception as e:
        result["status"] = False

    return result

def check_manager_type():
    app_conf = get_app_config()
    backend = app_conf.get("backend", "awg").lower()

    result = {
        "manager": "AmneziaWG Manager" if backend == "awg" else "Wireguard Manager",
    }

    return result