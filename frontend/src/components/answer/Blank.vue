<script lang="ts" setup>
import {ref} from "vue";

const answer = ref('')
</script>

<template>
  <el-input v-model="answer" placeholder="请输入答案" style="width: 240px"/>
</template>

<style scoped>

</style>