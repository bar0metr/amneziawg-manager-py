let PREVIEW = null;

async function fetchPreview() {
    const res = await fetch("/api/next-peer");
    const data = await res.json();
    PREVIEW = data;
    document.getElementById("clientConfig").value = data.config;
    document.getElementById("qrImage").src = data.qr;
}

async function fetchPeers() {
    const res = await fetch("/api/peers");
    const data = await res.json();
    const tbody = document.querySelector("#peersTable tbody");
    tbody.innerHTML = "";
    data.forEach(p => {
        const showBtn = p.has_config
            ? `<button onclick='showConfig("${p.PublicKey}")'>Show Config</button>`
            : "";
        const tr = document.createElement("tr");
        tr.innerHTML = `<td><code style="font-size:12px">${p.PublicKey}</code></td>
                        <td>${p.AllowedIPs||""}</td>
                        <td>${p.Endpoint||""}</td>
                        <td>${p.latest_handshake||""}</td>
                        <td>${p.transfer||""}</td>
                        <td>
                            <button onclick='deletePeer("${p.PublicKey}")'>Delete</button>
                            ${showBtn}
                        </td>`;
        tbody.appendChild(tr);
    });
}

async function addPeer() {
    if (!PREVIEW) {
        showToast("Preview not ready", 2000);
        return;
    }

    const body = {
        privkey: PREVIEW.privkey,
        pubkey: PREVIEW.pubkey,
        ipaddr: PREVIEW.ipaddr
    };

    let res;
    try {
        res = await fetch("/api/peers", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(body)
        });
    } catch (err) {
        showToast("Add peer error: " + err.message, 3000);
        return;
    }

    if (!res.ok) {
        let msg = `Add peer error ${res.status}`;
        try {
            const j = await res.json();
            if (j && j.ip) {
                msg += `: IP already in use: ${j.ip}`;
            } else if (j && j.detail) {
                msg += `: ${j.detail}`;
            }
        } catch {
        }
        showToast(msg, 3000);
        await fetchPreview();
        return;
    }

    const data = await res.json();
    document.getElementById("clientConfig").value = data.config;
    document.getElementById("qrImage").src = data.qr;
    showToast("Peer added successfully!", 2000);

    await fetchPeers();
    await fetchPreview();
}


async function deletePeer(pubkey) {
    const ok = confirm("Delete peer " + pubkey + " ?");
    if (!ok) return;

    let res;
    try {
        res = await fetch("/api/peers", {
            method: "DELETE",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({pubkey: pubkey})
        });
    } catch (err) {
        showToast("Delete peer error: " + err.message, 3000);
        return;
    }

    if (!res.ok) {
        let msg = `Delete peer error ${res.status}`;
        try {
            const j = await res.json();
            if (j && j.detail) {
                msg += `: ${j.detail}`;
            }
        } catch {}
        showToast(msg, 3000);
        return;
    }

    showToast("Peer deleted successfully!", 2000);
    await fetchPeers();
}

function copyConfig() {
    const cfg = document.getElementById("clientConfig");
    cfg.select();
    document.execCommand("copy");
    showToast("Copied to clipboard!", 2000);
}

function downloadConfig() {
    const cfg = document.getElementById("clientConfig").value;
    const blob = new Blob([cfg], {type:"text/plain"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "client.conf";
    a.click();
    URL.revokeObjectURL(url);
}

async function showConfig(pubkey) {
    const res = await fetch(`/api/peer-config?pubkey=${encodeURIComponent(pubkey)}`);
    if (res.status === 404) {
        alert("Peer not found");
        return;
    }
    const data = await res.json();

    const backdrop = document.createElement("div");
    backdrop.className = "modal-backdrop";

    const modal = document.createElement("div");
    modal.className = "modal-window";
    modal.innerHTML = `
        <h3>Peer Config</h3>
        <textarea readonly rows="14" cols="60">${data.cfg}</textarea>
        <div><img src="${data.qr}"></div>
        <button id="downloadBtn">Download Config</button>
        <button id="closeBtn">Close</button>
    `;

    modal.querySelector("#closeBtn").onclick = () => {
        modal.remove();
        backdrop.remove();
    };

    modal.querySelector("#downloadBtn").onclick = () => {
        const blob = new Blob([data.cfg], {type:"text/plain"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "client.conf";
        a.click();
        URL.revokeObjectURL(url);
    };

    backdrop.onclick = () => {
        modal.remove();
        backdrop.remove();
    };

    document.body.appendChild(backdrop);
    document.body.appendChild(modal);
}

async function updateBackendStatus() {
    try {
        const res = await fetch("/api/interface-status");
        const data = await res.json();
        const div = document.getElementById("backendStatus");

        if (data.status) {
            div.className = "status-online";
            div.textContent = `${data.backend_name} (${data.interface}) is ONLINE`;
        } else {
            div.className = "status-offline";
            div.textContent = `${data.backend_name} (${data.interface}) is OFFLINE`;
        }

        const controls = document.querySelectorAll("#addPeerBtn, #copyConfigBtn, #downloadConfigBtn");
        controls.forEach(btn => btn.disabled = !data.status);

    } catch (e) {
        console.error("Failed to fetch backend status", e);
    }
}

async function getManagerName() {
    try {
        const res = await fetch("/api/manager-type");
        const data = await res.json();
        const div = document.getElementById("managerName");

        div.textContent = `${data.manager}`;

    } catch (e) {
        console.error("Failed to fetch manager name", e);
    }
}

function showToast(message, duration = 2000) {
    const toast = document.createElement("div");
    toast.className = "toast-message";
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

document.getElementById("addPeerBtn").addEventListener("click", addPeer);
document.getElementById("copyConfigBtn").addEventListener("click", copyConfig);
document.getElementById("downloadConfigBtn").addEventListener("click", downloadConfig);

fetchPreview();
fetchPeers();
getManagerName();
setInterval(fetchPeers, 5000);

updateBackendStatus();
setInterval(updateBackendStatus, 5000);
