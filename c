[Unit]
Description=VRAM Watchdog - GPU OOM Prevention
Documentation=https://github.com/ai-hub-madrid/nuclear-recovery
After=nvidia-driver.service graphical.target
Wants=nvidia-driver.service

[Service]
Type=simple
ExecStart=/usr/local/bin/vram-watchdog.sh
Restart=always
RestartSec=10

# Security: needs root to kill processes and manage systemd services
User=root
Group=root

# Resource limits (keep watchdog lightweight)
MemoryMax=64M
CPUQuota=5%

# This service should NEVER be killed by OOM killer
OOMScoreAdjust=-1000

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vram-watchdog

# This is a critical safety service - don't let systemd rate-limit restarts
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target