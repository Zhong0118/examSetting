<script lang="ts" setup>
import {ref} from "vue";

const answer = ref()
</script>

<template>
  <span class="mr-2">错误</span>
  <input v-model="answer" class="toggle toggle-secondary translate-y-1/4" type="checkbox"/>
  <span class="ml-2">正确</span>
</template>

<style scoped>

</style>