<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../lib/api'
import { authOpen, user, notify, message, changeIdentity } from '../lib/state'
import Modal from './Modal.vue'
const mode = ref<'login'|'register'>('register'), name=ref(''), email=ref(''), password=ref(''), error=ref(''), busy=ref(false)
async function submit() { busy.value=true; error.value=''; try { if(!await changeIdentity(()=>api.auth(mode.value,{name:name.value,email:email.value,password:password.value})))return; authOpen.value=false; password.value='';   } catch(e){error.value=message(e)} finally{busy.value=false} }
</script>
<template><Modal :open="authOpen" :title="mode==='register'?'把学习留在自己的账户':'欢迎回来'" @close="authOpen=false"><p class="muted">{{mode==='register'?'绑定当前访客记录，下次登录继续学习':'登录后查看该账户的题集和学习记录'}}</p><form class="form-stack" @submit.prevent="submit"><label v-if="mode==='register'">称呼<input v-model="name" autocomplete="name" maxlength="80" required placeholder="如何称呼你"/></label><label>邮箱<input v-model="email" type="email" autocomplete="email" required placeholder="you@example.com"/></label><label>密码<input v-model="password" type="password" :autocomplete="mode==='register'?'new-password':'current-password'" minlength="8" required placeholder="至少 8 位字符"/></label><p v-if="error" class="error" role="alert">{{error}}</p><button class="button primary" :disabled="busy">{{busy?'正在处理…':mode==='register'?'创建账户':'登录'}}</button><button type="button" class="text-button" @click="mode=mode==='register'?'login':'register';error=''">{{mode==='register'?'已有账户？去登录':'还没有账户？创建账户'}}</button></form></Modal></template>
