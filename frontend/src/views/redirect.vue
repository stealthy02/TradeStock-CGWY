<template></template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { onMounted } from 'vue'

// 重定向核心逻辑：解析参数跳回原页面
const router = useRouter()
const route = useRoute()

onMounted(() => {
  const { path } = route.params as { path: string }
  router.replace({ 
    path: '/' + path, 
    query: route.query 
  })
})
</script>

<style scoped></style>