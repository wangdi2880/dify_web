
# 前端 (Frontend)
	位于 frontend/ 目录：

	核心框架: Vue 3 (^3.3.4)
	构建工具: Vite (^4.4.5) - 提供极速的开发服务器和构建功能。
	编程语言: TypeScript (^5.6.3) - 增加了类型安全。
	UI 组件库: Element Plus (^2.4.1) - 基于 Vue 3 的桌面端组件库。
	路由管理: Vue Router (^4.6.4)。
	HTTP 客户端: Axios (^1.4.0)。
	Markdown 渲染: marked - 用于解析和渲染 Markdown 内容。

# 后端 (Backend)
	位于 api/ 目录：

	核心框架: FastAPI - 一个现代、高性能的 Python Web 框架。
	入口文件为 
	api/index.py
	。
	服务器: uvicorn - 用于运行 FastAPI 应用的 ASGI 服务器。
	异步请求: aiohttp - 用于处理异步 HTTP 请求。
	数据处理: python-multipart - 用于解析表单数据（通常用于文件上传）。

# 部署与架构
	部署配置: 项目根目录下包含 vercel.json，表明该项目可能配置为部署在 Vercel 平台上，或者使用了类似的 Serverless 架构。
	跨域处理: 后端 (api/index.py) 配置了 CORSMiddleware，允许来自任何来源 (*) 的跨域请求，方便前后端联调。

# 本地起后端服务：
	cd api
	pip install -r requirements.txt
	uvicorn index:app --reload

# 本地起前端服务：
	cd frontend
	npm install
	npm run dev