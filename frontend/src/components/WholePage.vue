<script lang="ts" setup>
import QTop from "@/components/question/QTop.vue";
import {ref} from "vue";
import {useQuestionStore} from "@/stores/question";
import {ElLoading, ElMessage} from "element-plus";
import {useTitleStore} from "@/stores/title";
// @ts-ignore
import emitter from "@/utils/mitter";
// @ts-ignore
import router from "@/router";
import Multiple from "@/components/answer/Multiple.vue";
import Single from "@/components/answer/Single.vue";
import Blank from "@/components/answer/Blank.vue";
import Result from "@/components/answer/Result.vue";
import Check from "@/components/answer/Check.vue";

const questionStore = useQuestionStore();
const questionNeed = ref('')
const titleStore = useTitleStore();
const loading = ref(false);
const createTopic = async () => {
  const target = questionStore.question?.target;
  const type = questionStore.question?.type;
  const difficult = questionStore.question?.difficult;
  console.log(difficult)
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
  const loadingInstance = ElLoading.service({
    lock: true,
    text: "生成题目中，请稍候...",
    background: "rgba(0, 0, 0, 0.7)",
  });
  loading.value = true;
  try {
    const response = await fetch("http://localhost:5000/api/single", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        target: target,
        type: type,
        difficult: difficult,
        questionNeed: questionNeed.value,
      }),
    });
    if (response.status === 200) {
      loading.value = false;
      loadingInstance.close()
      const result = await response.json()
      const result_str = result.message;
      const result_arr = result_str.split('\n\n');
      const type_str = type;
      if (type_str === '单选' || type_str === '多选') {
        const answer = result_arr[3] + '\n' + result_arr[4];
        const q = result_arr[1];
        const options = result_arr[2].split('\n');
        // @ts-ignore
        titleStore.setTitle({type_str, answer, q, options})
      } else {
        const answer = result_arr[3] + '\n' + result_arr[4];
        const q = result_arr[1];
        // @ts-ignore
        titleStore.setTitle({type_str, answer, q})
      }
      emitter.emit('answer-page-setting')
    }
  } catch (e) {
    ElMessage({
      message: '生成题目失败',
      type: 'error',
    })
  }
}

function toSingle() {
  router.push({
    name: "index2",
  })
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
    <div class="flex flex-row justify-center w-full">
      <el-button class="opposans w-1/4 " type="success" @click="createTopic">提交任务需求</el-button>
      <el-button class="opposans w-1/4 " type="warning" @click="toSingle">切换到单题</el-button>
    </div>
  </div>

  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <div class="flex flex-col">
      <h1 class="opposans mt-1 text-[16px] text-[--black-light-color]">试题</h1>
      <div class="divider mt-1 mb-1"></div>
      <div class="h-[500px] overflow-y-auto opposans">

      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <el-button class="opposans w-1/3 mr-auto ml-auto " type="primary" @click="toSingle">导出word</el-button>
  </div>
</template>

<style scoped>
</style>