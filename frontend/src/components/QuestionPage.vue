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

const questionStore = useQuestionStore();
const questionNeed = ref('')
const titleStore = useTitleStore();
const loading = ref(false);
const createTopic = async () => {
  const target = questionStore.question?.target;
  const type = questionStore.question?.type;
  const difficult = questionStore.question?.difficult;
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
      const result_arr = result_str.split('答案解析：');
      const result_arr2 = result_arr[1].split('评分标准：');
      titleStore.setTitle({question: result_arr[0], answer: result_arr2[0], standard: result_arr2[1]})
      ElMessage({
        message: '题目生成完毕',
        type: 'success',
      })
      emitter.emit('answer-page-setting')
    }
  } catch (e) {
    ElMessage({
      message: '生成题目失败',
      type: 'error',
    })
  }
}

const randomRequire = async () => {
  questionNeed.value = ''
  const target = questionStore.question?.target;
  const type = questionStore.question?.type;
  const difficult = questionStore.question?.difficult;
  if (target?.length === 0 || type === '' || difficult === 0) {
    ElMessage({
      message: '请选择学科类型、题目种类和难度系数',
      type: 'warning',
    })
    return
  }
  const response = await fetch("http://localhost:5000/api/requirement", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      target: target,
      type: type,
      difficult: difficult,
    }),
  });
  const reader = response.body!.getReader();
  while (true) {
    const {done, value} = await reader.read();
    const chunk = new TextDecoder().decode(value);
    questionNeed.value += chunk;
    if (done) {
      break;
    }
  }
  reader.releaseLock();
  ElMessage({
    message: '随机需求生成完毕',
    type: 'success',
  })
}

function toWhole() {
  router.push({
    name: "index",
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
      <el-button class="opposans w-1/4 " type="info" @click="randomRequire">生成随机需求</el-button>
      <el-button class="opposans w-1/4 " type="success" @click="createTopic">提交任务需求</el-button>
      <el-button class="opposans w-1/4 " type="warning" @click="toWhole">切换到整卷</el-button>
    </div>
  </div>
</template>

<style scoped>
</style>