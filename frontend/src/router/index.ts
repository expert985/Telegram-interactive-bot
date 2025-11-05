import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '数据概览', icon: 'DataAnalysis' }
      },
      {
        path: 'protection',
        name: 'Protection',
        component: () => import('@/pages/Protection.vue'),
        meta: { title: '防护控制台', icon: 'Shield' }
      },
      {
        path: 'workbench',
        name: 'Workbench',
        component: () => import('@/pages/Workbench.vue'),
        meta: { title: '客服工作台', icon: 'ChatDotRound' }
      },
      {
        path: 'threat',
        name: 'Threat',
        component: () => import('@/pages/ThreatIntelligence.vue'),
        meta: { title: '威胁情报', icon: 'Warning' }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/pages/Monitor.vue'),
        meta: { title: '实时监控', icon: 'Monitor' }
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/pages/Accounts.vue'),
        meta: { title: '账号管理', icon: 'User' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - Telegram 智能客服系统`
  }

  // TODO: 添加登录验证
  // const token = localStorage.getItem('token')
  // if (!token && to.path !== '/login') {
  //   next('/login')
  // } else {
  //   next()
  // }

  next()
})

export default router
