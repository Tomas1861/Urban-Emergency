<script setup>
</script>

<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <div class="t1">复兴岛 · 量子城市</div>
        <div class="t2">应急预案<b>管理后台</b></div>
      </div>
      <nav class="app-nav">
        <div class="grp">知识管理</div>
        <router-link :to="{ name: 'documents' }">RAG 文件管理</router-link>
        <router-link :to="{ name: 'graph' }">知识图谱（GraphRAG）</router-link>

        <div class="grp">系统</div>
        <router-link :to="{ name: 'settings' }">其他设置</router-link>
      </nav>
      <div style="padding:14px 18px;border-top:1px solid var(--line);font-size:11px;color:var(--dim)">
        管理后台 · 独立部署
      </div>
    </aside>

    <div class="app-main">
      <div class="app-topbar">
        <span class="crumb">重大演绎活动应急预案智能生成系统 · 管理后台</span>
      </div>
      <div class="app-content">
        <router-view />
      </div>
    </div>
  </div>
</template>
