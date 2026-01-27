<script setup lang="ts">
import { ref } from 'vue'

const message = ref('等待调用...')
const password = ref('')

const callBackend = async () => {
  try {
    const res = await fetch('/api/hello')
    const data = await res.json()
    message.value = data.message
  } catch (error) {
    message.value = '调用失败，请检查后端是否启动'
    console.error(error)
  }
}

const generatePassword = async () => {
  try {
    const res = await fetch('/api/skill/generate_password?length=12&use_special=true')
    const data = await res.json()
    password.value = data.result
  } catch (error) {
    password.value = '生成失败'
  }
}
</script>

<template>
  <div class="container">
    <h1>Dify Web Starter</h1>
    
    <div class="card">
      <h2>测试 1: 基础连通性</h2>
      <p>后端响应: {{ message }}</p>
      <button @click="callBackend">Ping 后端</button>
    </div>

    <div class="card">
      <h2>测试 2: Skill 调用 (密码生成)</h2>
      <p class="password">{{ password }}</p>
      <button @click="generatePassword">生成强密码</button>
    </div>
  </div>
</template>

<style scoped>
.container { font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 2rem; text-align: center; }
.card { border: 1px solid #ccc; padding: 1rem; margin-top: 1rem; border-radius: 8px; }
button { cursor: pointer; padding: 8px 16px; background: #646cff; color: white; border: none; border-radius: 4px; }
button:hover { background: #535bf2; }
.password { font-family: monospace; font-size: 1.2em; font-weight: bold; color: #2c3e50; }
</style>
