"""How busy the Pi is: processor, memory, temperature and its busiest processes.

The phone's Pi page shows these as stat cards and a list with meters. Every reading is
optional: a reading the machine cannot give is left out rather than guessed.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path


def _cpu_times() -> tuple[int, int] | None:
    try:
        fields = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
        values = [int(v) for v in fields]
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return idle, sum(values)
    except (OSError, ValueError, IndexError):
        return None


def _cpu_percent() -> float | None:
    """Processor use over a short sample, across all cores."""
    first = _cpu_times()
    if first is None:
        return None
    time.sleep(0.25)
    second = _cpu_times()
    if second is None or second[1] == first[1]:
        return None
    return round(100 * (1 - (second[0] - first[0]) / (second[1] - first[1])), 1)


def _memory() -> dict | None:
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            info[key] = int(value.split()[0]) * 1024
        total, available = info["MemTotal"], info.get("MemAvailable", info.get("MemFree", 0))
        return {"totalBytes": total, "usedBytes": total - available}
    except (OSError, KeyError, ValueError):
        return None


def _temperature() -> float | None:
    try:
        return round(int(Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def _processes(limit: int) -> list[dict]:
    try:
        out = subprocess.run(["ps", "-eo", "pid=,%cpu=,%mem=,comm="], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        try:
            row = {"pid": int(parts[0]), "cpu": float(parts[1]), "memory": float(parts[2]),
                   "name": parts[3].strip().rsplit("/", 1)[-1]}
        except ValueError:
            continue
        # ps measures itself from its own start, which reads as a busy process that is not one.
        if row["name"] != "ps":
            rows.append(row)
    rows.sort(key=lambda row: (row["cpu"], row["memory"]), reverse=True)
    return rows[:limit]


def snapshot(limit: int = 12) -> dict:
    """One reading of the Pi, with the busiest processes first."""
    reading: dict = {"processes": _processes(limit)}
    cpu = _cpu_percent()
    if cpu is not None:
        reading["cpuPercent"] = cpu
    memory = _memory()
    if memory is not None:
        reading["memory"] = memory
    temperature = _temperature()
    if temperature is not None:
        reading["temperatureC"] = temperature
    return reading
