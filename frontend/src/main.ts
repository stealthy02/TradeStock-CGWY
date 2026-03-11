import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { ConfigProvider } from "ant-design-vue";
import zhCN from "ant-design-vue/es/locale/zh_CN";
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

// 全局配置
dayjs.locale('zh-cn')
const app = createApp(App)

app.use(router)
app.use(ConfigProvider, {
  locale: zhCN,
  theme: {
    token: {
      colorPrimary: '#1890ff'
    }
  }
})

// 全局挂载dayjs
app.config.globalProperties.$dayjs = dayjs

app.mount('#app')