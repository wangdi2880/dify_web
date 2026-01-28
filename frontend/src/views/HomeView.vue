<template>
  <div class="home-container">
    <h1>Web Services Hub</h1>
    <div class="actions">
      <el-button type="primary" size="large" @click="$router.push('/dify')">
        <el-icon class="el-icon--left"><Connection /></el-icon>
        Dify 工作流调用
      </el-button>
      <el-button type="success" size="large" @click="$router.push('/test')">
        测试连通
      </el-button>
      <el-button size="large" disabled>其他服务 (待开发)</el-button>
    </div>
  </div>
</template>

<style scoped>
.home-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; overflow: hidden; background-color: #f5f7fa; }
.actions { display: flex; gap: 20px; margin-top: 30px; }
</style>