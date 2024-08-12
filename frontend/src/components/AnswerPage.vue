<script lang="ts" setup>

import Single from "@/components/answer/Single.vue";
import Check from "@/components/answer/Check.vue";
import Blank from "@/components/answer/Blank.vue";
import Result from "@/components/answer/Result.vue";
import Multiple from "@/components/answer/Multiple.vue";
</script>

<template>
  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <div class="flex flex-col">
      <h1 class="opposans mt-1 text-[16px] text-[--black-light-color]">题目要求</h1>
      <div class="h-[240px] overflow-y-auto opposans">

      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <div class="flex flex-col">
      <h1 class="opposans text-[16px] text-[--black-light-color]">你的答案</h1>
      <div class="h-[240px] overflow-y-auto opposans">
<!--        <Single/>-->
<!--        <Check/>-->
<!--        <Blank/>-->
<!--        <Result/>-->
        <Multiple/>
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <el-button-group class="ml-auto mr-auto">
      <el-button plain type="primary">提交答案</el-button>
      <el-button plain type="primary">查看解析</el-button>
      <el-button plain type="primary">导出word</el-button>
    </el-button-group>
  </div>
</template>

<style scoped>

</style>