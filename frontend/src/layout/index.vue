<template>
  <a-layout class="pro-layout" style="height: 100vh">
    <!-- 侧边导航：可折叠 -->
<a-layout-sider
  v-model:collapsed="collapsed"
  trigger="" 
  collapsible
  :width="200"
  breakpoint="lg"
  :collapsed-width="80"
  class="pro-sider"
>
  <!-- 自定义触发器插槽：#trigger，支持所有Vue语法，直接用导入的图标组件 -->
  <template #trigger>
    <div style="width:100%; height:100%; display:flex; align-items:center; justify-content:center; color:#fff; font-size:16px;">
      <!-- 直接用你已经导入的折叠/展开图标，无需再写类名，和顶栏完全一致 -->
      <component :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined" />
    </div>
  </template>
      <!-- Logo区域 -->
<div class="logo-container flex items-center justify-center bg-white">
  <ShopOutlined class="logo-icon text-primary text-xl" />
  <span v-show="!collapsed" class="logo-title ml-2 text-lg font-bold text-primary">
    {{ VITE_APP_TITLE }}
  </span>
</div>
      <!-- 侧边菜单：遍历固定菜单数组menuList -->
<a-menu
  theme="dark"
  mode="inline"
  :selected-keys="selectedKeys"
  :open-keys="openKeys"
  @select="handleSelect as any"
  @open-change="handleOpenChange"
  class="pro-menu"
  :style="{ height: 'calc(100vh - 70px)', overflow: 'auto', position: 'relative', zIndex: 1 }"
>
        <template v-for="menu in menuList" :key="menu.path">
          <!-- 无子女：一级菜单项 -->
          <a-menu-item 
            :key="menu.path" 
            v-if="!menu.children || menu.children.length === 0"
          >
            <component v-if="menu.icon" :is="menu.icon" />
            <span v-show="!collapsed" class="menu-title">{{ menu.title }}</span>
          </a-menu-item>
          <!-- 有子女：折叠子菜单 -->
<a-sub-menu 
  :key="'sub-' + menu.title"
  v-else
>
            <template #title>
              <component v-if="menu.icon" :is="menu.icon" />
              <span v-show="!collapsed">{{ menu.title }}</span>
            </template>
            <!-- 二级子菜单 -->
            <a-menu-item
              v-for="child in menu.children"
              :key="child.path"
            >
              <component v-if="child.icon" :is="child.icon" class="ml-1" />
              <span>{{ child.title }}</span>
            </a-menu-item>
          </a-sub-menu>
        </template>
      </a-menu>
    </a-layout-sider>

    <!-- 主内容区域：顶部栏 + 页面内容 -->
    <a-layout class="pro-main-layout">
      <!-- 顶部操作栏 -->
<!-- 顶部操作栏：修复所有元素在同一行，垂直完美对齐 -->
<!-- 顶部操作栏：最终版 - 高度适中+按钮全显+同一行对齐 -->
<a-layout-header class="pro-header">
  <div class="header-inner flex items-center justify-between w-full h-full">
    <!-- 左侧：折叠图标 -->
    <div class="header-left">
      <component
        :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined"
        class="collapse-icon cursor-pointer"
        @click="collapsed = !collapsed"
      />
    </div>
    <!-- 右侧：刷新+全屏按钮（清晰显示，不隐藏） -->
    <div class="header-right flex items-center gap-4">
      <a-button type="text" class="header-btn" @click="handleRefresh" tooltip="刷新页面">
        <ReloadOutlined />
      </a-button>
      <a-button type="text" class="header-btn" @click="handleFullScreen" tooltip="全屏/退出全屏">
        <FullscreenOutlined />
      </a-button>
    </div>
  </div>
</a-layout-header>


      <!-- 页面内容区：路由出口 -->
<a-layout-content class="pro-content p-6 bg-gray-50">
  <router-view :key="$route.fullPath" />
</a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
// 导入Antd图标
import {
  ShopOutlined, MenuFoldOutlined, MenuUnfoldOutlined,
  ReloadOutlined, FullscreenOutlined, DashboardOutlined,
  ProfileOutlined, ShoppingOutlined, StockOutlined,
  MoneyCollectOutlined
} from '@ant-design/icons-vue'
// 导入TS类型
import type { Key } from 'ant-design-vue/es/_util/type'
import type { Component } from 'vue'

// 定义菜单TS接口
interface MenuOption {
  path: string;
  title: string;
  icon?: Component;
  children?: MenuOption[];
}

// 环境变量：系统名称
const { VITE_APP_TITLE = '库存结算管理' } = import.meta.env
// 路由实例
const router = useRouter()
const route = useRoute()

// 固定菜单数组
const menuList: MenuOption[] = [
  {
    path: '/layout/home',
    title: '首页-数据总览',
    icon: DashboardOutlined,
  },
  {
    path: '/layout/basic',
    title: '基础信息管理',
    icon: ProfileOutlined,
    children: [
      { path: '/layout/basic/supplier', title: '供货商信息' },
      { path: '/layout/basic/purchaser', title: '客户信息' }
    ]
  },
  {
    path: '/layout/purchase',
    title: '采购管理',
    icon: ShoppingOutlined,
    children: [
      { path: '/layout/purchase/info', title: '采购信息录入/查询' },
      { path: '/layout/purchase/bill', title: '采购对账单管理' }
    ]
  },
  {
    path: '/layout/sale',
    title: '销售管理',
    icon: ShopOutlined,
    children: [
      { path: '/layout/sale/info', title: '销售信息录入/查询' },
      { path: '/layout/sale/bill', title: '销售对账单管理' }
    ]
  },
  {
    path: '/layout/inventory',
    title: '库存管理',
    icon: StockOutlined,
    children: [
      { path: '/layout/inventory/list', title: '当前库存查询' },
      { path: '/layout/inventory/loss', title: '库存报损录入/查询' },
      { path: '/layout/inventory/detail', title: '库存商品流动详情' }
    ]
  },
  {
    path: '/layout/cost',
    title: '成本费用管理',
    icon: MoneyCollectOutlined,
    children: [
      { path: '/layout/cost/fee', title: '运营杂费录入/查询' }
    ]
  }
]

// 侧边栏折叠状态
const collapsed = ref<boolean>(false)
// 菜单选中的key
const selectedKeys = ref<Key[]>([(route.path || '') as Key])
// 菜单展开的key
const openKeys = ref<Key[]>([])

// 菜单点击事件：跳转对应路由
const handleSelect = (info: { key: Key; keyPath: Key[] }) => {
  router.push(info.key as string)
}

// 子菜单展开/收起事件
const handleOpenChange = (keys: Key[]) => {
  openKeys.value = keys
}

// 刷新页面
const handleRefresh = () => {
  router.replace({
    path: '/redirect' + route.fullPath,
  })
}

// 全屏/退出全屏（兼容多浏览器）
const handleFullScreen = () => {
  const doc = document.documentElement
  const docObj = document as unknown as {
    webkitFullscreenElement?: Element;
    msFullscreenElement?: Element;
    webkitExitFullscreen?: () => void;
    msExitFullscreen?: () => void;
  }
  const docElObj = doc as unknown as {
    webkitRequestFullscreen?: () => Promise<void>;
    msRequestFullscreen?: () => Promise<void>;
  }

  if (!document.fullscreenElement && !docObj.webkitFullscreenElement && !docObj.msFullscreenElement) {
    doc.requestFullscreen?.().catch((err) => console.error('全屏失败:', err))
    docElObj.webkitRequestFullscreen?.().catch((err) => console.error('全屏失败:', err))
    docElObj.msRequestFullscreen?.().catch((err) => console.error('全屏失败:', err))
  } else {
    document.exitFullscreen?.()
    docObj.webkitExitFullscreen?.()
    docObj.msExitFullscreen?.()
  }
}

// 解析当前路由的父级路径：多级路由自动展开父菜单
const getParentPaths = (path: string): Key => {
  if (!path || path.split('/').length <= 2) return ''
  // 截取父级路由（如 /layout/basic/supplier → /layout/basic）
  return path.substring(0, path.lastIndexOf('/'))
}

// 核心修复：保留手动展开状态，仅追加当前路由父路径
watch(
  () => route.path,
  (newPath) => {
    selectedKeys.value = [newPath]
    const parentPath = getParentPaths(newPath)
    if (parentPath && !openKeys.value.includes(parentPath)) {
      openKeys.value = [...openKeys.value, parentPath]
    }
  },
  { immediate: true }
)
</script>

<style lang="less" scoped>
// 全局布局根容器：消除白边+撑满视口+适配Flex
.pro-layout {
  min-width: 1200px;
  width: 100% !important;
  height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  box-sizing: border-box !important;
}

// 侧边栏：隐藏null+深色背景+触发器样式
.pro-sider {
  background: #001529 !important;
  overflow: hidden !important; // 隐藏底部null
  // 侧边栏折叠触发器：自定义背景+消除null
  .ant-layout-sider-trigger {
    background: #1890ff !important;
    font-size: 0 !important; // 彻底消除trigger里的null文字
  }
}

// Logo容器：和顶栏/侧边栏高度匹配+排版舒展
.logo-container {
  min-height: 70px; // 匹配顶栏70px高度
  padding: 16px 20px; // 上下16px+左右20px，不挤不松
  background: #001529 !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important; // 内部元素垂直居中
  .logo-icon {
    font-size: 24px;
    color: #fff !important;
    flex-shrink: 0;
    white-space: nowrap;
  }
  .logo-title {
    margin-left: 12px !important;
    font-size: 18px;
    font-weight: 600;
    color: #fff !important;
    letter-spacing: 1px;
    flex-shrink: 0;
    white-space: nowrap;
  }
}

// 侧边菜单：匹配Logo高度+滚动条美化+间距优化
.pro-menu {
  border-right: none !important;
  height: calc(100vh - 70px) !important;
  overflow: auto;
  box-sizing: border-box !important;

  .ant-menu-item,
  .ant-submenu-title {
    margin: 4px 0 !important;
    .menu-title {
      white-space: nowrap;
    }
  }

  // 滚动条美化
  :deep(&::-webkit-scrollbar) {
    width: 6px;
    height: 6px;
  }

  :deep(&::-webkit-scrollbar-track) {
    background: #001529;
    border-radius: 3px;
  }

  :deep(&::-webkit-scrollbar-thumb) {
    background: #1890ff40;
    border-radius: 3px;
    transition: background 0.3s ease;
  }

  :deep(&::-webkit-scrollbar-thumb:hover) {
    background: #1890ff66;
  }

  :deep(&::-webkit-scrollbar-corner) {
    background: #001529;
  }
}

// 主布局：Flex垂直布局+顶栏/内容区不重叠+适配剩余宽度
.pro-main-layout {
  height: 100vh !important;
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
}

// 顶部栏：70px高度+按钮不溢出+所有元素同一行居中+hover柔和
.pro-header {
  height: 70px !important;
  line-height: 70px !important;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  box-sizing: border-box !important;
  padding: 0 20px !important;
  width: 100% !important;
  flex-shrink: 0 !important; // 禁止顶栏被挤压
  overflow: visible !important; // 避免按钮被隐藏

  // 顶栏内层容器：强制Flex居中，兜底排版
  .header-inner {
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
  }

  // 左侧折叠图标：大尺寸+充足点击区+hover效果
  .collapse-icon {
    font-size: 20px;
    color: #555;
    width: 48px;
    height: 48px;
    line-height: 48px;
    display: inline-block;
    text-align: center;
    border-radius: 8px;
    transition: all 0.2s ease;
    &:hover {
      color: #1890ff;
      background: #e6f7ff;
    }
  }

  // 右侧功能按钮组：不溢出+同一行+大图标
  .header-right {
    display: flex !important;
    align-items: center !important;
    gap: 30px !important; // 间距适中，避免溢出
    flex-shrink: 0 !important; // 禁止按钮组被挤压

    // 清除Antd按钮所有默认样式，避免宽度占用
    :deep(.ant-btn) {
      vertical-align: middle !important;
      margin: 0 !important;
      padding: 0 !important;
      width: auto !important;
      height: auto !important;
      border: none !important;
      background: none !important;
    }

    // 刷新/全屏按钮：和折叠图标同尺寸+hover统一
    .header-btn {
      font-size: 20px;
      color: #555;
      width: 48px;
      height: 48px;
      line-height: 48px;
      text-align: center !important;
      border-radius: 8px;
      transition: all 0.2s ease;
      &:hover {
        color: #1890ff !important;
        background: #e6f7ff !important;
      }
    }
  }
}

// 页面内容区：适配顶栏70px高度+自动滚动+内边距
.pro-content {
  height: calc(100vh - 70px) !important;
  overflow: auto;
  box-sizing: border-box !important;
  padding: 6px;
  flex: 1 !important;

  // 滚动条美化
  :deep(&::-webkit-scrollbar) {
    width: 8px;
    height: 8px;
  }

  :deep(&::-webkit-scrollbar-track) {
    background: #f0f2f5;
    border-radius: 4px;
  }

  :deep(&::-webkit-scrollbar-thumb) {
    background: #bfbfbf;
    border-radius: 4px;
    transition: background 0.3s ease;
  }

  :deep(&::-webkit-scrollbar-thumb:hover) {
    background: #8c8c8c;
  }

  :deep(&::-webkit-scrollbar-corner) {
    background: #f0f2f5;
  }
}

// 核心适配：让顶栏父容器自动占满侧边栏剩余宽度（解决按钮溢出关键）
:deep(.ant-layout-has-sider > .ant-layout) {
  flex: 1 !important;
  width: calc(100% - 200px) !important; // 匹配侧边栏展开宽度200px
}
// 侧边栏折叠时，主布局自动适配宽度
:deep(.ant-layout-sider-collapsed + .ant-layout) {
  width: calc(100% - 80px) !important; // 匹配侧边栏折叠宽度80px
}

// 响应式适配：小屏幕撑满100%，无横向滚动
@media (max-width: 991px) {
  .pro-layout {
    min-width: 100% !important;
  }
  :deep(.ant-layout-has-sider > .ant-layout) {
    width: 100% !important;
  }
}
</style>