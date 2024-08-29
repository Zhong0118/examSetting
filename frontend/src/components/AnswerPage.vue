<script lang="ts" setup>
import * as docx from "docx";
import {Paragraph} from "docx";
import dayjs from "dayjs";
import {onMounted, onUnmounted, ref} from "vue";
// @ts-ignore
import emitter from "@/utils/mitter";
import {useTitleStore} from "@/stores/title";
import {ElMessage} from "element-plus";
import {useQuestionStore} from "@/stores/question";
import {marked} from "marked";

const answerInput = ref('')
const titleStore = useTitleStore();
const questionStore = useQuestionStore();
const answer = ref('')
const question = ref('')
const standard = ref('')
const target = ref([])

const initPage = () => {
  answer.value = titleStore.title?.answer!;
  question.value = titleStore.title?.question!;
  standard.value = titleStore.title?.standard!;
  // @ts-ignore
  target.value = questionStore.question?.target!;
}


// ai对话
const openAItalk = ref(false);
const sendAiQuestion = ref("");
const aiTalkDialog = ref();

const sendAiMessage = async () => {
  const userMessageDiv = document.createElement("div");
  userMessageDiv.className = "flex flex-row px-4 py-8 sm:px-6";
  const userImg = document.createElement("img");
  userImg.className = "mr-2 flex h-8 w-8 rounded-full sm:mr-4";
  userImg.src = "src/assets/icons/talkuser.svg";
  const userText = document.createElement("div");
  userText.className = "flex max-w-3xl items-center";
  const userP = document.createElement("p");
  userP.className = "opposans";
  let text: string | undefined = sendAiQuestion.value;
  userP.textContent = text;
  userText.appendChild(userP);
  userMessageDiv.appendChild(userImg);
  userMessageDiv.appendChild(userText);
  aiTalkDialog.value.appendChild(userMessageDiv);
  sendAiQuestion.value = "";

  const aiMessageDiv = document.createElement("div");
  aiMessageDiv.className =
      "flex bg-slate-100 px-4 py-8 dark:bg-slate-900 sm:px-6";
  const aiImg = document.createElement("img");
  aiImg.className = "mr-2 flex h-8 w-8 rounded-full sm:mr-4";
  aiImg.src = "src/assets/icons/talkai.svg";
  const aiText = document.createElement("div");
  aiText.className =
      "flex w-full flex-col items-start lg:flex-row lg:justify-between";
  const aiP = document.createElement("p");
  aiP.className = "max-w-3xl opposans";
  aiText.appendChild(aiP);
  aiMessageDiv.appendChild(aiImg);
  aiMessageDiv.appendChild(aiText);
  aiTalkDialog.value.appendChild(aiMessageDiv);

  const response = await fetch("http://localhost:5000/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: text,
    }),
  });
  const reader = response.body!.getReader();
  let returnText = "";
  while (true) {
    const {done, value} = await reader.read();
    const chunk = new TextDecoder().decode(value);
    returnText += chunk;
    aiP.innerHTML = <string>marked.parse(returnText);
    if (done) {
      break;
    }
  }
  reader.releaseLock();
};

function cancelAiMessage() {
  sendAiQuestion.value = "";
  openAItalk.value = false;
}


const chatOpen = () => {
  if (target.value.length === 0) {
    ElMessage({
      message: '请生成题目',
      type: 'error',
    })
  } else {
    openAItalk.value = true;
  }
}

// 为后端发送答案，进行评价
const analyseDialog = ref();
const analyseChat = ref();
const sendAnswer = async () => {
  if (answerInput.value === '' || target.value.length === 0) {
    ElMessage({
      message: '请填入你的答案',
      type: 'error',
    })
    return;
  }
  analyseChat.value.innerHTML = '';
  analyseDialog.value.showModal();
  const response = await fetch("http://localhost:5000/api/check", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: answerInput.value,
    }),
  });
  const aiBP = document.createElement("p");
  analyseChat.value.appendChild(aiBP);
  const reader = response.body!.getReader();
  let returnText = "";
  while (true) {
    const {done, value} = await reader.read();
    const chunk = new TextDecoder().decode(value);
    returnText += chunk;
    aiBP.innerHTML = <string>marked.parse(returnText);
    if (done) {
      break;
    }
  }
  reader.releaseLock();
}

const closeAnalyse = () => {
  analyseDialog.value.close()
}

// 打开初始生成的AI答案框架
const resultDialog = ref();
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

// 导出word
function exportWord() {
  let fileName1 = '';
  for (let i = 0; i < target.value.length; i++) {
    fileName1 += (target.value[i]);
  }
  const fileName2 = dayjs().format('YYYYMMDDHHmmss');
  const fileName = fileName1 + fileName2 + '.docx';
  const fullText = question.value + '\n' + answer.value + '\n' + standard.value;
  const doc = new docx.Document({
    //文档作者，显示在文档属性中
    creator: "BUPT_AI",
    title: fileName,
    description: 'AI出题，仅供参考',
    sections: [
      {
        properties: {},
        //主体内容
        children: fullText.split('\n').map((t) => {
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
  <!--  <div v-show="openAItalk" class="drop-shadow-xl fixed z-[999] flex h-[75%] w-[65%] flex-col right-1/2 translate-x-1/2">-->
  <!--    <div-->
  <!--        ref="aiTalkDialog"-->
  <!--        class="flex-1 overflow-y-auto bg-slate-300 text-sm leading-6 text-slate-900 shadow-md sm:text-base sm:leading-7 dark:bg-slate-800 dark:text-slate-300"-->
  <!--    ></div>-->
  <!--    &lt;!&ndash; Prompt message input &ndash;&gt;-->
  <!--    <div-->
  <!--        class="flex w-full items-center rounded-b-md border-t border-slate-300 bg-slate-200 p-2 dark:border-slate-700 dark:bg-slate-900"-->
  <!--    >-->
  <!--      <label class="sr-only" for="chat">输入</label>-->
  <!--      <textarea-->
  <!--          id="chat-input"-->
  <!--          v-model="sendAiQuestion"-->
  <!--          class="mx-2 flex min-h-full w-full rounded-md border border-slate-300 bg-slate-50 p-2 text-base text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-50 dark:placeholder-slate-400 dark:focus:border-blue-600 dark:focus:ring-blue-600"-->
  <!--          placeholder="输入文本"-->
  <!--          rows="3"-->
  <!--      ></textarea>-->
  <!--      <div>-->
  <!--        <button-->
  <!--            class="inline-flex hover:text-blue-600 sm:p-2 dark:text-slate-200 dark:hover:text-blue-600"-->
  <!--            @click="sendAiMessage"-->
  <!--        >-->
  <!--          <i class="ri-send-plane-line"></i>-->
  <!--          <span class="sr-only">Send message</span>-->
  <!--        </button>-->
  <!--      </div>-->
  <!--      <div>-->
  <!--        <button-->
  <!--            class="inline-flex hover:text-blue-300 sm:p-2 dark:text-slate-200 dark:hover:text-blue-600"-->
  <!--            @click="cancelAiMessage"-->
  <!--        >-->
  <!--          <i class="ri-close-circle-line"></i>-->
  <!--        </button>-->
  <!--      </div>-->
  <!--    </div>-->
  <!--  </div>-->


  <!--  <dialog ref="analyseDialog" class="modal">-->
  <!--    <div class="modal-box">-->
  <!--      <form method="dialog">-->
  <!--        <button-->
  <!--            class="btm-circle btn btn-ghost btn-sm absolute right-2 top-2"-->
  <!--            @click="closeAnalyse"-->
  <!--        >-->
  <!--          <i class="ri-close-line"></i>-->
  <!--        </button>-->
  <!--      </form>-->
  <!--      <h3 class="alidongfang text-lg font-bold">AI评价</h3>-->
  <!--      <div ref="analyseChat" class="opposans py-4"></div>-->
  <!--    </div>-->
  <!--  </dialog>-->


  <!--  <dialog ref="resultDialog" class="modal">-->
  <!--    <div class="modal-box">-->
  <!--      <form method="dialog">-->
  <!--        <button-->
  <!--            class="btm-circle btn btn-ghost btn-sm absolute right-2 top-2"-->
  <!--            @click="closeAnswer"-->
  <!--        >-->
  <!--          <i class="ri-close-line"></i>-->
  <!--        </button>-->
  <!--      </form>-->
  <!--      <h3 class="alidongfang text-lg font-bold">AI解析</h3>-->
  <!--      <div class="opposans py-4 break-words whitespace-break-spaces">{{ answer }}</div>-->
  <!--      <form class="top-2 flex justify-end">-->
  <!--        <button class="opposans btn" @click.prevent="clipAnswer">-->
  <!--          <i class="ri-clipboard-line"></i>复制-->
  <!--        </button>-->
  <!--      </form>-->
  <!--    </div>-->
  <!--  </dialog>-->


  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <div class="flex flex-col">
      <h1 class="opposans mt-1 text-[16px] text-[--black-light-color]">题目要求</h1>
      <div class="h-[240px] overflow-y-auto opposans break-words whitespace-break-spaces">
        {{ question }}
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <div class="grid grid-rows-1 grid-cols-2 gap-1">
      <div class="flex flex-col">
        <h1 class="opposans text-[16px] text-[--black-light-color]">答案解析</h1>
        <div class="h-[240px] overflow-y-auto opposans break-words whitespace-break-spaces">
          {{ answer }}
        </div>
      </div>
      <div class="flex flex-col">
        <h1 class="opposans text-[16px] text-[--black-light-color]">评分标准</h1>
        <div class="h-[240px] overflow-y-auto opposans break-words whitespace-break-spaces">
          {{ standard }}
        </div>
      </div>
      <!--      <div class="h-[240px] overflow-y-auto opposans">-->
      <!--        <el-input-->
      <!--            v-model="answerInput"-->
      <!--            :rows="8"-->
      <!--            placeholder="输入您的答案"-->
      <!--            resize="none"-->
      <!--            type="textarea"-->
      <!--        />-->
      <!--      </div>-->
    </div>
    <div class="divider mt-1 mb-1"></div>
    <div class="flex flex-row justify-center w-full">
      <el-button class="opposans w-1/4 " plain type="primary" @click="exportWord">导出word</el-button>
    </div>
    <!--    <el-button-group class="ml-auto mr-auto">-->
    <!--      <el-button plain type="success" @click="chatOpen">AI交流</el-button>-->
    <!--      <el-button plain type="primary" @click="sendAnswer">提交答案</el-button>-->
    <!--      <el-button plain type="primary" @click="viewAnswer">查看解析</el-button>-->
    <!--    </el-button-group>-->
  </div>
</template>

<style scoped>

</style>