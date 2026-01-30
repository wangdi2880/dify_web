import json
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Body
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict
from pydantic import BaseModel
from service.dify_service import dify_service

router = APIRouter(prefix="/api/dify", tags=["Dify"])


class DifyConfig(BaseModel):
    id: str
    name: str
    service_type: str = "dify"
    method: str = "POST"
    url: str
    headers: Dict[str, str] = {}
    timeout: int = 120
    stream: bool = True

@router.post("/parameters")
async def get_parameters(config: DifyConfig):
    try:
        # Convert Pydantic model to dict for service layer
        config_dict = config.dict()
        data = await dify_service.get_parameters(config_dict)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 运行工作流 ---
@router.post("/run")
async def run_workflow(
    config_json: str = Form(...),
    params_json: str = Form("{}"),
    files: List[UploadFile] = File(None)
):
    try:
        config_dict = json.loads(config_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid config_json")

    try:
        inputs = json.loads(params_json)
    except:
        inputs = {}


    # 预读取文件内容，防止 StreamingResponse 导致文件关闭
    pre_read_files = []
    if files:
        for f in files:
            content = await f.read()
            pre_read_files.append({
                "filename": f.filename,
                "content": content
            })

    return StreamingResponse(
        dify_service.run_workflow(
            config=config_dict,
            inputs=inputs,
            files=pre_read_files,
            user=inputs.get("user", "web-user")
        ),
        media_type="text/event-stream"
    )