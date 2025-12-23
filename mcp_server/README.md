## AMPRD MCP Server (optional)

This repository already provides a FastAPI Web UI (`webui/app.py`).  
This folder adds an **optional** MCP server wrapper so other tools can call:
- `generate_prd` (run pipeline)
- `evaluate_prd` (compute metrics)

### Install (optional)
Add the MCP dependency in your environment (kept optional to avoid breaking existing setups):

```bash
pip install mcp
```

### Run
```bash
python mcp_server/server.py
```

If you don't need MCP, ignore this folder and use the Web UI APIs instead:
- `POST /api/generate`
- `POST /api/evaluate`



