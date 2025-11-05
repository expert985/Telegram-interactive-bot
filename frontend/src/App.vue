<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useWebSocketStore } from '@/stores/websocket'

const wsStore = useWebSocketStore()

onMounted(() => {
  // 初始化 WebSocket 连接
  wsStore.connect()
})
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>
