import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Player from '../views/Player.vue'
import Collection from '../views/Collection.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/play/:bvid', component: Player, props: true },
  { path: '/collection', component: Collection },
  { path: '/stats', component: () => import('../views/Stats.vue') },
  { path: '/courses', component: () => import('../views/Courses.vue') },
  { path: '/user/:mid', component: () => import('../views/User.vue'), props: true },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
