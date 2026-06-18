#!/bin/bash
# tailscale_keepalive.sh - Keep Tailscale tunnel alive
# Run via cron every 5 minutes
# Checks if Tailscale is connected, if not restarts it

LOG="/var/log/tailscale-keepalive.log"

# Check if tailscale is running
if ! systemctl is-active --quiet tailscaled; then
    echo "$(date): tailscaled not running, starting..." >> $LOG
    sudo systemctl start tailscaled
    sleep 5
fi

# Check if we can reach the coordination server
TS_STATUS=$(tailscale status 2>&1)
if echo "$TS_STATUS" | grep -q "offline\|error\|not connected"; then
    echo "$(date): Tailscale not connected, restarting..." >> $LOG
    sudo tailscale down 2>/dev/null
    sleep 2
    sudo tailscale up --accept-routes 2>/dev/null
    echo "$(date): Tailscale restarted" >> $LOG
fi

# Ping relay to keep NAT alive
tailscale ping --c 1 100.76.38.116 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "$(date): Ping failed, forcing reconnect..." >> $LOG
    sudo tailscale down 2>/dev/null
    sleep 2
    sudo tailscale up --accept-routes 2>/dev/null
fi