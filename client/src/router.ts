import { createRouter, createWebHistory } from 'vue-router';
import RoomList from './components/RoomList.vue';
import RoomJoin from './components/RoomJoin.vue';
import WaitingLobby from './components/WaitingLobby.vue';
import GamePage from './components/GamePage.vue';

const routes = [
  { path: '/', component: RoomList },
  { path: '/join/:gameId', component: RoomJoin },
  { path: '/lobby/:gameId', component: WaitingLobby },
  { path: '/game/:gameId', component: GamePage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
