"""
GPU Resource Manager.
Monitors VRAM usage and manages service start/stop to optimize GPU utilization.
Includes auto-unload of idle services to prevent VRAM exhaustion.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import time
from typing import Dict, List, Optional

from .config import (
    GPU_AVAILABLE_VRAM_MB,
    GPU_TOTAL_VRAM_MB,
    SERVICES,
)

logger = logging.getLogger(__name__)

# Idle timeout: services with no activity for this long get auto-stopped
IDLE_TIMEOUT_SECONDS = 600  # 10 minutes
# How often the watchdog runs
WATCHDOG_INTERVAL_SECONDS = 60

# NOTE: Password is now read from env var, not hardcoded
# Configure passwordless sudo via /etc/sudoers.d/ai-hub-gateway instead
SUDO_PASSWORD = os.getenv("SUDO_PASSWORD", "")  # Empty = use passwordless sudo

# Docker compose directory (configurable)
DOCKER_COMPOSE_DIR = os.getenv("DOCKER_COMPOSE_DIR", "/mnt/seagate/ai-hub-gateway")


class GPUManager:
    """
    Manages GPU VRAM allocation and service lifecycle.
    """

    def __init__(self):
        self._running_services: Dict[str, Dict] = {}
        self._vram_used_mb = 0
        self._last_used: Dict[str, Optional[float]] = {}  # service_name -> timestamp or None
        self._watchdog_task: Optional[asyncio.Task] = None
        # Semaphore: only 1 GPU-intensive job at a time (prevents OOM from concurrent requests)
        self._gpu_semaphore = asyncio.Semaphore(1)
        # Track queue depth for status reporting
        self._queue_waiting = 0

    # ============================================================
    # GPU Job Semaphore (prevents concurrent GPU jobs -> OOM)
    # ============================================================

    async def acquire_gpu(self):
        """Acquire GPU lock. Use as: async with gpu_manager.acquire_gpu(): ..."""
        self._queue_waiting += 1
        try:
            await self._gpu_semaphore.acquire()
        finally:
            self._queue_waiting -= 1

    def release_gpu(self):
        """Release GPU lock."""
        self._gpu_semaphore.release()

    @property
    def gpu_queue_waiting(self) -> int:
        """How many requests are waiting for the GPU lock."""
        return self._queue_waiting

    # ============================================================
    # Service usage tracking (called by routers)
    # ============================================================

    def mark_service_used(self, service_name: str):
        """Mark a service as actively being used. Resets its idle timer."""
        self._last_used[service_name] = time.time()

    def get_idle_seconds(self, service_name: str) -> Optional[float]:
        """How many seconds since this service was last used. Returns None if never used."""
        last = self._last_used.get(service_name)
        if last is None:
            return None
        return time.time() - last

    # ============================================================
    # Auto-unload watchdog
    # ============================================================

    async def start_watchdog(self):
        """Start the background task that auto-stops idle services."""
        if self._watchdog_task and not self._watchdog_task.done():
            return
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())
        logger.info("GPU watchdog started - idle services will be stopped after %ds", IDLE_TIMEOUT_SECONDS)

    async def stop_watchdog(self):
        """Stop the background watchdog task."""
        if self._watchdog_task:
            self._watchdog_task.cancel()
            self._watchdog_task = None
            logger.info("GPU watchdog stopped")

    async def _watchdog_loop(self):
        """Background loop: check for idle services and stop them."""
        while True:
            try:
                await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
                await self._check_idle_services()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Watchdog error: %s", e)

    async def _check_idle_services(self):
        """Stop services that have been idle for too long."""
        for name, service in SERVICES.items():
            if service.get("always_on"):
                continue
            if service.get("vram_mb", 0) == 0:
                continue

            status = await self.get_service_status(name)
            if status.get("status") != "online":
                continue

            idle_secs = self.get_idle_seconds(name)
            # Only stop if we have a valid idle time AND it exceeds the timeout
            if idle_secs is not None and idle_secs > IDLE_TIMEOUT_SECONDS:
                logger.info("Auto-unloading idle service '%s' (idle: %.0fs)", name, idle_secs)
                result = await self.stop_service(name)
                if "error" not in result:
                    logger.info("Auto-unloaded '%s' - freed ~%dMB VRAM", name, service.get("vram_mb", 0))
                else:
                    logger.warning("Failed to auto-unload '%s': %s", name, result.get("error"))

    # ============================================================
    # GPU Info
    # ============================================================

    def _find_nvidia_smi(self) -> Optional[str]:
        """Find nvidia-smi binary, checking common paths."""
        # Check PATH first
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            return nvidia_smi
        # Check common locations
        for path in [
            "/usr/bin/nvidia-smi",
            "/usr/local/bin/nvidia-smi",
            "/opt/cuda/bin/nvidia-smi",
            "/usr/lib/wsl/lib/nvidia-smi",  # WSL
        ]:
            if os.path.exists(path):
                return path
        return None

    async def get_gpu_info(self) -> Dict:
        """Get current GPU information using nvidia-smi."""
        try:
            nvidia_smi = self._find_nvidia_smi()
            if not nvidia_smi:
                logger.warning("nvidia-smi not found in PATH or common locations.")
                return {
                    "total_vram_mb": GPU_TOTAL_VRAM_MB,
                    "used_vram_mb": None,
                    "free_vram_mb": None,
                    "error": "nvidia-smi not found",
                }

            result = subprocess.run(
                [
                    nvidia_smi,
                    "--query-gpu=name,memory.total,memory.used,memory.free,"
                    "utilization.gpu,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                parts = [p.strip() for p in result.stdout.strip().split(",")]
                return {
                    "gpu_name": parts[0],
                    "total_vram_mb": int(float(parts[1])),
                    "used_vram_mb": int(float(parts[2])),
                    "free_vram_mb": int(float(parts[3])),
                    "gpu_utilization": float(parts[4]),
                    "temperature": float(parts[5]),
                }
        except subprocess.TimeoutExpired:
            logger.warning("nvidia-smi timed out.")
        except Exception as e:
            logger.error(f"GPU info error: {e}")

        return {
            "total_vram_mb": GPU_TOTAL_VRAM_MB,
            "used_vram_mb": None,
            "free_vram_mb": None,
        }

    # ============================================================
    # Service Status
    # ============================================================

    async def get_service_status(self, service_name: str) -> Dict:
        """Get the status of a specific service."""
        service = SERVICES.get(service_name)
        if not service:
            return {"error": f"Unknown service: {service_name}"}

        if service.get("systemd_service"):
            return await self._check_systemd_service(service["systemd_service"])
        elif service.get("docker_compose"):
            return await self._check_docker_service(service_name)
        # For services without systemd/docker, check HTTP health
        return await self._check_http_health(service)

    async def get_all_services_status(self) -> List[Dict]:
        """Get status of all registered services."""
        statuses = []
        for name, service in SERVICES.items():
            health = await self.get_service_status(name)
            idle_secs = self.get_idle_seconds(name) if health.get("status") == "online" else None
            statuses.append({
                "name": name,
                "display_name": service["name"],
                "status": health.get("status", "unknown"),
                "url": service["base_url"],
                "port": service["port"],
                "type": service["type"],
                "categories": service.get("categories", []),
                "vram_mb": service.get("vram_mb", 0),
                "always_on": service.get("always_on", False),
                "idle_seconds": round(idle_secs) if idle_secs is not None else None,
                "response_time_ms": health.get("response_time_ms"),
                "error": health.get("error"),
            })
        return statuses

    # ============================================================
    # Start / Stop Services
    # ============================================================

    async def start_service(self, service_name: str) -> Dict:
        """Start a service, checking VRAM availability first."""
        service = SERVICES.get(service_name)
        if not service:
            return {"error": f"Unknown service: {service_name}"}

        # Check if already running
        status = await self.get_service_status(service_name)
        if status.get("status") == "online":
            self.mark_service_used(service_name)
            return {"status": "already_running", "message": f"{service['name']} is already running"}

        # Check VRAM availability
        gpu_info = await self.get_gpu_info()
        free_vram = gpu_info.get("free_vram_mb") or 0
        needed_vram = service.get("vram_mb", 0)

        if free_vram > 0 and needed_vram > free_vram:
            freed = await self._free_vram(needed_vram - free_vram, exclude=service_name)
            if not freed and needed_vram > free_vram:
                return {
                    "error": "Insufficient VRAM",
                    "free_vram_mb": free_vram,
                    "needed_vram_mb": needed_vram,
                    "message": f"Need {needed_vram}MB but only {free_vram}MB free.",
                }

        self.mark_service_used(service_name)
        if service.get("systemd_service"):
            return await self._start_systemd_service(service["systemd_service"], service["name"])
        elif service.get("docker_compose"):
            return await self._start_docker_service(service_name, service["name"])
        return {"status": "no_action", "message": f"{service['name']} has no start method (HTTP-only)"}

    async def stop_service(self, service_name: str) -> Dict:
        """Stop a running service to free VRAM."""
        service = SERVICES.get(service_name)
        if not service:
            return {"error": f"Unknown service: {service_name}"}

        if service.get("always_on"):
            return {"error": f"Cannot stop {service['name']} - it's marked as always_on"}

        if service.get("systemd_service"):
            return await self._stop_systemd_service(service["systemd_service"], service["name"])
        elif service.get("docker_compose"):
            return await self._stop_docker_service(service_name, service["name"])
        return {"status": "no_action", "message": f"{service['name']} has no stop method (HTTP-only)"}

    async def _free_vram(self, needed_mb: int, exclude: str = "") -> bool:
        """Try to free VRAM by stopping non-essential services."""
        freed = 0
        for name, service in SERVICES.items():
            if name == exclude or service.get("always_on"):
                continue
            status = await self.get_service_status(name)
            if status.get("status") == "online":
                result = await self.stop_service(name)
                if "error" not in result:
                    freed += service.get("vram_mb", 0)
                    if freed >= needed_mb:
                        return True
        return freed >= needed_mb

    # ============================================================
    # Health Check Methods
    # ============================================================

    async def _check_http_health(self, service: Dict) -> Dict:
        """Check service health via HTTP."""
        import httpx
        url = service["base_url"] + service.get("health_endpoint", "/")
        try:
            start = time.time()
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=15.0)
                elapsed_ms = int((time.time() - start) * 1000)
                if resp.status_code < 500:
                    return {"status": "online", "response_time_ms": elapsed_ms}
                return {"status": "offline", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "offline", "error": str(e)[:100]}

    async def _check_systemd_service(self, service_name: str) -> Dict:
        """Check if a systemd service is active AND responding on HTTP."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True, timeout=5,
            )
            status = result.stdout.strip()
            if status == "active":
                # Also verify HTTP health if we have a base_url for this service
                for svc_name, svc_config in SERVICES.items():
                    if svc_config.get("systemd_service") == service_name:
                        return await self._check_http_health(svc_config)
                return {"status": "online"}
            elif status in ("inactive", "failed"):
                return {"status": "offline"}
            elif status == "activating":
                return {"status": "unknown", "error": "activating"}
            return {"status": "unknown", "error": status}
        except Exception as e:
            return {"status": "unknown", "error": str(e)}

    async def _check_docker_service(self, service_name: str) -> Dict:
        """Check if a Docker container is running AND responding on HTTP."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Status}}"],
                capture_output=True, text=True, timeout=10,
            )
            if not result.stdout.strip():
                return {"status": "offline"}

            # Container is running - also verify HTTP health if we have a URL
            service = SERVICES.get(service_name)
            if service and service.get("base_url"):
                return await self._check_http_health(service)
            return {"status": "online"}
        except Exception:
            return {"status": "unknown"}

    # ============================================================
    # Systemd Start/Stop (passwordless sudo or SUDO_PASSWORD env var)
    # ============================================================

    def _build_sudo_cmd(self, base_cmd: List[str]) -> tuple:
        """Build sudo command. Returns (cmd_list, stdin_data)."""
        if SUDO_PASSWORD:
            return (["sudo", "-S"] + base_cmd, SUDO_PASSWORD + "\n")
        return (["sudo"] + base_cmd, None)

    async def _start_systemd_service(self, systemd_name: str, display_name: str) -> Dict:
        """Start a systemd service. Uses passwordless sudo or SUDO_PASSWORD env var."""
        try:
            # Try direct first (if running as root or systemd user)
            result = subprocess.run(
                ["systemctl", "start", systemd_name],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {"status": "started", "message": f"{display_name} started successfully"}
            # Try with sudo
            cmd, stdin_data = self._build_sudo_cmd(["systemctl", "start", systemd_name])
            result = subprocess.run(
                cmd,
                input=stdin_data, capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {"status": "started", "message": f"{display_name} started successfully"}
            return {"error": f"Failed to start: {result.stderr.strip()}"}
        except Exception as e:
            return {"error": str(e)}

    async def _stop_systemd_service(self, systemd_name: str, display_name: str) -> Dict:
        """Stop a systemd service. Uses passwordless sudo or SUDO_PASSWORD env var."""
        try:
            # Try direct first
            result = subprocess.run(
                ["systemctl", "stop", systemd_name],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {"status": "stopped", "message": f"{display_name} stopped. VRAM freed."}
            # Try with sudo
            cmd, stdin_data = self._build_sudo_cmd(["systemctl", "stop", systemd_name])
            result = subprocess.run(
                cmd,
                input=stdin_data, capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {"status": "stopped", "message": f"{display_name} stopped. VRAM freed."}
            return {"error": f"Failed to stop: {result.stderr.strip()}"}
        except Exception as e:
            return {"error": str(e)}

    # ============================================================
    # Docker Start/Stop (Docker Compose)
    # ============================================================

    async def _start_docker_service(self, service_name: str, display_name: str) -> Dict:
        """Start a Docker Compose service."""
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d", service_name],
                capture_output=True, text=True, timeout=60,
                cwd=DOCKER_COMPOSE_DIR,
            )
            if result.returncode == 0:
                return {"status": "started", "message": f"{display_name} started successfully"}
            return {"error": f"Failed to start: {result.stderr.strip()[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    async def _stop_docker_service(self, service_name: str, display_name: str) -> Dict:
        """Stop a Docker Compose service."""
        try:
            result = subprocess.run(
                ["docker", "compose", "stop", service_name],
                capture_output=True, text=True, timeout=60,
                cwd=DOCKER_COMPOSE_DIR,
            )
            if result.returncode == 0:
                return {"status": "stopped", "message": f"{display_name} stopped. VRAM freed."}
            return {"error": f"Failed to stop: {result.stderr.strip()[:200]}"}
        except Exception as e:
            return {"error": str(e)}