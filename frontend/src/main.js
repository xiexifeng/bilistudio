import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')

// Service Worker 管理
if ('serviceWorker' in navigator) {
  if (import.meta.env.PROD) {
    // 生产模式：注册 SW
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  } else {
    // 开发模式：注销所有已注册的 SW，避免缓存干扰热更新
    navigator.serviceWorker.getRegistrations().then(regs => {
      regs.forEach(r => r.unregister())
    })
  }
}
