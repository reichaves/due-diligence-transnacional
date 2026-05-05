"""
Wrapper that loads .env from the project root before starting the FEC MCP server.
This allows users to store API keys in .env without setting system environment variables.
"""

import os
import runpy
import sys
from pathlib import Path

# Locate .env relative to this script (project root)
env_file = Path(__file__).resolve().parent.parent / ".env"

if env_file.exists():
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)

# Hand off to the actual FEC MCP server
server_script = "E:/Code/fec-mcp-server/repo/start_server.py"
sys.argv = [server_script]
runpy.run_path(server_script, run_name="__main__")
