<script lang="ts" setup>
import * as docx from "docx";
import {Paragraph} from "docx";
import dayjs from "dayjs";
import {onMounted, onUnmounted, ref} from "vue";
// @ts-ignore
import emitter from "@/utils/mitter";
import {useTitleStore} from "@/stores/title";
import {ElMessage} from "element-plus";

const answerInput = ref('')
const titleStore = useTitleStore();
const answer = ref('')
const question = ref('')

const resultDialog = ref();

const initPage = () => {
  answer.value = titleStore.title?.answer!;
  question.value = titleStore.title?.question!;
}

const sendAnswer = () => {
  if (answerInput.value === '') {
    ElMessage({
      message: '请填入你的答案',
      type: 'error',
    })
  }
}

const viewAnswer = () => {
  resultDialog.value.showModal()
}
const closeAnswer = () => {
  resultDialog.value.close()
}
const clipAnswer = () => {
  navigator.clipboard.writeText(answer.value)
  ElMessage({
    message: '复制答案成功',
    type: 'success',
  })
};

function exportWord() {
  const fileName = dayjs().format('YYYYMMDDHHmmss') + '.docx';
  const fullText = question.value + '\n' + answer.value; // 确保两个值之间有换行符

// 使用正则表达式替换换行符为 TextRun 的换行
  const textRuns = fullText.split('\n');
  const doc = new docx.Document({
    //文档作者，显示在文档属性中
    creator: "BUPT_AI",
    title: fileName,
    description: 'AI出题，仅供参考',
    sections: [
      {
        properties: {},
        //主体内容
        children: fullText.split('\n').map((t, index) => {
          return new Paragraph({text: t})
        }),
      },
    ],
  });
  docx.Packer.toBlob(doc).then((blob) => {
    const blobUrl = URL.createObjectURL(blob);
    const downloadLink = document.createElement("a");
    downloadLink.href = blobUrl;
    downloadLink.download = fileName;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
  });
}

onMounted(() => {
  emitter.on('answer-page-setting', initPage);
})
onUnmounted(() => {
  emitter.off('answer-page-setting', initPage);
})
</script>

<template>
  <dialog ref="resultDialog" class="modal">
    <div class="modal-box">
      <form method="dialog">
        <button
            class="btm-circle btn btn-ghost btn-sm absolute right-2 top-2"
            @click="closeAnswer"
        >
          <i class="ri-close-line"></i>
        </button>
      </form>
      <h3 class="alidongfang text-lg font-bold">AI解析</h3>
      <div class="opposans py-4 break-words whitespace-break-spaces">{{ answer }}</div>
      <form class="top-2 flex justify-end">
        <button class="opposans btn" @click.prevent="clipAnswer">
          <i class="ri-clipboard-line"></i>复制
        </button>
      </form>
    </div>
  </dialog>


  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <div class="flex flex-col">
      <h1 class="opposans mt-1 text-[16px] text-[--black-light-color]">题目要求</h1>
      <div class="h-[280px] overflow-y-auto opposans break-words whitespace-break-spaces">
        {{ question }}
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <div class="flex flex-col">
      <h1 class="opposans text-[16px] text-[--black-light-color]">你的答案</h1>
      <div class="h-[200px] overflow-y-auto opposans">
        <el-input
            v-model="answerInput"
            :rows="8"
            placeholder="输入您的答案"
            resize="none"
            type="textarea"
        />
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <el-button-group class="ml-auto mr-auto">
      <el-button plain type="primary" @click="sendAnswer">提交答案</el-button>
      <el-button plain type="primary" @click="viewAnswer">查看解析</el-button>
      <el-button plain type="primary" @click="exportWord">导出word</el-button>
    </el-button-group>
  </div>
</template>

<style scoped>

</style>