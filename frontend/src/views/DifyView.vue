<template>
  <div class="dify-container">
    <el-header class="page-header">
      <div class="left">
        <el-button icon="Back" circle @click="$router.push('/')" />
        <h3 class="title">Dify Workflow Manager</h3>
      </div>
    </el-header>

    <el-main class="dify-main">
      <el-row :gutter="20" class="h-100">
        <!-- Main Area: Config & Run -->
        <el-col :span="24" class="h-100">
          <el-card shadow="never" class="h-100 main-card" v-if="currentConfig.id">
            <div class="scroll-container">
              <!-- api config section -->
              <div class="compact-block config-block">
                <div class="config-row">
                  <span class="label-text">API URL:</span>
                  <el-input v-model="currentConfig.url" placeholder="http://.../v1/workflows/run" style="flex: 1;" />
                  <el-button type="success" :loading="loading" icon="Promotion" @click="executeRun" style="margin-left: 10px; width: 120px;">
                    发送请求
                  </el-button>
                </div>

                <div class="config-row mt-2">
                   <span class="label-text">API KEY:</span>
                   <el-input v-model="currentConfig.headers['Authorization']" placeholder="Bearer app-xxxx..." style="flex: 1;" />
                </div>

                <div class="config-row mt-2">
                   <div class="flex-item">
                      <span class="label-text">超时(s):</span>
                      <el-input-number v-model="currentConfig.timeout" :min="10" size="default" style="width: 120px;" />
                   </div>
                   <div class="flex-item ml-4">
                      <span class="label-text">流式响应:</span>
                      <el-switch v-model="currentConfig.stream" />
                   </div>
                </div>

                <div class="config-row mt-2 headers-row">
                    <span class="label-text" style="align-self: flex-start; margin-top: 5px;">Headers:</span>
                    <div class="headers-container">
                      <div v-for="(val, key) in currentConfig.headers" :key="key" class="kv-row">
                        <template v-if="key !== 'Authorization' && key !== 'Content-Type'">
                           <el-input :model-value="key" @input="v => updateHeaderKey(key, v)" placeholder="Key" style="width: 30%;" size="small" />
                           <span class="mx-2">:</span>
                           <el-input v-model="currentConfig.headers[key]" placeholder="Value" style="width: 50%;" size="small" />
                           <el-button icon="Delete" link type="danger" @click="delete currentConfig.headers[key]" />
                        </template>
                      </div>
                      <el-button size="small" icon="Plus" link @click="addHeader">添加 Header</el-button>
                    </div>
                </div>
              </div>

              <!-- parameters section -->
              <div class="run-section compact-block params-block">
                <div class="block-header">
                  <span class="block-title">请求参数 (Inputs)</span>
                   <div class="flex-item ml-auto">
                     <el-button type="primary" plain size="small" icon="Refresh" @click="fetchParameters">
                        同步参数配置
                      </el-button>
                   </div>
                </div>
                
                <div class="param-table-container">
                  <div class="param-thead">
                    <div class="col-var">字段 Key</div>
                    <div class="col-type">类型</div>
                    <div class="col-ctrl">值 / 控件</div>
                    <div class="col-desc">描述</div>
                    <div class="col-action"></div>
                  </div>
                  <div class="param-tbody" :class="{ 'has-content': runState.dynamicParams.length > 0 }">
                    <div v-for="(item, index) in runState.dynamicParams" :key="index" class="param-row">
                      <div class="col-var">
                        <el-input v-model="item.variable" :readonly="!item.isManual" size="small" />
                      </div>
                      <div class="col-type">
                        <el-select v-model="item.type" :disabled="!item.isManual" size="small" style="width: 100%">
                          <el-option value="text-input" label="文字" />
                          <el-option value="number" label="数字" />
                          <el-option value="file" label="文件" />
                          <el-option value="select" label="选择" />
                          <el-option value="paragraph" label="段落" />
                        </el-select>
                      </div>
                      <div class="col-ctrl">
                        <el-input-number v-if="item.type === 'number'" v-model="item.value" size="small" style="width: 100%" />
                        <div v-else-if="item.type === 'file'" class="dynamic-file-box">
                          <label :for="'f-'+index" class="custom-file-upload"> 选择文件 </label>
                          <input :id="'f-'+index" type="file" @change="(e) => handleDynamicFileChange(e, item)" />
                          <span class="file-status" v-if="item.fileInfo">{{ item.fileInfo.name }}</span>
                        </div>
                        <el-select v-else-if="item.type === 'select'" v-model="item.value" size="small" style="width: 100%">
                          <el-option v-for="opt in item.options" :key="opt" :label="opt" :value="opt" />
                        </el-select>
                        <el-input v-else v-model="item.value" :type="item.type === 'paragraph' ? 'textarea' : 'text'" :rows="1" autosize size="small" />
                      </div>
                      <div class="col-desc">
                        <el-input v-model="item.label" :readonly="!item.isManual" placeholder="描述" size="small" />
                      </div>
                      <div class="col-action">
                        <el-button icon="Delete" link type="danger" @click="runState.dynamicParams.splice(index, 1)" />
                      </div>
                    </div>
                     <div v-if="runState.dynamicParams.length === 0" class="empty-params">
                      暂无参数项，请点击上方“同步参数配置”或手动添加
                    </div>
                  </div>
                  <div class="param-tfoot">
                    <el-button type="primary" link icon="Plus" size="small" @click="addManualParam">添加手动参数</el-button>
                  </div>
                </div>
              </div>

              <!-- result section -->
              <div class="result-section compact-block result-block">
                <div class="block-header">
                  <span class="block-title">返回结果</span>
                  <el-radio-group v-model="resultTab" size="small">
                    <el-radio-button value="raw">Raw</el-radio-button>
                    <el-radio-button value="md">Markdown</el-radio-button>
                    <el-radio-button value="json">JSON</el-radio-button>
                  </el-radio-group>
                </div>
                <div class="result-content-wrapper">
                    <div v-if="resultTab === 'md'" class="scroll-content result-container markdown-body" :class="{ 'has-content': runResult }" v-html="renderMarkdown(runResult)"></div>
                    <pre v-else-if="resultTab === 'json'" class="scroll-content result-container json-box" :class="{ 'has-content': runResult }">{{ renderJson(runResult) }}</pre>
                    <pre v-else class="scroll-content result-container raw-box" :class="{ 'has-content': runResult }">{{ runResult }}</pre>
                </div>
              </div>

            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import JSON5 from 'json5'

// --- State ---
const currentConfig = ref({})
const loading = ref(false)
const resultTab = ref('raw')
const runResult = ref('') // Accumulates text/markdown result

const runState = reactive({
  dynamicParams: [], // { variable, type, value, required, options, fileInfo }
})

onMounted(() => {
  initNewConfig()
})

const initNewConfig = () => {
  currentConfig.value = {
    id: Date.now().toString(),
    name: 'NewDifyWorkflow',
    service_type: 'dify',
    method: 'POST',
    url: 'https://api.dify.ai/v1/workflows/run',
    headers: { 'Authorization': '', 'Content-Type': 'application/json' },
    timeout: 60,
    stream: false
  }
  runState.dynamicParams = []
  runResult.value = ''
}

const selectConfig = async (item) => {
  // 深拷贝
  currentConfig.value = JSON.parse(JSON.stringify(item))
  runResult.value = ''
  // 尝试自动同步参数
  await fetchParameters()
}

const updateHeaderKey = (oldKey, newKey) => {
  const val = currentConfig.value.headers[oldKey]
  delete currentConfig.value.headers[oldKey]
  currentConfig.value.headers[newKey] = val
}
const addHeader = () => {
  currentConfig.value.headers['New-Key'] = ''
}

// --- Run Methods ---
const fetchParameters = async () => {
  if (!currentConfig.value.url) {
     ElMessage.warning('请先填写 API URL')
     return
  }

  try {
    // 调用后端代理接口
    const res = await axios.post(`/api/dify/parameters`, currentConfig.value)

    const form = res.data.user_input_form || []
    const newParams = form.map(item => {
      const type = Object.keys(item)[0]
      const details = item[type]
      let initialValue = details.default;
      if (initialValue === undefined || initialValue === null) {
          if (type === 'number') initialValue = undefined; 
          else initialValue = '';
      }
      
      return {
        variable: details.variable,
        label: details.label,
        type: type, 
        required: details.required,
        options: details.options || [],
        value: initialValue,
        fileInfo: null,
        isManual: false
      }
    })

    // 保留已输入的值
    const oldParams = [...runState.dynamicParams]
    runState.dynamicParams = newParams.map(p => {
      const matched = oldParams.find(old => old.variable === p.variable)
      if (matched) p.value = matched.value
      return p
    })
    
    ElMessage.success('参数已同步')
  } catch (e) {
    ElMessage.error('同步参数失败: ' + (e.response?.data?.detail || e.message))
  }
}

const handleDynamicFileChange = (e, item) => {
  if (e.target.files && e.target.files[0]) {
    item.fileInfo = e.target.files[0]
  }
}

const addManualParam = () => {
  runState.dynamicParams.push({
    variable: 'new_var',
    label: '自定义参数',
    type: 'text-input',
    value: '',
    required: false,
    isManual: true
  })
}

const executeRun = async () => {
  if (!currentConfig.value.url) {
     ElMessage.warning('请先填写 API URL')
     return
  }
  
  loading.value = true
  runResult.value = ''
  
  const finalParams = {}
  const filesToUpload = []
  
  runState.dynamicParams.forEach(p => {
    if (p.type === 'file' && p.fileInfo) {
      filesToUpload.push({
        variable: p.variable,
        file: p.fileInfo
      })
    } else {
      finalParams[p.variable] = p.value
    }
  })

  const fd = new FormData()
  fd.append('config_json', JSON.stringify(currentConfig.value))
  fd.append('params_json', JSON.stringify(finalParams))
  
  if (filesToUpload.length > 0) {
    filesToUpload.forEach(f => {
      const blob = f.file.slice(0, f.file.size, f.file.type)
      const renamedFile = new File([blob], `${f.variable}#${f.file.name}`, { type: f.file.type })
      fd.append('files', renamedFile) 
    })
  }

  try {
    const response = await fetch('/api/dify/run', {
      method: 'POST',
      body: fd
    })

    if (!response.ok) throw new Error(response.statusText)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk
      
      const lines = buffer.split('\n')
      // Store incomplete line in buffer
      buffer = lines.pop()
      
      for (const line of lines) {
        if (!line.trim()) continue
        
        // Parse SSE data
        let jsonStr = line
        if (line.startsWith('data: ')) {
          jsonStr = line.substring(6)
        }
        
        try {
          const data = JSON.parse(jsonStr)
          
          if (data.event === 'sys_log' || data.event === 'ping') {
             continue
          }
          if (data.error) {
            runResult.value += `\n[Error]: ${data.error}`
            continue
          }
          
          // Handle various Dify events
          if (data.event === 'message' || data.event === 'text_chunk') {
             // Chat / Agent output
             const text = data.answer || data.text || ''
             runResult.value += text
          } else if (data.event === 'workflow_finished') {
             // Workflow output
             if (data.data && data.data.outputs) {
                const outputs = data.data.outputs
                if (typeof outputs === 'string') {
                    runResult.value += outputs
                } else {
                    runResult.value = JSON.stringify(outputs, null, 2)
                }
             }
          } else if (!data.event) {
             // 假如没有 event 字段，说明是直接返回的结果对象 (Blocking Mode)
             if (typeof data === 'string') {
                runResult.value += data
             } else {
                runResult.value = JSON.stringify(data, null, 2)
             }
          }

        } catch (e) {
           // Not a JSON line, assume raw text
           runResult.value += line + '\n'
        }
      }
    }
    
    if (buffer.trim()) {
       // Try parse last chunk
       let jsonStr = buffer
       if (buffer.startsWith('data: ')) jsonStr = buffer.substring(6)
       try {
          const data = JSON.parse(jsonStr)
          if (data.event === 'workflow_finished' && data.data?.outputs) {
              const outputs = data.data.outputs
              if (typeof outputs === 'string') runResult.value += outputs
              else runResult.value = JSON.stringify(outputs, null, 2)
          } else if (!data.event) {
              // Handle non-event JSON at end (Blocking mode fallback)
              if (typeof data === 'string') runResult.value += data
              else runResult.value = JSON.stringify(data, null, 2)
          }
       } catch(e) {
          runResult.value += buffer
       }
    }

  } catch (e) {
    runResult.value = `请求失败: ${e.message}`
  } finally {
    loading.value = false
  }
}

const renderMarkdown = (text) => {
  return marked(text || '', { headerIds: false, mangle: false })
}

const renderJson = (text) => {
  if (!text) return ''
  try {
    const trimmed = text.trim()
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
       const obj = JSON5.parse(trimmed)
       return JSON5.stringify(obj, null, 2) 
    }
    return text
  } catch (e) {
    return text
  }
}
</script>

<style>
/* Global resets handled by main CSS or App.vue, ensure clean host here */
.dify-container { height: 100vh; display: flex; flex-direction: column; background: #f5f7fa; }
.page-header { background: #fff; border-bottom: 1px solid #dcdfe6; height: 50px !important; display: flex; align-items: center; padding: 0 20px; }
.left { display: flex; align-items: center; gap: 12px; }
.title { font-weight: 600; font-size: 16px; margin: 0; }

.dify-main { padding: 16px; overflow: hidden; flex: 1; display: flex; flex-direction: column; }
.main-card { display: flex; flex-direction: column; border-radius: 8px; }
:deep(.main-card .el-card__body) { padding: 0; flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 8px; }
.header-actions { display: flex; align-items: center; gap: 8px; }

.scroll-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }

/* List Styles (Removed, keeping minimal if needed or clean up later) */
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: bold; font-size: 14px; }
.list-scroll { flex: 1; height: 100%; border-right: 1px solid #ebeef5; padding-right: 10px; }
.list-item { padding: 10px 12px; margin-bottom: 4px; cursor: pointer; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; border: 1px solid transparent; transition: all 0.2s; }
.list-item:hover { background: #e6f7ff; }
.list-item.active { background: #1677ff; color: #fff; }
.list-item.active .el-button { color: #fff; }


/* Config Block Styles */
.config-block { padding: 15px; background: #fff; border-left: 4px solid #409eff; }
.config-row { display: flex; align-items: center; width: 100%; }
.mt-2 { margin-top: 10px; }
.ml-4 { margin-left: 20px; }
.label-text { width: 80px; font-weight: 500; font-size: 13px; color: #606266; flex-shrink: 0; }
.flex-item { display: flex; align-items: center; }

.headers-row { align-items: flex-start; }
.headers-container { flex: 1; display: flex; flex-direction: column; background: #f9f9f9; padding: 10px; border-radius: 4px; }

/* Run Layout Blocks */
.compact-block { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.params-block { border-top: 3px solid #67c23a; flex: 0 0 auto; max-height: 500px; display: flex; flex-direction: column; }
.params-block .param-table-container { display: flex; flex-direction: column; height: 100%; }
.result-block { border-top: 3px solid #409eff; flex: 1; min-height: 200px; display: flex; flex-direction: column; }

.block-header { padding: 10px 15px; border-bottom: 1px solid #ebeef5; display: flex; justify-content: space-between; align-items: center; background: #fafafa; }
.block-title { font-weight: bold; font-size: 14px; color: #303133; }

/* Param Table */
.param-thead { display: flex; background: #f5f7fa; padding: 8px 10px; font-weight: 600; color: #606266; font-size: 12px; border-bottom: 1px solid #ebeef5; }
.param-tbody { overflow-y: auto; padding: 0; max-height: 300px; }
.param-row { display: flex; align-items: center; padding: 8px 10px; border-bottom: 1px solid #ebeef5; gap: 10px; }
.param-tfoot { padding: 10px; background: #f9f9f9; border-top: 1px solid #ebeef5; display: flex; align-items: center; }

.col-var { width: 140px; flex-shrink: 0; }
.col-type { width: 100px; flex-shrink: 0; }
.col-ctrl { flex: 1; min-width: 100px; }
.col-desc { width: 150px; flex-shrink: 0; }
.col-action { width: 30px; }

.empty-params { padding: 30px; text-align: center; color: #909399; font-size: 13px; }

/* Result Box */
.result-content-wrapper { flex: 1; overflow: hidden; position: relative; display: flex; flex-direction: column; }
.scroll-content { flex: 1; overflow-y: auto; padding: 15px; margin: 0; font-size: 14px; line-height: 1.6; }
.raw-box { background: #282c34; color: #abb2bf; font-family: Consolas, monospace; white-space: pre-wrap; word-break: break-all; }
.json-box { background: #fdf6e3; color: #333; font-family: Consolas, monospace; white-space: pre-wrap; word-break: break-all; }
.markdown-body { background: #fff; }

.empty-selection { height: 100%; display: flex; align-items: center; justify-content: center; }
</style>