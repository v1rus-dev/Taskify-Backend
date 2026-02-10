import os
import time
from datetime import datetime, timezone

import psutil


def _human_bytes(num_bytes: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def _resolve_disk_path(path: str) -> str:
    if path and os.path.exists(path):
        return path
    return "/"


def _host_proc_root() -> str | None:
    path = "/hostfs/proc"
    if os.path.isdir(path):
        return path
    return None


def _read_host_cpu_percent(proc_root: str) -> float | None:
    stat_path = os.path.join(proc_root, "stat")

    def read_times() -> tuple[int, int] | None:
        try:
            with open(stat_path, "r", encoding="utf-8") as stat_file:
                first_line = stat_file.readline().strip()
        except OSError:
            return None

        parts = first_line.split()
        if len(parts) < 8 or parts[0] != "cpu":
            return None

        values = [int(value) for value in parts[1:]]
        idle = values[3] + values[4]
        total = sum(values)
        return total, idle

    start = read_times()
    if not start:
        return None
    time.sleep(0.2)
    end = read_times()
    if not end:
        return None

    total_delta = end[0] - start[0]
    idle_delta = end[1] - start[1]
    if total_delta <= 0:
        return None
    return (1 - (idle_delta / total_delta)) * 100


def _read_host_mem_percent(proc_root: str) -> tuple[float, int, int] | None:
    meminfo_path = os.path.join(proc_root, "meminfo")
    try:
        with open(meminfo_path, "r", encoding="utf-8") as meminfo_file:
            lines = meminfo_file.readlines()
    except OSError:
        return None

    parsed: dict[str, int] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parts = value.strip().split()
        if not parts:
            continue
        try:
            parsed[key] = int(parts[0]) * 1024
        except ValueError:
            continue

    total = parsed.get("MemTotal")
    available = parsed.get("MemAvailable")
    if not total or available is None:
        return None

    used = total - available
    percent = (used / total) * 100
    return percent, used, total


def _read_host_load_avg(proc_root: str) -> str | None:
    loadavg_path = os.path.join(proc_root, "loadavg")
    try:
        with open(loadavg_path, "r", encoding="utf-8") as loadavg_file:
            parts = loadavg_file.read().strip().split()
    except OSError:
        return None

    if len(parts) < 3:
        return None
    return f"{parts[0]} / {parts[1]} / {parts[2]}"


def collect_system_stats(disk_path: str) -> dict[str, str]:
    metrics_scope = "container"
    cpu_percent = psutil.cpu_percent(interval=0.3)
    memory = psutil.virtual_memory()

    host_proc = _host_proc_root()
    if host_proc:
        host_cpu = _read_host_cpu_percent(host_proc)
        host_mem = _read_host_mem_percent(host_proc)
        if host_cpu is not None:
            cpu_percent = host_cpu
        if host_cpu is not None or host_mem is not None:
            metrics_scope = "host"
        if host_mem is not None:
            memory_percent, memory_used, memory_total = host_mem
        else:
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
        load_avg = _read_host_load_avg(host_proc)
    else:
        memory_percent = memory.percent
        memory_used = memory.used
        memory_total = memory.total
        load_avg = None

    effective_disk_path = _resolve_disk_path(disk_path)
    disk = psutil.disk_usage(effective_disk_path)
    boot_at = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if load_avg is None and hasattr(os, "getloadavg"):
        la1, la5, la15 = os.getloadavg()
        load_avg = f"{la1:.2f} / {la5:.2f} / {la15:.2f}"
    if load_avg is None:
        load_avg = "n/a"

    return {
        "cpu_percent": f"{cpu_percent:.1f}%",
        "load_average": load_avg,
        "memory_percent": f"{memory_percent:.1f}%",
        "memory_used": _human_bytes(memory_used),
        "memory_total": _human_bytes(memory_total),
        "disk_percent": f"{disk.percent:.1f}%",
        "disk_used": _human_bytes(disk.used),
        "disk_total": _human_bytes(disk.total),
        "disk_free": _human_bytes(disk.free),
        "disk_path": effective_disk_path,
        "boot_at": boot_at,
        "metrics_scope": metrics_scope,
    }
