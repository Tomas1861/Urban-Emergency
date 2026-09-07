import { createRouter, createWebHistory } from "vue-router";

const routes = [
  { path: "/", redirect: "/activities" },
  { path: "/activities", name: "activities", component: () => import("../views/ActivityListView.vue") },
  { path: "/activities/:id", name: "activity-detail", component: () => import("../views/ActivityDetailView.vue"), props: true },
  {
    path: "/events/new",
    name: "event-new",
    component: () => import("../views/EventEditorView.vue"),
    props: (route) => ({ id: "new", activityId: route.query.activityId, sceneId: route.query.sceneId }),
  },
  { path: "/events/:id", name: "event-editor", component: () => import("../views/EventEditorView.vue"), props: true },
  { path: "/events/:id/knowledge", name: "knowledge-selection", component: () => import("../views/KnowledgeSelectionView.vue"), props: true },
  { path: "/events/:id/plan", name: "plan-editor", component: () => import("../views/PlanEditorView.vue"), props: true },
  { path: "/events/:id/tasks", name: "task-board", component: () => import("../views/TaskBoardView.vue"), props: true },
  { path: "/events/:id/execution", name: "execution-panel", component: () => import("../views/ExecutionPanelView.vue"), props: true },
  { path: "/events/:id/report", name: "report-editor", component: () => import("../views/ReportEditorView.vue"), props: true },
  { path: "/knowledge", name: "knowledge-admin", component: () => import("../views/KnowledgeAdminView.vue") },
  { path: "/dashboard", name: "dashboard", component: () => import("../views/DashboardView.vue") },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
