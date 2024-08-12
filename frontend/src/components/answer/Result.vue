<script lang="ts" setup>
import {ref} from "vue";

const answer = ref()
</script>

<template>
  <el-input
      v-model="answer"
      :rows="10"
      placeholder="输入您的答案"
      resize="none"
      type="textarea"
  />
</template>

<style scoped>

</style>