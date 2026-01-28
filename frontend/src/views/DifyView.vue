<template>
  <div class="dify-container">
    <el-header class="page-header">
      <div class="left">
        <el-button icon="Back" circle @click="$router.push('/')" />
        <h3 class="title">Dify Workflow Manager</h3>
      </div>
    </el-header>

    <el-main>
      <el-tabs v-model="activeTab" type="border-card">
        
        <el-tab-pane label="API 配置" name="config">
          <el-row :gutter="20" class="tab-content-row">
            <el-col :span="6" class="h-100">
              <div class="list-header">
                <span>配置列表</span>
                <el-button type="primary" link icon="Plus" @click="initNewConfig">新增</el-button>
              </div>
              <el-scrollbar class="list-scroll" :class="{ 'has-content': configList.length > 0 }">
                <div v-for="item in configList" :key="item.id" 
                     class="list-item" :class="{active: currentConfig.id === item.id}"
                     @click="selectConfig(item)">
                  <span class="name">{{ item.name }}</span>
                  <el-button type="danger" link icon="Delete" @click.stop="deleteConfig(item.id)" />
                </div>
              </el-scrollbar>
            </el-col>
            
            <el-col :span="18" class="h-100">
              <el-card shadow="never" class="h-100" v-if="currentConfig.id">
                <template #header>
                  <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <span style="font-weight: bold;">{{ currentConfig.name || '未命名配置' }}</span>
                    <el-button type="primary" icon="" @click="saveConfig">保存配置</el-button>
                  </div>
                </template>
                <el-form label-width="120px" :model="currentConfig">
                  <el-form-item label="配置名称">
                    <el-input v-model="currentConfig.name" placeholder="例如: 文本摘要工作流" />
                  </el-form-item>
                  <el-form-item label="服务类型">
                    <el-select v-model="currentConfig.service_type" disabled><el-option value="dify" label="Dify" /></el-select>
                  </el-form-item>
                  <el-form-item label="API URL">
                    <el-input v-model="currentConfig.url" placeholder="http://.../v1/workflows/run" />
                  </el-form-item>
                  <el-form-item label="API KEY">
                    <el-input v-model="currentConfig.headers['Authorization']" placeholder="app-xxxx..." />
                  </el-form-item>
                  
                  <el-divider content-position="left">其他 Headers</el-divider>
                  <div v-for="(val, key) in currentConfig.headers" :key="key" class="kv-row">
                    <template v-if="key !== 'Authorization' && key !== 'Content-Type'">
                       <el-input :model-value="key" @input="v => updateHeaderKey(key, v)" placeholder="Key" style="width: 30%;" />
                       <span class="mx-2">:</span>
                       <el-input v-model="currentConfig.headers[key]" placeholder="Value" style="width: 50%;" />
                       <el-button icon="Delete" link type="danger" @click="delete currentConfig.headers[key]" />
                    </template>
                  </div>
                  <el-button size="small" icon="Plus" @click="addHeader">添加 Header</el-button>

                  <el-divider />
                  <el-row>
                    <el-col :span="12">
                      <el-form-item label="超时时间(s)">
                        <el-input-number v-model="currentConfig.timeout" :min="10" />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="流式响应">
                        <el-switch v-model="currentConfig.stream" />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </el-form>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="API 调用" name="run">
          <el-row :gutter="20" class="tab-content-row">
            <el-col :span="6" class="h-100">
               <el-card shadow="never" class="h-100">
                 <div slot="header" class="mb-10"><b>选择服务调用</b></div>
                 <el-scrollbar class="list-scroll" :class="{ 'has-content': historyOrConfigList.length > 0 }">
                   <div v-for="h in historyOrConfigList" :key="h.id || h.config_id" 
                        class="list-item" @click="loadRunConfig(h)">
                     <div class="name">{{ h.name || h.config_name }}</div>
                     <small v-if="h.timestamp" style="color:#999">上次调用: {{ h.timestamp }}</small>
                   </div>
                 </el-scrollbar>
               </el-card>
            </el-col>

            <el-col :span="18" class="h-100 call-area">
              <!-- Block 1: URL & Config Selector -->
              <div class="compact-block config-block">
                <div class="block-title">1. 配置与地址</div>
                <div class="run-header">
                  <el-select v-model="runState.configId" placeholder="选择激活配置" size="default" style="width: 300px" @change="onConfigChange">
                    <el-option v-for="c in configList" :key="c.id" :label="c.name" :value="c.id" />
                  </el-select>
                  <el-button type="success" :loading="loading" icon="Promotion" @click="executeRun">发送请求 (Run)</el-button>
                  <el-button type="primary" plain icon="Refresh" @click="fetchParameters" :disabled="!runState.configId">同步参数配置</el-button>
                </div>
              </div>

              <!-- Block 2: Request Parameters -->
              <div class="compact-block params-block">
                <div class="block-title">2. 请求参数 (Inputs)</div>
                <div class="param-table-container">
                  <div class="param-thead">
                    <div class="col-var">字段 Key (Variable)</div>
                    <div class="col-type">类型</div>
                    <div class="col-ctrl">参数值/控件</div>
                    <div class="col-desc">描述 (Label)</div>
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
                      暂无参数项，请点击下方添加
                    </div>
                  </div>
                  <div class="param-tfoot">
                    <el-button type="primary" link icon="Plus" size="small" @click="addManualParam">添加手动参数</el-button>
                  </div>
                </div>
              </div>

              <!-- Block 3: Result -->
              <div class="compact-block result-block">
                <div class="block-title">3. 返回结果</div>
                <div class="result-tabs-wrapper">
                  <el-tabs v-model="resultTab" class="full-height-tabs">
                    <el-tab-pane label="Markdown 渲染" name="md">
                      <div class="scroll-content result-container markdown-body" :class="{ 'has-content': runResult }" v-html="renderMarkdown(runResult)"></div>
                    </el-tab-pane>
                    <el-tab-pane label="Raw 原始数据" name="raw">
                      <pre class="scroll-content result-container raw-box" :class="{ 'has-content': runResult }">{{ runResult }}</pre>
                    </el-tab-pane>
                  </el-tabs>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

      </el-tabs>
    </el-main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'

// --- State ---
const activeTab = ref('run')
const configList = ref([])
const historyList = ref([])
const currentConfig = ref({})
const loading = ref(false)
const resultTab = ref('md')
const runResult = ref('')

const runState = reactive({
  configId: '',
  dynamicParams: [], // { variable, type, value, required, options, fileInfo }
})

// --- Computed ---
// 混合展示：优先展示历史记录，没有历史记录展示纯配置
const historyOrConfigList = computed(() => {
  return historyList.value.length ? historyList.value : configList.value
})

// --- Lifecycle ---
onMounted(async () => {
  await fetchConfigs()
  await fetchHistory()
  initNewConfig()
})

// --- API Config Methods ---
const fetchConfigs = async () => {
  const res = await axios.get('/api/dify/configs')
  configList.value = res.data
}

const fetchHistory = async () => {
  const res = await axios.get('/api/dify/history')
  historyList.value = res.data
}

const initNewConfig = () => {
  currentConfig.value = {
    id: Date.now().toString(),
    name: 'New Dify Config',
    service_type: 'dify',
    method: 'POST',
    url: 'https://api.dify.ai/v1/workflows/run',
    headers: { 'Authorization': '', 'Content-Type': 'application/json' },
    timeout: 60,
    stream: false
  }
}

const selectConfig = (item) => {
  currentConfig.value = JSON.parse(JSON.stringify(item))
}

const saveConfig = async () => {
  await axios.post('/api/dify/configs', currentConfig.value)
  ElMessage.success('保存成功')
  fetchConfigs()
}

const deleteConfig = async (id) => {
  await axios.delete(`/api/dify/configs/${id}`)
  fetchConfigs()
  initNewConfig()
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
const onConfigChange = async (val) => {
  await fetchParameters()
}

const fetchParameters = async () => {
  if (!runState.configId) return

  try {
    // 调用后端代理接口，由后端负责拼接 Bearer
    const res = await axios.get(`/api/dify/parameters?config_id=${runState.configId}`)

    const form = res.data.user_input_form || []
    const newParams = form.map(item => {
      const type = Object.keys(item)[0]
      const details = item[type]
      return {
        variable: details.variable,
        label: details.label,
        type: type, // text-input, number, select, file, paragraph
        required: details.required,
        options: details.options || [],
        value: details.default || '',
        fileInfo: null,
        isManual: false
      }
    })

    // 如果当前有历史数据或正在编辑的数据，尝试合并
    const oldParams = [...runState.dynamicParams]
    runState.dynamicParams = newParams.map(p => {
      const matched = oldParams.find(old => old.variable === p.variable)
      if (matched) p.value = matched.value
      return p
    })
  } catch (e) {
    ElMessage.error('获取应用参数失败: ' + e.message)
  }
}

const loadRunConfig = async (item) => {
  if (item.config_id) {
    runState.configId = item.config_id
    await fetchParameters()
    // 填充历史值
    if (item.params_json) {
       runState.dynamicParams.forEach(p => {
         if (item.params_json[p.variable] !== undefined) {
           p.value = item.params_json[p.variable]
         }
       })
    }
  } else {
    runState.configId = item.id
    await fetchParameters()
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
  if (!runState.configId) return ElMessage.error('请选择配置')
  
  loading.value = true
  runResult.value = '' // 清空旧结果
  
  // 1. 组装参数
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

  // 2. 构造 FormData
  const fd = new FormData()
  fd.append('config_id', runState.configId)
  fd.append('params_json', JSON.stringify(finalParams))
  
  if (filesToUpload.length > 0) {
    filesToUpload.forEach(f => {
      // 为了让后端知道哪个文件对应哪个变量，我们将变量名编码进文件名中
      // 格式：variableName#originalFileName
      const blob = f.file.slice(0, f.file.size, f.file.type)
      const renamedFile = new File([blob], `${f.variable}#${f.file.name}`, { type: f.file.type })
      fd.append('files', renamedFile) 
    })
  }

  // 3. 发送请求 (使用 fetch 处理流)
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
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      
      // 最后一项可能是不完整的，留给下一块
      buffer = lines.pop()
      
      for (const line of lines) {
        if (!line.trim()) continue
        
        try {
          const data = JSON.parse(line)
          if (data.event === 'sys_log') {
            console.log('Dify System Log:', data.message)
            // 你也可以在这里用 ElMessage 显示中间状态
            continue
          }
          if (data.error) {
            runResult.value += `\n[系统错误]: ${data.error}`
            continue
          }
        } catch (e) {
          // 不是 JSON 或者是 Dify 的文本块，直接追加
          runResult.value += line + '\n'
        }
      }
    }
    
    // 处理最后剩余的 buffer
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer)
        if (!data.error && data.event !== 'sys_log') {
           runResult.value += buffer
        }
      } catch (e) {
        runResult.value += buffer
      }
    }
    
    fetchHistory() // 刷新历史
  } catch (e) {
    runResult.value = `请求失败: ${e.message}`
  } finally {
    loading.value = false
  }
}

const renderMarkdown = (text) => {
  return marked(text || '')
}
</script>

<style>
/* 全局样式：确保页面无滚动条 */
html, body {
  height: 100%;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

#app {
  height: 100%;
  overflow: hidden;
}
</style>

<style scoped>
.dify-container { height: 100vh; display: flex; flex-direction: column; overflow: hidden; background: #f5f7fa; }
.page-header { background: #fff; border-bottom: 1px solid #e6e6e6; height: 50px !important; display: flex; align-items: center; padding: 0 20px; flex-shrink: 0; }
.left { display: flex; align-items: center; gap: 12px; }
.title { font-weight: 600; font-size: 16px; color: #303133; margin: 0; }

.el-main { flex: 1; padding: 12px; overflow: hidden; display: flex; flex-direction: column; min-height: 0; }
.el-tabs--border-card { border: none; box-shadow: none; display: flex; flex-direction: column; flex: 1; min-height: 0; overflow: hidden; }
:deep(.el-tabs__content) { flex: 1; overflow: hidden; padding: 12px; min-height: 0; }
:deep(.el-tab-pane) { height: 100%; display: flex; flex-direction: column; min-height: 0; }

.tab-content-row { height: 100%; display: flex; flex-direction: row; min-height: 0; overflow: hidden; }
:deep(.tab-content-row .el-row) { height: 100%; min-height: 0; overflow: hidden; }
:deep(.tab-content-row .el-col) { display: flex; flex-direction: column; min-height: 0; height: 100%; overflow: hidden; }

.h-100 { height: 100%; display: flex; flex-direction: column; min-height: 0; }
:deep(.h-100 .el-card) { display: flex; flex-direction: column; height: 100%; }
:deep(.h-100 .el-card__body) { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: bold; font-size: 14px; flex-shrink: 0; }
.list-scroll { flex: 1; min-height: 0; height: 100%; }
:deep(.list-scroll .el-scrollbar__wrap) { overflow-x: hidden !important; }
:deep(.list-scroll:not(.has-content) .el-scrollbar__bar.is-vertical) { display: none !important; }
:deep(.list-scroll:not(.has-content) .el-scrollbar__bar.is-horizontal) { display: none !important; }
.list-item { padding: 10px 12px; margin-bottom: 4px; cursor: pointer; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; border: 1px solid transparent; }
.list-item:hover { background: #f0f2f5; }
.list-item.active { background: #e6f7ff; color: #409eff; border-color: #bae7ff; }

.call-area { display: flex; flex-direction: column; gap: 10px; height: 100%; min-height: 0; overflow: hidden; }

.compact-block { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; padding: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.config-block { flex-shrink: 0; border-top: 2px solid #67c23a;}
.params-block { border-top: 2px solid #67c23a; flex: 0 0 1; max-height: 45%; display: flex; flex-direction: column; }
.result-block { border-top: 2px solid #67c23a; flex: 1; min-height: 0; display: flex; flex-direction: column; }

.block-title { font-size: 13px; font-weight: 700; color: #333; margin-bottom: 8px; padding-left: 2px; }
.run-header { display: flex; gap: 8px; align-items: center; }

/* Parameter Table Re-styled */
.param-table-container { border: 1px solid #f0f0f0; border-radius: 6px; overflow: hidden; display: flex; flex-direction: column; flex: 1; }
.param-thead { display: flex; background: #fafafa; padding: 8px 12px; font-weight: 600; color: #606266; font-size: 12px; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; }
.param-tbody { overflow-y: auto; flex: 1; min-height: 40px; }
.param-row { display: flex; align-items: center; padding: 6px 10px; border-bottom: 1px solid #f5f5f5; }
.param-tfoot { border-top: 1px solid #f0f0f0; padding: 4px 10px; }
.empty-params { padding: 20px; text-align: center; color: #999; font-size: 12px; }

.col-var { width: 140px; flex-shrink: 0; }
.col-type { width: 90px; flex-shrink: 0; margin: 0 8px; }
.col-ctrl { flex: 1; min-width: 0; }
.col-desc { width: 140px; flex-shrink: 0; margin-left: 8px; }
.col-action { width: 30px; flex-shrink: 0; text-align: right; }

.result-tabs-wrapper { flex: 1; display: flex; flex-direction: column; min-height: 0; padding-top: 5px; }
.full-height-tabs { height: 100%; display: flex; flex-direction: column; }
:deep(.full-height-tabs .el-tabs__content) { flex: 1; padding: 0 !important; min-height: 0; }
:deep(.full-height-tabs .el-tab-pane) { height: 100%; display: flex; flex-direction: column; min-height: 0; }

.scroll-content { height: 100%; overflow-y: auto; padding: 12px; background: #fafafa; border: 1px solid #f0f0f0; border-radius: 4px; box-sizing: border-box; min-height: 0; }
.raw-box { background: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace; font-size: 12px; margin: 0; white-space: pre-wrap; word-break: break-all; }
.markdown-body { background: #fff; font-size: 14px; }
.markdown-body:empty::after { content: "暂无运行结果"; color: #999; display: flex; align-items: center; justify-content: center; height: 100%; font-size: 13px; }
.raw-box { background: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 12px; margin: 0; white-space: pre-wrap; word-break: break-all; }
.markdown-body { background: #fff; font-size: 14px; }

/* File upload */
.dynamic-file-box { display: flex; align-items: center; gap: 8px; }
.custom-file-upload { padding: 4px 10px; cursor: pointer; background: #f5f7fa; border: 1px solid #dcdfe6; border-radius: 4px; font-size: 11px; }
input[type="file"] { display: none; }
.file-status { color: #409eff; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100px; }
</style>