import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import redis
import os

# Absolute path to the directory containing the scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
REDIS_CLI = redis.Redis(decode_responses=True)

@app.get("/", response_class=HTMLResponse)
async def get_visualization_page():
    with open(os.path.join(SCRIPT_DIR, "visualization.html"), "r") as f:
        return f.read()

@app.get("/api/log")
async def get_supervisor_log():
    # Fetch the last 100 entries from the supervisor log stream
    log_entries = REDIS_CLI.xrange("supervisor:log", count=100)
    
    formatted_logs = []
    for entry_id, entry_data in log_entries:
        decoded_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in entry_data.items()}
        formatted_logs.append({
            "id": entry_id.decode('utf-8'),
            "data": decoded_data
        })
    return {"logs": formatted_logs}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
