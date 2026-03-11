<template>
  <a-sub-menu :key="route.path">
    <template #title>
      <component :is="route.meta?.icon" />
      <span>{{ route.meta?.title }}</span>
    </template>
<template v-for="child in route.children" :key="child.path">     
  <a-menu-item> <!-- 删掉这里的:key="child.path" -->
    <span>{{ child.meta?.title }}</span>
  </a-menu-item>
</template>
  </a-sub-menu>
</template>

<script setup lang="ts">
import { RouteRecordRaw } from 'vue-router'

defineProps({
  route: {
    type: Object as () => RouteRecordRaw,
    required: true
  }
})
</script>