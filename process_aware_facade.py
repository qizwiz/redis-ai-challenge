#!/usr/bin/env python3
"""
Process-Aware Facade
Tracks process lifecycle, crashes, and system health as part of facade state
"""

import fastmcp
import redis
import subprocess
import json
import time
import threading
import psutil
import signal
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cmdline: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: float


@dataclass
class SystemState:
    timestamp: float
    emacs_processes: List[ProcessInfo]
    mcp_servers: List[ProcessInfo]
    redis_status: Dict[str, Any]
    process_deaths: List[Dict[str, Any]]
    system_health: Dict[str, Any]


class ProcessAwareFacade:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.last_processes = {}
        self.process_deaths = []
        self.running = True

        # Start monitoring
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        print("🔍 Process-Aware Facade: Monitoring system health and process lifecycle")

    def get_emacs_processes(self) -> List[ProcessInfo]:
        """Get all Emacs-related processes"""
        emacs_processes = []

        try:
            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cmdline",
                    "status",
                    "cpu_percent",
                    "memory_percent",
                    "create_time",
                ]
            ):
                try:
                    if proc.info["name"] and "emacs" in proc.info["name"].lower():
                        emacs_processes.append(
                            ProcessInfo(
                                pid=proc.info["pid"],
                                name=proc.info["name"],
                                cmdline=" ".join(proc.info["cmdline"] or []),
                                status=proc.info["status"],
                                cpu_percent=proc.info["cpu_percent"] or 0.0,
                                memory_percent=proc.info["memory_percent"] or 0.0,
                                create_time=proc.info["create_time"],
                            )
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting Emacs processes: {e}")

        return emacs_processes

    def get_mcp_servers(self) -> List[ProcessInfo]:
        """Get all MCP server processes"""
        mcp_processes = []

        try:
            for proc in psutil.process_iter(
                [
                    "pid",
                    "name",
                    "cmdline",
                    "status",
                    "cpu_percent",
                    "memory_percent",
                    "create_time",
                ]
            ):
                try:
                    cmdline = " ".join(proc.info["cmdline"] or [])
                    if any(
                        keyword in cmdline
                        for keyword in [
                            "mcp",
                            "fastmcp",
                            "coordinator",
                            "facade",
                            "subagent",
                        ]
                    ):
                        mcp_processes.append(
                            ProcessInfo(
                                pid=proc.info["pid"],
                                name=proc.info["name"],
                                cmdline=cmdline,
                                status=proc.info["status"],
                                cpu_percent=proc.info["cpu_percent"] or 0.0,
                                memory_percent=proc.info["memory_percent"] or 0.0,
                                create_time=proc.info["create_time"],
                            )
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting MCP processes: {e}")

        return mcp_processes

    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis server health"""
        try:
            start_time = time.time()
            ping_result = self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000

            info = self.redis_client.info()

            return {
                "status": "healthy" if ping_result else "unhealthy",
                "ping_time_ms": ping_time,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "redis_version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "ping_time_ms": None}

    def detect_process_deaths(
        self, current_processes: Dict[int, ProcessInfo]
    ) -> List[Dict[str, Any]]:
        """Detect processes that died since last check"""
        deaths = []

        if self.last_processes:
            for old_pid, old_proc in self.last_processes.items():
                if old_pid not in current_processes:
                    death_event = {
                        "timestamp": time.time(),
                        "pid": old_pid,
                        "name": old_proc.name,
                        "cmdline": old_proc.cmdline,
                        "lived_seconds": time.time() - old_proc.create_time,
                        "death_type": "process_exit",
                    }
                    deaths.append(death_event)

                    # Store in persistent deaths list
                    self.process_deaths.append(death_event)
                    if len(self.process_deaths) > 50:  # Keep last 50 deaths
                        self.process_deaths = self.process_deaths[-50:]

        return deaths

    def detect_process_status_changes(
        self, current_processes: Dict[int, ProcessInfo]
    ) -> List[Dict[str, Any]]:
        """Detect process status changes (zombie, stopped, etc.)"""
        status_changes = []

        if self.last_processes:
            for pid, current_proc in current_processes.items():
                if pid in self.last_processes:
                    old_proc = self.last_processes[pid]
                    if old_proc.status != current_proc.status:
                        status_changes.append(
                            {
                                "timestamp": time.time(),
                                "pid": pid,
                                "name": current_proc.name,
                                "status_change": f"{old_proc.status} -> {current_proc.status}",
                                "cmdline": current_proc.cmdline[:100],
                            }
                        )

        return status_changes

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
                "boot_time": psutil.boot_time(),
            }
        except Exception as e:
            return {"error": str(e)}

    def _monitor_loop(self):
        """Main monitoring loop for process lifecycle"""
        while self.running:
            try:
                # Get current process state
                emacs_procs = self.get_emacs_processes()
                mcp_procs = self.get_mcp_servers()
                all_processes = {p.pid: p for p in emacs_procs + mcp_procs}

                # Detect deaths and status changes
                deaths = self.detect_process_deaths(all_processes)
                status_changes = self.detect_process_status_changes(all_processes)

                # Check Redis health
                redis_health = self.check_redis_health()

                # Get system health
                system_health = self.get_system_health()

                # Create system state snapshot
                system_state = SystemState(
                    timestamp=time.time(),
                    emacs_processes=emacs_procs,
                    mcp_servers=mcp_procs,
                    redis_status=redis_health,
                    process_deaths=list(self.process_deaths),
                    system_health=system_health,
                )

                # Store system state in facade
                self.redis_client.set("system:facade", json.dumps(asdict(system_state)))

                # Log significant events
                if deaths:
                    print(f"💀 PROCESS DEATHS DETECTED: {len(deaths)}")
                    for death in deaths:
                        print(
                            f"   • PID {death['pid']}: {death['name']} ({death['cmdline'][:50]})"
                        )

                        # Send death notification to Redis stream
                        self.redis_client.xadd(
                            "system:process_deaths",
                            {
                                "timestamp": death["timestamp"],
                                "pid": death["pid"],
                                "name": death["name"],
                                "cmdline": death["cmdline"],
                                "lived_seconds": death["lived_seconds"],
                            },
                        )

                if status_changes:
                    print(f"🔄 STATUS CHANGES: {len(status_changes)}")
                    for change in status_changes:
                        print(f"   • PID {change['pid']}: {change['status_change']}")

                        self.redis_client.xadd("system:status_changes", change)

                # Health alerts
                if redis_health["status"] != "healthy":
                    print(f"🚨 REDIS HEALTH ISSUE: {redis_health}")

                if system_health.get("cpu_percent", 0) > 90:
                    print(f"⚠️ HIGH CPU: {system_health['cpu_percent']}%")

                if system_health.get("memory_percent", 0) > 90:
                    print(f"⚠️ HIGH MEMORY: {system_health['memory_percent']}%")

                # Update last known state
                self.last_processes = all_processes

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)


# FastMCP Server
mcp = fastmcp.FastMCP("process-aware-facade")
facade = ProcessAwareFacade()


@mcp.tool()
def get_process_health() -> str:
    """Get current process health and lifecycle status"""
    try:
        system_state_json = facade.redis_client.get("system:facade")
        if not system_state_json:
            return "❌ No system state available"

        system_state = json.loads(system_state_json)

        result = f"""🔍 **PROCESS-AWARE FACADE STATE**

📊 **Emacs Processes:** {len(system_state['emacs_processes'])}
📊 **MCP Servers:** {len(system_state['mcp_servers'])}
📊 **Recent Deaths:** {len(system_state['process_deaths'])}

🎯 **Redis Health:**
Status: {system_state['redis_status']['status']}
Ping: {system_state['redis_status'].get('ping_time_ms', 'N/A')}ms
Clients: {system_state['redis_status'].get('connected_clients', 'N/A')}

🖥️ **System Health:**
CPU: {system_state['system_health'].get('cpu_percent', 'N/A')}%
Memory: {system_state['system_health'].get('memory_percent', 'N/A')}%
Disk: {system_state['system_health'].get('disk_percent', 'N/A')}%
"""
        return result

    except Exception as e:
        return f"❌ Error getting process health: {e}"


@mcp.tool()
def get_recent_deaths(count: int = 5) -> str:
    """Get recent process deaths"""
    try:
        deaths = facade.redis_client.xrevrange("system:process_deaths", count=count)

        if not deaths:
            return "✅ No recent process deaths"

        result = "💀 **RECENT PROCESS DEATHS**\n"
        for death_id, fields in deaths:
            timestamp = float(fields.get("timestamp", 0))
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            pid = fields.get("pid", "unknown")
            name = fields.get("name", "unknown")
            lived = float(fields.get("lived_seconds", 0))

            result += f"\n[{time_str}] PID {pid}: {name}"
            result += f"\n   Lived: {lived:.1f}s"
            result += f"\n   Command: {fields.get('cmdline', 'unknown')[:60]}...\n"

        return result

    except Exception as e:
        return f"❌ Error getting deaths: {e}"


@mcp.tool()
def check_mcp_server_health() -> str:
    """Check health of all MCP servers"""
    try:
        system_state_json = facade.redis_client.get("system:facade")
        if not system_state_json:
            return "❌ No system state available"

        system_state = json.loads(system_state_json)
        mcp_servers = system_state["mcp_servers"]

        if not mcp_servers:
            return "⚠️ No MCP servers detected"

        result = f"🖥️ **MCP SERVER HEALTH** ({len(mcp_servers)} servers)\n"

        for server in mcp_servers:
            result += f"\n• PID {server['pid']}: {server['name']}"
            result += f"\n  Status: {server['status']}"
            result += f"\n  CPU: {server['cpu_percent']:.1f}%"
            result += f"\n  Memory: {server['memory_percent']:.1f}%"
            result += f"\n  Command: {server['cmdline'][:50]}...\n"

        return result

    except Exception as e:
        return f"❌ Error checking MCP health: {e}"


if __name__ == "__main__":
    print("🚀 Starting Process-Aware Facade...")
    print("   • Monitoring process lifecycle and deaths")
    print("   • Tracking system health in real-time")
    print("   • Available as MCP tools for integration")
    mcp.run()
