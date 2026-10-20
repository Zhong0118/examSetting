<script setup lang="ts">
import { House, Collection, Compass, Clock, Setting, Plus, ArrowRight, ArrowLeft, Search, Close, Menu, Document, Edit, Star, Share, Download, CopyDocument, Delete, Check, Refresh, ChatLineSquare, Reading, Lock, User, SwitchButton, Warning } from '@element-plus/icons-vue'
defineProps<{name?: string}>()
const icons: Record<string,unknown> = {home:House,library:Collection,discover:Compass,history:Clock,settings:Setting,plus:Plus,right:ArrowRight,left:ArrowLeft,search:Search,close:Close,menu:Menu,document:Document,edit:Edit,star:Star,share:Share,download:Download,copy:CopyDocument,delete:Delete,check:Check,refresh:Refresh,ai:ChatLineSquare,book:Reading,lock:Lock,user:User,logout:SwitchButton,warning:Warning}
</script>
<template><svg class="icon" viewBox="0 0 1024 1024" aria-hidden="true"><component :is="icons[name || 'document']" /></svg></template>
