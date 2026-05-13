import { createRouter, createWebHistory } from 'vue-router';

const RoomList = () => import('./components/RoomList.vue');
const RoomJoin = () => import('./components/RoomJoin.vue');
const WaitingLobby = () => import('./components/WaitingLobby.vue');
const GamePage = () => import('./components/GamePage.vue');
const RoomCreate = () => import('./pages/RoomCreate.vue');
const ScriptsPage = () => import('./components/scripts/ScriptsPage.vue');

const routes = [
  { path: '/', component: RoomList },
  { path: '/join/:gameId', component: RoomJoin },
  { path: '/lobby/:gameId', component: WaitingLobby },
  { path: '/game/:gameId', component: GamePage },
  { path: '/create', component: RoomCreate },
  { path: '/scripts', component: ScriptsPage },
  { path: '/scripts/generate', component: () => import('./components/scripts/ScriptGenerateWizard.vue') },
  { path: '/scripts/edit/:id', component: () => import('./components/scripts/ScriptEditor.vue'), meta: { placeholder: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
