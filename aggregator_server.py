from fastapi import FastAPI
from dotenv import load_dotenv
import os
import requests
from vector_store import ToolVectorDB
from typing import List

load_dotenv()

MCP_SERVERS = os.getenv("MCP_SERVERS", "").split(",")

app = FastAPI()
vector_db = ToolVectorDB()

@app.on_event("startup")
def startup_event():
    for server_url in MCP_SERVERS:
        try:
            res = requests.get(f"{server_url}/.well-known/ai-plugin.json", timeout=5)
            if res.status_code == 200:
                plugin_info = res.json()
                tools = plugin_info.get("tools", [])
                for tool in tools:
                    vector_db.add_tool(
                        name=tool["name"],
                        description=tool["description"],
                        endpoint=server_url + "/tools/" + tool["name"]
                    )
        except Exception as e:
            print(f"[!] Failed to connect to {server_url}: {e}")

@app.get("/tools/mcp_aggregator")
def mcp_aggregator(search: str):
    """Returns best-matching tools and optionally calls them."""
    results = vector_db.search_tools(search)
    output = []
    for tool in results:
        try:
            r = requests.get(tool["endpoint"], params={"query": search})
            response = r.text
        except Exception as e:
            response = f"Failed to call: {e}"
        output.append({
            "name": tool["name"],
            "description": tool["description"],
            "endpoint": tool["endpoint"],
            "response": response
        })
    return {"matches": output}
