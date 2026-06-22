import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/connections',
      name: 'connections',
      component: () => import('@/views/ConnectionView.vue'),
    },
    {
      path: '/meta-import',
      name: 'metaImport',
      component: () => import('@/views/MetaImportView.vue'),
    },
    {
      path: '/meta-config',
      name: 'metaConfig',
      component: () => import('@/views/MetaConfigView.vue'),
    },
    {
      path: '/dv-config',
      name: 'dvConfig',
      component: () => import('@/views/DvConfigView.vue'),
    },
    {
      path: '/generate',
      name: 'generate',
      component: () => import('@/views/GenerateView.vue'),
    },
    {
      path: '/deploy',
      name: 'deploy',
      component: () => import('@/views/DeployView.vue'),
    },
    {
      path: '/logs',
      name: 'logs',
      component: () => import('@/views/LogsView.vue'),
    },
    {
      path: '/intro',
      name: 'intro',
      component: () => import('@/views/IntroView.vue'),
    },
  ],
})

export default router