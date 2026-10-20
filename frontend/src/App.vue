<script setup lang="ts">
import { onMounted, onBeforeUnmount, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Icon from './components/Icon.vue'
import AuthDialog from './components/AuthDialog.vue'
import Modal from './components/Modal.vue'
import { activateDrawer } from './lib/drawer'
import { user, notice, initSession, message, authOpen, sessionFrozen, identityChanging, sessionIssue, reconcileSession, checkSession, handleSessionSignal } from './lib/state'
const route=useRoute(), menu=ref(false), ready=ref(false), error=ref('')
const nav=[{to:'/',label:'学习工作台',icon:'home'},{to:'/library',label:'我的题库',icon:'library'},{to:'/discover',label:'发现题集',icon:'discover'},{to:'/history',label:'学习记录',icon:'history'}]
watch(()=>route.fullPath,()=>menu.value=false)
async function load(){error.value='';try{await initSession();ready.value=true}catch(e){error.value=message(e)}}
const sidebar=ref<HTMLElement>(),workspace=ref<HTMLElement>()
let releaseDrawer: (()=>void) | undefined
watch(menu,async open=>{
  releaseDrawer?.();releaseDrawer=undefined
  if(open){await nextTick();if(menu.value&&sidebar.value&&workspace.value)releaseDrawer=activateDrawer(sidebar.value,workspace.value,()=>menu.value=false)}
})
watch(authOpen,open=>{if(open)menu.value=false})
watch(sessionFrozen,frozen=>{if(frozen)menu.value=false})
function visible(){if(document.visibilityState==='visible')void checkSession()}
function resize(){if(window.innerWidth>760)menu.value=false}
onMounted(()=>{void load();window.addEventListener('storage',handleSessionSignal);window.addEventListener('focus',checkSession);window.addEventListener('resize',resize);document.addEventListener('visibilitychange',visible)})
onBeforeUnmount(()=>{releaseDrawer?.();window.removeEventListener('storage',handleSessionSignal);window.removeEventListener('focus',checkSession);window.removeEventListener('resize',resize);document.removeEventListener('visibilitychange',visible)})
</script>
<template>
  <a href="#main" class="skip-link" @click="menu=false">跳到主要内容</a>
  <div :inert="sessionFrozen||identityChanging" class="app-shell" :class="{'focus-mode':route.path.startsWith('/practice/')}">
    <Transition name="fade"><div v-if="menu" class="nav-scrim" @click="menu=false"/></Transition>
    <aside ref="sidebar" tabindex="-1" :role="menu?'dialog':undefined" :aria-modal="menu?true:undefined" aria-label="学习空间导航" class="sidebar" :class="{open:menu}" @keydown.esc="menu=false">
      <RouterLink to="/" class="brand"><span class="brand-mark"><Icon name="book"/></span><span>Exam<span class="brand-light">Hub</span></span></RouterLink>
      <button class="icon-button mobile-close" aria-label="关闭导航" @click="menu=false"><Icon name="close"/></button>
      <RouterLink to="/sets/new" class="button primary create-nav"><Icon name="plus"/>创建题集</RouterLink>
      <nav aria-label="主导航"><RouterLink v-for="item in nav" :key="item.to" :to="item.to" class="nav-item" :class="{active:route.path===item.to}"><Icon :name="item.icon"/>{{item.label}}</RouterLink></nav>
      <div class="sidebar-bottom"><RouterLink to="/settings" class="nav-item" active-class="active"><Icon name="settings"/>模型设置</RouterLink><div class="identity"><span class="avatar"><Icon name="user"/></span><div><strong>{{user?.name || '学习者'}}</strong><button v-if="!user?.email" class="text-button" @click="authOpen=true">访客模式 · 绑定账户</button><span v-else class="muted small">个人学习空间</span></div></div></div>
    </aside>
    <div ref="workspace" class="workspace"><header class="topbar"><div class="row"><button class="icon-button mobile-menu" aria-label="打开导航" :aria-expanded="menu" @click="menu=!menu"><Icon name="menu"/></button><span class="breadcrumb">个人空间 <span>/</span> <strong>{{route.meta.title}}</strong></span></div><RouterLink to="/discover" class="top-discover"><Icon name="search"/>寻找下一份知识</RouterLink><button class="avatar" aria-label="账户设置" @click="user?.email ? $router.push('/settings') : authOpen=true">{{user?.name?.slice(0,1)||'我'}}</button></header>
      <main id="main" tabindex="-1"><div v-if="error" class="empty-state"><Icon name="warning"/><h2>暂时无法打开学习空间</h2><p>{{error}}</p><button class="button primary" @click="load">重新连接</button></div><div v-else-if="!ready" class="loading" role="status">正在打开你的学习空间…</div><RouterView v-else :key="user?.id" v-slot="{Component}"><Transition name="page" mode="out-in"><component :is="Component" :key="route.path"/></Transition></RouterView></main>
      <footer class="app-footer"><span>ExamHub · 让知识成为自己的</span><span>专注每一次练习</span></footer>
    </div>
  </div><AuthDialog/><Modal :open="sessionFrozen" title="账户已在其他页面切换" :dismissible="false"><p>当前页面已暂停操作，仍显示原账户内容。未提交作答和编辑草稿会保留在原账户下。</p><p class="muted small">确认后加载当前账户；不会将原账户的作答提交给新账户。返回原账户可恢复原有草稿。</p><p v-if="sessionIssue" class="error" role="alert">{{sessionIssue}}</p><div class="modal-actions"><button class="button primary" :disabled="identityChanging" @click="reconcileSession">{{identityChanging?'正在确认…':'确认当前账户并继续'}}</button></div></Modal><Transition name="toast"><div v-if="notice" class="toast" role="status"><Icon name="check"/>{{notice}}</div></Transition>
</template>
