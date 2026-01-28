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
          <el-row :gutter="20" style="height: calc(100vh - 180px);">
            <el-col :span="6" class="h-100">
              <div class="list-header">
                <span>配置列表</span>
                <el-button type="primary" link icon="Plus" @click="initNewConfig">新增</el-button>
              </div>
              <el-scrollbar class="list-scroll">
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
                  <div class="card-header">
                    <span>{{ currentConfig.name || '未命名配置' }}</span>
                    <el-button type="primary" @click="saveConfig">保存配置</el-button>
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
          <el-row :gutter="20" style="height: calc(100vh - 180px);">
            <el-col :span="6" class="h-100">
               <el-card shadow="never" class="h-100">
                 <div slot="header" class="mb-10"><b>选择服务调用</b></div>
                 <el-scrollbar>
                   <div v-for="h in historyOrConfigList" :key="h.id || h.config_id" 
                        class="list-item" @click="loadRunConfig(h)">
                     <div class="name">{{ h.name || h.config_name }}</div>
                     <small v-if="h.timestamp" style="color:#999">上次调用: {{ h.timestamp }}</small>
                   </div>
                 </el-scrollbar>
               </el-card>
            </el-col>

            <el-col :span="18" class="h-100" style="display:flex; flex-direction:column;">
              <el-card shadow="hover" class="mb-10" body-style="padding: 15px;">
                <div class="run-header mb-10">
                   <el-select v-model="runState.configId" placeholder="选择配置" style="width: 300px">
                     <el-option v-for="c in configList" :key="c.id" :label="c.name" :value="c.id" />
                   </el-select>
                   <el-button type="success" :loading="loading" @click="executeRun">发送请求 (Run)</el-button>
                </div>

                <el-form label-position="top" size="small">
                  <el-form-item label="参数录入方式">
                    <el-radio-group v-model="runState.paramType">
                      <el-radio value="none">无参数</el-radio>
                      <el-radio value="form-data">Form-Data (Key-Value)</el-radio>
                      <el-radio value="json">JSON 文本</el-radio>
                    </el-radio-group>
                  </el-form-item>

                  <div v-if="runState.paramType === 'form-data'" class="param-area">
                    <div v-for="(item, index) in runState.kvParams" :key="index" class="kv-row mb-5">
                      <el-input v-model="item.key" placeholder="Key (e.g. query)" style="width: 30%" />
                      <span class="mx-2">=</span>
                      <el-input v-model="item.value" placeholder="Value" style="width: 50%" />
                      <el-button icon="Delete" link type="danger" @click="runState.kvParams.splice(index, 1)" />
                    </div>
                    <el-button type="primary" link icon="Plus" @click="runState.kvParams.push({key:'', value:''})">添加参数</el-button>
                  </div>

                  <div v-if="runState.paramType === 'json'">
                    <el-input type="textarea" :rows="4" v-model="runState.jsonStr" placeholder='{"inputs": {"query": "hello"}, "user": "abc"}' />
                  </div>

                  <div class="mt-10">
                    <label style="font-size:12px; color:#606266; margin-right:10px;">文件上传 (可选):</label>
                    <input type="file" multiple @change="handleFileChange" />
                  </div>
                </el-form>
              </el-card>

              <div class="result-area" style="flex:1; overflow:hidden; display:flex; flex-direction:column;">
                <el-tabs v-model="resultTab" type="border-card" style="height:100%">
                  <el-tab-pane label="Markdown 预览" name="md">
                    <div class="scroll-content" v-html="renderMarkdown(runResult)"></div>
                  </el-tab-pane>
                  <el-tab-pane label="原始文本" name="raw">
                    <pre class="scroll-content">{{ runResult }}</pre>
                  </el-tab-pane>
                </el-tabs>
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
const activeTab = ref('config')
const configList = ref([])
const historyList = ref([])
const currentConfig = ref({})
const loading = ref(false)
const resultTab = ref('md')
const runResult = ref('')

const runState = reactive({
  configId: '',
  paramType: 'none',
  kvParams: [{ key: 'query', value: '' }, { key: 'user', value: 'web-user' }],
  jsonStr: '{}',
  files: []
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
const loadRunConfig = (item) => {
  // 如果是历史记录
  if (item.config_id) {
    runState.configId = item.config_id
    // 恢复参数
    if (item.params_json) {
       runState.jsonStr = JSON.stringify(item.params_json, null, 2)
       runState.paramType = 'json'
       // 尝试转换回 KV
       const keys = Object.keys(item.params_json)
       runState.kvParams = keys.map(k => ({ key: k, value: item.params_json[k] }))
    }
  } else {
    // 纯配置
    runState.configId = item.id
  }
}

const handleFileChange = (e) => {
  runState.files = e.target.files
}

const executeRun = async () => {
  if (!runState.configId) return ElMessage.error('请选择配置')
  
  loading.value = true
  runResult.value = '' // 清空旧结果
  
  // 1. 组装参数为 JSON 对象
  let finalParams = {}
  if (runState.paramType === 'form-data') {
    runState.kvParams.forEach(p => { if(p.key) finalParams[p.key] = p.value })
  } else if (runState.paramType === 'json') {
    try {
      finalParams = JSON.parse(runState.jsonStr)
    } catch (e) {
      loading.value = false
      return ElMessage.error('JSON 格式错误')
    }
  }

  // 2. 构造 FormData
  const fd = new FormData()
  fd.append('config_id', runState.configId)
  fd.append('params_json', JSON.stringify(finalParams)) // 后端统一接收 JSON 字符串
  if (runState.files) {
    for (let f of runState.files) fd.append('files', f)
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

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      
      // 尝试解析是否为后端报错 JSON
      try {
         const jsonErr = JSON.parse(text)
         if (jsonErr.error) {
           runResult.value += `\n[System Error]: ${jsonErr.error}`
           continue
         }
      } catch (e) {}

      runResult.value += text
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

<style scoped>
.page-header { background: #fff; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }
.left { display: flex; align-items: center; gap: 15px; }
.list-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid #eee; margin-bottom: 10px; }
.list-item { padding: 10px; cursor: pointer; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
.list-item:hover { background: #f5f7fa; }
.list-item.active { background: #ecf5ff; color: #409eff; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.kv-row { display: flex; align-items: center; }
.mx-2 { margin: 0 10px; }
.mb-10 { margin-bottom: 10px; }
.mb-5 { margin-bottom: 5px; }
.h-100 { height: 100%; }
.scroll-content { height: 100%; overflow-y: auto; padding: 10px; background: #fafafa; border-radius: 4px; }
.run-header { display: flex; gap: 10px; }
</style>