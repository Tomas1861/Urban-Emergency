<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const crumb = computed(() => route.meta?.title || "");
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <div class="t1">复兴岛 · 量子城市</div>
        <div class="t2">应急预案<b>智能生成</b>平台</div>
      </div>
      <nav class="app-nav">
        <div class="grp">总览</div>
        <router-link :to="{ name: 'dashboard' }">态势大屏</router-link>
        <router-link :to="{ name: 'activities' }">活动列表</router-link>

        <div class="grp">知识管理</div>
        <router-link :to="{ name: 'knowledge-admin' }">知识库后台</router-link>
      </nav>
      <div style="padding:14px 18px;border-top:1px solid var(--line);font-size:11px;color:var(--dim)">
        MVP 教学实践演示
      </div>
    </aside>

    <div class="app-main">
      <div class="app-topbar">
        <span class="crumb">重大演绎活动应急预案智能生成教学实践平台</span>
      </div>
      <div class="app-content">
        <router-view />
      </div>
    </div>
  </div>
</template>
