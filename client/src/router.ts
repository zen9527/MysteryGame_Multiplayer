import { createRouter, createWebHistory } from 'vue-router';

const RoomList = () => import('./components/RoomList.vue');
const RoomJoin = () => import('./components/RoomJoin.vue');
const WaitingLobby = () => import('./components/WaitingLobby.vue');
const GamePage = () => import('./components/GamePage.vue');
const RoomCreate = () => import('./pages/RoomCreate.vue');

const routes = [
  { path: '/', component: RoomList },
  { path: '/join/:gameId', component: RoomJoin },
  { path: '/lobby/:gameId', component: WaitingLobby },
  { path: '/game/:gameId', component: GamePage },
  { path: '/create', component: RoomCreate },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
