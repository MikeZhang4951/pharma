#!/usr/bin/env python3
"""System health dashboard — all services, CPU, memory, disk on port 8092."""

import http.server
import json
import os
import subprocess
import time
from pathlib import Path

PORT = 8092
THIS_DIR = Path(__file__).parent

SERVICES = [
    ("8080", "Task Board / Agent Office"),
    ("8081", "Ticker Dashboard (Todd)"),
    ("8089", "Character Canvas"),
    ("8090", "Ticker Dashboard"),
    ("8091", "Flipper Portal UI"),
    ("3000", "WhatsApp (Mike)"),
    ("3001", "WhatsApp (Michael)"),
    ("8765", "Flipper Browser WS"),
    ("8766", "Flipper Hermes WS"),
]

import socket

def check_port(port: str) -> dict:
    """Check if a port is listening via TCP connect."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", int(port)))
        sock.close()
        if result == 0:
            # Try to get PID
            try:
                pid_out = subprocess.run(
                    ["fuser", f"{port}/tcp"], capture_output=True, text=True, timeout=3
                ).stdout.strip()
                pid = pid_out if pid_out else None
            except:
                pid = None
            return {"port": port, "up": True, "pid": pid}
        return {"port": port, "up": False, "pid": None}
    except Exception as e:
        return {"port": port, "up": False, "pid": None, "error": str(e)}

def get_system() -> dict:
    """Get CPU, memory, disk, uptime."""
    try:
        # CPU
        cpu = subprocess.run(
            ["top", "-bn1"], capture_output=True, text=True, timeout=5
        ).stdout
        cpu_line = [l for l in cpu.split("\n") if "Cpu(s)" in l]
        cpu_pct = cpu_line[0].split(":")[1].split(",")[0].strip() if cpu_line else "?"

        # Memory
        mem = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5).stdout
        mem_line = [l for l in mem.split("\n") if "Mem:" in l]
        if mem_line:
            parts = mem_line[0].split()
            mem_total = int(parts[1])
            mem_used = int(parts[2])
            mem_pct = round(mem_used / mem_total * 100, 1)
        else:
            mem_total = mem_used = mem_pct = "?"

        # Disk
        disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5).stdout
        disk_line = [l for l in disk.split("\n") if " /" in l and "/ " not in l]
        if not disk_line:
            disk_line = [l for l in disk.split("\n") if " /$" in l or l.endswith(" /")]
        if disk_line:
            parts = disk_line[0].split()
            disk_used = parts[2]
            disk_total = parts[1]
            disk_pct = parts[4]
        else:
            disk_used = disk_total = disk_pct = "?"

        # Uptime
        uptime_out = subprocess.run(["uptime", "-p"], capture_output=True, text=True, timeout=5).stdout.strip()
        uptime = uptime_out.replace("up ", "") if uptime_out else "?"

        return {
            "cpu": cpu_pct,
            "memory": {"used_mb": mem_used, "total_mb": mem_total, "pct": mem_pct},
            "disk": {"used": disk_used, "total": disk_total, "pct": disk_pct},
            "uptime": uptime,
        }
    except Exception as e:
        return {"error": str(e)}

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == "/":
            self._serve_file("health.html", "text/html")
        elif self.path == "/api/health":
            services = [check_port(p) for p, _ in SERVICES]
            system = get_system()
            all_up = all(s["up"] for s in services)
            self._json({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "all_up": all_up,
                "services": [
                    {**s, "name": name} for s, (_, name) in zip(services, SERVICES)
                ],
                "system": system,
            })
        elif self.path == "/health":
            self._json({"status": "ok"})
        else:
            self.send_error(404)

    def _json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filename, ctype):
        path = THIS_DIR / filename
        try:
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(500, f"{filename} missing")

if __name__ == "__main__":
    print(f"Health dashboard on 0.0.0.0:{PORT}")
    httpd = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
