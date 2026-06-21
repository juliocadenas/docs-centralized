#!/usr/bin/env python3
"""Crear paquete deploy tar.gz"""
import tarfile
import os

OUTPUT = "ai-hub-deploy.tar.gz"
files = []

for root, dirs, flist in os.walk("ai-hub-gateway/gateway"):
    for f in flist:
        if f.endswith(".py"):
            files.append(os.path.join(root, f))

for root, dirs, flist in os.walk("ai-hub-gateway/services"):
    for f in flist:
        if f.endswith((".py", "Dockerfile", ".yml", ".yaml", ".txt", ".sh")):
            files.append(os.path.join(root, f))

files.append("ai-hub-gateway/docker-compose.yml")
files.append("ai-hub-gateway/main.py")
files.append("ai-hub-gateway/requirements.txt")
files.append("_deploy_on_server.sh")

with tarfile.open(OUTPUT, "w:gz") as tar:
    for f in files:
        if os.path.exists(f):
            tar.add(f)
            print(f"  + {f}")

size = os.path.getsize(OUTPUT)
print(f"\nPaquete: {OUTPUT} ({size/1024:.0f} KB)")