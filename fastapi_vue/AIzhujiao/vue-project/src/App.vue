<script setup>
// 不需要额外导入，<router-link> 是全局组件
</script>

<template>
  <div id="app">
    <!-- 方法 1: 使用 router-link (推荐，类似 a 标签) -->
    <h1>欢迎使用本系统</h1>
    <p>
      <router-link to="/smart-qa" style="font-size: 20px; color: blue; text-decoration: underline;">
        点击进入智能问答 (SmartQA)
      </router-link>
    </p>

    <!-- 方法 2: 使用普通按钮 + JS 跳转 -->
    <!--
    <button @click="$router.push('/smart-qa')">去智能问答</button>
    -->

    <!-- 重要：保留这个标签，它是显示具体页面内容的地方 -->
    <router-view />
  </div>
</template>

<style scoped>
/* 样式保持不变 */
</style>