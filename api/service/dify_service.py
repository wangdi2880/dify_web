import json
import aiohttp
import mimetypes
import logging
import io
from typing import Optional, Tuple, AsyncGenerator, Dict, Any, List
from fastapi import UploadFile

logger = logging.getLogger("DifyService")
logger.setLevel(logging.INFO)

class DifyService:
    def _get_file_type_from_mime(self, mime_type: str) -> str:
        if mime_type.startswith("image/"):
            return "image"
        return "document"

    async def upload_file(self, filename: str, content: bytes, config: Dict[str, Any], user: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """上传文件到 Dify"""
        base_url = config.get("url", "").split("/v1/")[0]
        upload_url = f"{base_url}/v1/files/upload"
        
        # 复制Header并移除Content-Type (由FormData自动生成)
        headers = {k: v for k, v in config.get("headers", {}).items() if k.lower() != "content-type"}
        if "Authorization" in headers and not headers["Authorization"].strip().startswith("Bearer "):
            headers["Authorization"] = f"Bearer {headers['Authorization'].strip()}"
        
        try:
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            
            form_data = aiohttp.FormData()
            form_data.add_field('file', io.BytesIO(content), filename=filename, content_type=mime_type)
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

    async def run_workflow(self, config: Dict[str, Any], inputs: Dict[str, Any], files: List[Dict[str, Any]] = None, user: str = "api-user") -> AsyncGenerator[str, None]:
        """执行工作流 (流式)"""
        try:
            run_url = config.get("url")
            headers = config.get("headers", {}).copy()
            if "Authorization" in headers and not headers["Authorization"].strip().startswith("Bearer "):
                headers["Authorization"] = f"Bearer {headers['Authorization'].strip()}"
            headers["Content-Type"] = "application/json"
            
            # 1. 处理文件上传并映射到变量
            final_inputs = inputs.copy()
            
            if files:
                for f_data in files:
                    try:
                        full_filename = f_data.get("filename", "")
                        if "#" in full_filename:
                            var_name, real_filename = full_filename.split("#", 1)
                        else:
                            var_name, real_filename = "file", full_filename
                            
                        content = f_data.get("content")
                        file_id, mime_type, err = await self.upload_file(real_filename, content, config, user)
                        
                        if err:
                            logger.error(f"文件上传失败 ({real_filename}): {err}")
                            yield json.dumps({"error": f"上传失败: {err}"}) + "\n"
                            return
                        
                        file_info = {
                            "type": self._get_file_type_from_mime(mime_type),
                            "transfer_method": "local_file",
                            "upload_file_id": file_id
                        }
                        
                        # 核心逻辑：如果是单文件，直接传对象；如果是多文件，Dify文档通常也是传数组
                        # 这里修复 "pdf in input form must be a file" 报错，尝试直接传对象而非数组
                        final_inputs[var_name] = file_info
                        
                    except Exception as fe:
                        logger.error(f"文件处理异常: {str(fe)}", exc_info=True)
                        yield json.dumps({"error": f"单个文件处理异常: {str(fe)}"}) + "\n"
                        return

            # 2. 构造最终 Payload
            # 工作流 API 应当只使用 inputs 来传递文件变量，移除根目录的 files 已防冲突
            payload = {
                "inputs": final_inputs,
                "response_mode": "streaming" if config.get("stream") else "blocking",
                "user": user
            }
            logger.info(f"发送至 Dify Payload: {json.dumps(payload, ensure_ascii=False)}")

            # 3. 发送请求
            timeout = aiohttp.ClientTimeout(total=config.get("timeout", 120))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(run_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        err = await response.text()
                        yield json.dumps({"error": f"API Error {response.status}: {err}"}) + "\n"
                        return

                    # 根据是否为流式模式处理
                    if config.get("stream"):
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
                                        yield json.dumps(data, ensure_ascii=False) + "\n"
                                    elif event == "error":
                                        yield f"\n[Error: {data.get('message')}]"
                                except: pass
                    else:
                        # 阻塞模式：直接读取完整结果
                        full_resp = await response.json()
                        # 对于工作流，结果通常在 data.outputs 中
                        # 对于聊天，结果在 data.answer 中
                        data = full_resp.get("data", {}) if "data" in full_resp else full_resp
                        result = data.get("outputs") or data.get("answer") or str(full_resp)
                        
                        if isinstance(result, dict):
                            yield json.dumps(result, ensure_ascii=False, indent=2) + "\n"
                        else:
                            yield str(result) + "\n"
                            
        except Exception as e:
            logger.error(f"run_workflow 发生异常: {str(e)}", exc_info=True)
            yield json.dumps({"error": f"执行异常: {str(e)}"}) + "\n"


    async def get_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取 Dify 应用参数"""
        base_url = config.get("url", "").split("/v1/")[0]
        url = f"{base_url}/v1/parameters"
        
        headers = config.get("headers", {}).copy()
        auth = headers.get("Authorization", "").strip()
        if auth and not auth.startswith("Bearer "):
            headers["Authorization"] = f"Bearer {auth}"
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Dify Error {response.status}: {text}")
                return await response.json()

dify_service = DifyService()

