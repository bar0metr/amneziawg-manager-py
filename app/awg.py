# app/awg.py
import subprocess
from .utils import get_app_config

def _get_binary_and_interface():
    app_conf = get_app_config() or {}
    binary = app_conf.get("binary") or app_conf.get("backend", "awg")
    interface = app_conf.get("interface")
    if not interface:
        interface = "wg0" if binary == "wg" else "awg0"
    return binary, interface

def run_awg_cmd(args):
    binary, interface = _get_binary_and_interface()
    
    if args and args[0] == "show" and len(args) == 1:
        args.append(interface)

    return subprocess.check_output([binary] + args, text=True)

def generate_keypair():
    binary, _ = _get_binary_and_interface()
    priv = subprocess.check_output([binary, "genkey"], text=True).strip()
    pub = subprocess.check_output([binary, "pubkey"], input=priv, text=True).strip()
    return priv, pub

def list_peers():
    out = run_awg_cmd(["show"])
    peers = []
    current = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("peer:"):
            if current:
                peers.append(current)
            current = {"PublicKey": line[len("peer:"):].strip()}
        elif current:
            if line.startswith("allowed ips:"):
                current["AllowedIPs"] = line[len("allowed ips:"):].strip()
            elif line.startswith("endpoint:"):
                current["Endpoint"] = line[len("endpoint:"):].strip()
            elif line.startswith("latest handshake:"):
                current["latest_handshake"] = line[len("latest handshake:"):].strip()
            elif line.startswith("transfer:"):
                current["transfer"] = line[len("transfer:"):].strip()
    if current:
        peers.append(current)
    return peers

def get_interface():
    out = run_awg_cmd(["show"])
    interface = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("interface:"):
            interface["name"] = line[len("interface:"):].strip()
        elif line.startswith("public key:"):
            interface["PublicKey"] = line[len("public key:"):].strip()
        elif line.startswith("listening port:"):
            interface["ListenPort"] = line[len("listening port:"):].strip()
        elif line.startswith("jc:"):
            interface["Jc"] = line[len("jc:"):].strip()
        elif line.startswith("jmin:"):
            interface["Jmin"] = line[len("jmin:"):].strip()
        elif line.startswith("jmax:"):
            interface["Jmax"] = line[len("jmax:"):].strip()
        elif line.startswith("s1:"):
            interface["S1"] = line[len("s1:"):].strip()
        elif line.startswith("s2:"):
            interface["S2"] = line[len("s2:"):].strip()
        elif line.startswith("h1:"):
            interface["H1"] = line[len("h1:"):].strip()
        elif line.startswith("h2:"):
            interface["H2"] = line[len("h2:"):].strip()
        elif line.startswith("h3:"):
            interface["H3"] = line[len("h3:"):].strip()
        elif line.startswith("h4:"):
            interface["H4"] = line[len("h4:"):].strip()
    return interface

def add_peer_cmd(pubkey: str, ip: str):
    binary, interface = _get_binary_and_interface()
    subprocess.run([binary, "set", interface, "peer", pubkey, "allowed-ips", f"{ip}/32"], check=True)

def remove_peer_cmd(pubkey: str):
    binary, interface = _get_binary_and_interface()
    subprocess.run([binary, "set", interface, "peer", pubkey, "remove"], check=True)
