<template>
  <div class="not-found-page">
    <h1>404</h1>
    <p>页面未找到</p>
    <el-button type="primary" @click="goHome">返回首页</el-button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<style scoped lang="scss">
.not-found-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;

  h1 {
    font-size: 120px;
    color: var(--safeline-primary);
    margin: 0;
  }

  p {
    font-size: 24px;
    color: var(--safeline-text-secondary);
    margin: 20px 0 40px;
  }
}
</style>
