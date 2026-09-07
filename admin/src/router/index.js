import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/", redirect: "/documents" },
  { path: "/documents", name: "documents", component: () => import("../views/DocumentsView.vue") },
  { path: "/graph", name: "graph", component: () => import("../views/GraphView.vue") },
  { path: "/settings", name: "settings", component: () => import("../views/SettingsView.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
