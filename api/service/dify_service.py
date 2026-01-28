import json
import aiohttp
import mimetypes
import logging
from typing import Optional, Tuple, AsyncGenerator, Dict, Any, List
from fastapi import UploadFile

logger = logging.getLogger("DifyService")
logger.setLevel(logging.INFO)

class DifyService:
    def _get_file_type_from_mime(self, mime_type: str) -> str:
        if mime_type.startswith("image/"):
            return "image"
        return "document"

    async def upload_file(self, file: UploadFile, config: Dict[str, Any], user: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """上传文件到 Dify"""
        base_url = config.get("url", "").split("/v1/")[0]
        upload_url = f"{base_url}/v1/files/upload"
        
        # 复制Header并移除Content-Type (由FormData自动生成)
        headers = {k: v for k, v in config.get("headers", {}).items() if k.lower() != "content-type"}
        if "Authorization" in headers and not headers["Authorization"].strip().startswith("Bearer "):
            headers["Authorization"] = f"Bearer {headers['Authorization'].strip()}"
        
        try:
            content = await file.read()
            mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            
            form_data = aiohttp.FormData()
            form_data.add_field('file', content, filename=file.filename, content_type=mime_type)
            form_data.add_field('user', user)

            timeout = aiohttp.ClientTimeout(total=config.get("timeout", 60))
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(upload_url, headers=headers, data=form_data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        file_id = result.get("id")
                        res_mime = result.get("mime_type", mime_type)
                        return file_id, res_mime, None
                    else:
                        error_text = await response.text()
                        return None, None, f"Status {response.status}: {error_text}"
        except Exception as e:
            return None, None, str(e)
        finally:
            await file.seek(0)

    async def run_workflow(self, config: Dict[str, Any], inputs: Dict[str, Any], files: List[UploadFile] = None, user: str = "api-user") -> AsyncGenerator[str, None]:
        """执行工作流 (流式)"""
        run_url = config.get("url")
        headers = config.get("headers", {}).copy()
        if "Authorization" in headers and not headers["Authorization"].strip().startswith("Bearer "):
            headers["Authorization"] = f"Bearer {headers['Authorization'].strip()}"
        headers["Content-Type"] = "application/json"
        
        # 1. 处理文件上传
        uploaded_files_info = []
        if files:
            yield json.dumps({"event": "sys_log", "message": "正在上传文件..."}) + "\n"
            for file in files:
                file_id, mime_type, err = await self.upload_file(file, config, user)
                if err:
                    yield json.dumps({"error": f"上传失败: {err}"})
                    return
                
                uploaded_files_info.append({
                    "type": self._get_file_type_from_mime(mime_type),
                    "transfer_method": "local_file",
                    "upload_file_id": file_id
                })
            yield json.dumps({"event": "sys_log", "message": "文件上传完成，开始执行工作流..."}) + "\n"

        # 2. 构造参数
        final_inputs = inputs.copy()
        # 兼容性处理：如果有文件，尝试注入到 inputs
        if uploaded_files_info:
            # 如果是单个文件，且inputs为空，或者按照你样例代码的习惯
            if "files" not in final_inputs:
                final_inputs["files"] = uploaded_files_info # 通用
            # 如果你的工作流特定使用 base_input 接收文件
            # final_inputs["base_input"] = uploaded_files_info[0] 

        payload = {
            "inputs": final_inputs,
            "response_mode": "streaming" if config.get("stream") else "blocking",
            "user": user
        }

        # 3. 发送请求
        try:
            timeout = aiohttp.ClientTimeout(total=config.get("timeout", 120))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(run_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        err = await response.text()
                        yield json.dumps({"error": f"API Error {response.status}: {err}"})
                        return

                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if not line_str or line_str.startswith("event: ping"): continue
                        
                        if line_str.startswith("data: "):
                            try:
                                data = json.loads(line_str[6:])
                                event = data.get("event")
                                if event == "text_chunk":
                                    yield data.get("data", {}).get("text", "")
                                elif event == "workflow_finished":
                                    pass
                                elif event == "error":
                                    yield f"\n[Error: {data.get('message')}]"
                            except: pass
                        else:
                            # 处理非流式返回 (Blocking)
                            try:
                                full = json.loads(line_str)
                                # 尝试获取 answer 或 outputs
                                res = full.get("data", {}).get("answer") or full.get("data", {}).get("outputs") or str(full)
                                yield str(res)
                            except: pass
        except Exception as e:
            yield json.dumps({"error": str(e)})

dify_service = DifyService()