import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Layout from '@/layout/index.vue'

const routes: Array<RouteRecordRaw> = [
  // 根路由：重定向到首页，隐藏不生成菜单
  {
    path: '/',
    redirect: '/layout/home',
    meta: { hidden: true },
  },
  // 【新增：刷新页面的重定向路由】解决handleRefresh跳转404问题
  {
    path: '/redirect',
    component: Layout,
    meta: { hidden: true },
    children: [
      { path: ':path(.*)',
        component: () => import('@/views/redirect.vue')
      }
    ]
  },
  // 【核心重构】全局唯一Layout根路由：所有业务模块都是它的子路由
  {
    path: '/layout',
    component: Layout, // 仅这里挂载一次Layout，全局唯一
    meta: {}, // 无标题/图标，不单独生成菜单项
    children: [
      // 1. 首页-数据总览（纯一级菜单项，无折叠箭头）
      {
        path: 'home',
        meta: { title: '首页-数据总览', icon: 'DashboardOutlined' },
        component: () => import('@/views/home.vue')
      },
      // 2. 基础信息管理（折叠父菜单+二级子菜单）
      {
        path: 'basic',
        meta: { title: '基础信息管理', icon: 'ProfileOutlined' },
        children: [
          { path: 'supplier', meta: { title: '供货商信息' }, component: () => import('@/views/basic/supplier.vue') },
          { path: 'purchaser', meta: { title: '采购商信息' }, component: () => import('@/views/basic/purchaser.vue') }
        ]
      },
      // 3. 采购管理（折叠父菜单+二级子菜单）
      {
        path: 'purchase',
        meta: { title: '采购管理', icon: 'ShoppingOutlined' },
        children: [
          { path: 'info', meta: { title: '采购信息录入/查询' }, component: () => import('@/views/purchase/info.vue') },
          { path: 'bill', meta: { title: '采购对账单管理' }, component: () => import('@/views/purchase/bill.vue') }
        ]
      },
      // 4. 销售管理（折叠父菜单+二级子菜单）
      {
        path: 'sale',
        meta: { title: '销售管理', icon: 'ShopOutlined' },
        children: [
          { path: 'info', meta: { title: '销售信息录入/查询' }, component: () => import('@/views/sale/info.vue') },
          { path: 'bill', meta: { title: '销售对账单管理' }, component: () => import('@/views/sale/bill.vue') }
        ]
      },
      // 5. 库存管理（【修改6：统一icon为StockOutlined】）
      {
        path: 'inventory',
        meta: { title: '库存管理', icon: 'StockOutlined' },
        children: [
          { path: 'list', meta: { title: '当前库存查询' }, component: () => import('@/views/inventory/list.vue') },
          { path: 'loss', meta: { title: '库存报损录入/查询' }, component: () => import('@/views/inventory/loss.vue') },
          { path: 'detail', meta: { title: '库存商品流动详情' }, component: () => import('@/views/inventory/detail.vue') }
        ]
      },
      // 6. 成本费用管理（折叠父菜单+二级子菜单）
      {
        path: 'cost',
        meta: { title: '成本费用管理', icon: 'MoneyCollectOutlined' },
        children: [
          { path: 'fee', meta: { title: '运营杂费录入/查询' }, component: () => import('@/views/cost/fee.vue') }
        ]
      }
    ]
  },
  // 404页面：隐藏不生成菜单
  {
    path: '/404',
    component: () => import('@/views/404.vue'),
    meta: { title: '页面不存在', hidden: true }
  },
  // 通配符路由：匹配所有未定义路由，重定向404，隐藏
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: { hidden: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

// 全局路由守卫：动态设置页面标题，匹配你的系统名称
router.beforeEach((to, _from, next) => {
  document.title = `${to.meta?.title || '首页'} - 库存结算管理`
  next()
})

export default router