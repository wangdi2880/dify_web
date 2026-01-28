import os
import json
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict
from pydantic import BaseModel
from service.dify_service import dify_service

router = APIRouter(prefix="/api/dify", tags=["Dify"])

# 文件路径配置
# Vercel 环境下只有 /tmp 目录可写
if os.environ.get("VERCEL"):
    FILES_DIR = "/tmp/files"
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILES_DIR = os.path.join(BASE_DIR, "files")

CONFIG_FILE = os.path.join(FILES_DIR, "dify_configs.json")
HISTORY_FILE = os.path.join(FILES_DIR, "dify_history.json")

# 初始化文件
try:
    os.makedirs(FILES_DIR, exist_ok=True)
    for f_path in [CONFIG_FILE, HISTORY_FILE]:
        if not os.path.exists(f_path):
            with open(f_path, 'w', encoding='utf-8') as f: 
                json.dump([], f)
except Exception as e:
    print(f"Warning: Could not initialize files: {e}")

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f: return json.load(f)

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

class DifyConfig(BaseModel):
    id: str
    name: str
    service_type: str = "dify"
    method: str = "POST"
    url: str
    headers: Dict[str, str] = {}
    timeout: int = 120
    stream: bool = True

# --- 配置管理 ---
@router.get("/configs")
def get_configs():
    return read_json(CONFIG_FILE)

@router.post("/configs")
def save_config(config: DifyConfig):
    configs = read_json(CONFIG_FILE)
    # Upsert logic
    existing = False
    for i, c in enumerate(configs):
        if c['id'] == config.id:
            configs[i] = config.dict()
            existing = True
            break
    if not existing:
        configs.append(config.dict())
    write_json(CONFIG_FILE, configs)
    return {"status": "success"}

@router.delete("/configs/{config_id}")
def delete_config(config_id: str):
    configs = [c for c in read_json(CONFIG_FILE) if c['id'] != config_id]
    write_json(CONFIG_FILE, configs)
    return {"status": "success"}

# --- 历史记录 ---
@router.get("/history")
def get_history():
    return read_json(HISTORY_FILE)

# --- 运行工作流 ---
@router.post("/run")
async def run_workflow(
    config_id: str = Form(...),
    params_json: str = Form("{}"),
    files: List[UploadFile] = File(None)
):
    configs = read_json(CONFIG_FILE)
    config = next((c for c in configs if c['id'] == config_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    try:
        inputs = json.loads(params_json)
    except:
        inputs = {}

    # 保存调用历史 (Upsert based on config_id for simplicity)
    history = read_json(HISTORY_FILE)
    new_entry = {
        "config_id": config_id,
        "config_name": config['name'],
        "params_json": inputs, # 保存解析后的JSON
        "timestamp": "latest"
    }
    history = [h for h in history if h['config_id'] != config_id]
    history.insert(0, new_entry)
    write_json(HISTORY_FILE, history)

    return StreamingResponse(
        dify_service.run_workflow(
            config=config,
            inputs=inputs,
            files=files or [],
            user=inputs.get("user", "web-user")
        ),
        media_type="text/event-stream"
    )