import { createRouter, createWebHistory } from 'vue-router';
import RoomList from './components/RoomList.vue';
import RoomJoin from './components/RoomJoin.vue';
import WaitingLobby from './components/WaitingLobby.vue';
import GameTimer from './components/GameTimer.vue';
import TrialPanel from './components/TrialPanel.vue';
import RevealPanel from './components/RevealPanel.vue';

const routes = [
  { path: '/', component: RoomList },
  { path: '/join/:gameId', component: RoomJoin },
  { path: '/lobby/:gameId', component: WaitingLobby },
  { path: '/game/:gameId', component: GameTimer },
  { path: '/trial/:gameId', component: TrialPanel },
  { path: '/reveal/:gameId', component: RevealPanel },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
