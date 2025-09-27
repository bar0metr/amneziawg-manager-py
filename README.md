# AmneziaWG / WireGuard Manager

**AmneziaWG Manager** is a FastAPI-based web service for managing virtual VPN interfaces using **AmneziaWG (AWG)** or **WireGuard (WG)**.  
It allows you to:

- View current peers
- Add new peers with automatic IP assignment
- Generate client configurations and QR codes for quick connection
- Delete peers
- Support multiple interfaces and backends (AWG/WG)

---

## Installation

This guide assumes installation **as root**, but it can also run under a dedicated non-root user.

### 1. Clone the repository

```bash
cd /opt/
git clone https://github.com/bar0metr/amneziawg-manager-py.git
```

### 2. Set up Python virtual environment

```bash
cd /opt/amneziawg-manager-py
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up systemd-service

```bash
cp /opt/amneziawg-manager-py/amneziawg-manager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable amneziawg-manager.service
```

### 4. Configuration

The service configuration is stored in a JSON file /opt/amneziawg-manager-py/config.json

The configuration file controls both the **backend VPN interface** and default client parameters.

```json
{
  "app": {
    "host": "127.0.0.1",
    "port": 6688,
    "reload": true,
    "peers_file": "data/peers.json",
    "log_level": "INFO",
    "backend": "awg",
    "interface": "awg0"
  },
  "client_defaults": {
    "network_cidr": "192.168.6.0/24",
    "server_ip": "192.168.6.1",
    "server_endpoint": "your_(a)wg_server_ip_address",
    "dns": ["192.168.6.1", "8.8.8.8"],
    "persistent_keepalive": 15
  }
}
```

#### app section

* host – IP address where the FastAPI web server will bind.
Example: "127.0.0.1" means it only listens on localhost.

* port – Port for the web server. Example: 6688.

* reload – Boolean flag to enable auto-reloading during development. Useful when editing code.

* peers_file – Path to the JSON file storing all peers. Default is "data/peers.json". The service must have write access to this file.

* log_level – Logging level for the uvicorn service. 
Common values: "DEBUG", "INFO", "WARNING", "ERROR".

* backend – Which VPN backend to use. Can be:

* * "awg" → AmneziaWG

* * "wg" → WireGuard

* interface – VPN interface name associated with the backend. 
Example: "awg0" for AmneziaWG or "wg0" for WireGuard. The service will only manage this specific interface.

#### client_defaults section

These values are applied when generating new client configurations:

* network_cidr – The subnet used for assigning IPs to clients. 
Example: "192.168.6.0/24".

* server_ip – The internal VPN server IP in the above subnet. 
Example: "192.168.6.1".

* server_endpoint – The public endpoint clients will connect to. Replace with your server’s real IP or domain.

* dns – List of DNS servers for clients. 
Example: "192.168.6.1" (local) and "8.8.8.8" (Google DNS).

* persistent_keepalive – Keepalive interval (in seconds) for clients to maintain connection behind NAT. Default: 15.

### 5. Start the service

```bash
systemctl start amneziawg-manager.service
systemctl status amneziawg-manager.service
```

---

### Recommendations:
It is highly recommended to bind the service to the localhost and provide access via Nginx (protected with authentication).

Also, as mentioned earlier, you can ensure the service runs under a limited user. To do this, you need to:

#### 1. Create a user and grant the necessary rights to directories

```bash
sudo useradd -r -s /bin/false amneziawg
sudo chown -R amneziawg:amneziawg /opt/amneziawg-manager-py
```

#### 2. Modify a systemd unit

Uncomment **User=amneziawg** and **Group=amneziawg** in /etc/systemd/system/amneziawg-manager.service

```bash
[Unit]
Description=AmneziaWG/WireGuard Manager FastAPI Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/amneziawg-manager-py
ExecStart=/opt/amneziawg-manager-py/venv/bin/python /opt/amneziawg-manager-py/run.py
Restart=always
RestartSec=5
# Optional if using dedicated user:
User=amneziawg
Group=amneziawg

[Install]
WantedBy=multi-user.target
```

#### 3. Ensure the user can execute wg or awg commands without password:

```bash
sudo visudo
```

Add:
```bash
amneziawg ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/sbin/awg
```

#### 4. Restart the systemd-unit

```bash
systemctl daemon-reload
systemctl restart amneziawg-manager.service
systemctl status amneziawg-manager.service
```