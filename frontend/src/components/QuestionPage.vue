<script lang="ts" setup>
import QTop from "@/components/question/QTop.vue";
import {ref} from "vue";
import {useQuestionStore} from "@/stores/question";
import {ElMessage} from "element-plus";

const questionStore = useQuestionStore();
const questionNeed = ref('')
const createTopic = () => {
  const target = questionStore.question?.target;
  const type = questionStore.question?.type;
  const difficult = questionStore.question?.difficult;
  console.log(target,type,difficult)
  if (target?.length === 0 || type === '' || difficult === 0) {
    ElMessage({
      message: '请选择学科类型、题目种类和难度系数',
      type: 'warning',
    })
    return
  }
  if (questionNeed.value === '') {
    ElMessage({
      message: '请输入完整的需求',
      type: 'warning',
    })
    return
  }
}

</script>

<template>
  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <QTop/>
    <div class="divider mt-1 mb-1"></div>
    <el-input
        v-model="questionNeed"
        :autosize="{ minRows: 18, maxRows: 20 }"
        class="t-a"
        placeholder="输入您的需求"
        resize="none"
        type="textarea"
    />
    <div class="divider mt-1 mb-1"></div>
    <el-button class="opposans w-1/3 ml-auto mr-auto" type="success" @click="createTopic">提交任务需求</el-button>
  </div>
</template>

<style scoped>
</style>