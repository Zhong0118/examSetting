<script lang="ts" setup>
import {computed, ref} from "vue";
import {ElMessage, ElMessageBox} from "element-plus";
// @ts-ignore
import emitter from "@/utils/mitter";
// @ts-ignore
import router from "@/router";
import {buoptions} from "@/utils/objects";
import {Upload} from "@element-plus/icons-vue";
import DocUpload from "@/components/question/DocUpload.vue";
import {marked} from "marked";
import dayjs from "dayjs";
import * as docx from "docx";
import {Paragraph} from "docx";

const target = ref([]);

const num1 = ref(0)
const num2 = ref(0)
const num3 = ref(0)
const num4 = ref(0)
const num5 = ref(0)
const num6 = ref(0)

const questionNeed = ref('')
const examTitles = ref();

const randomRequire = async () => {
  if (target.value.length === 0) {
    ElMessage({
      message: '请选择需要的科目',
      type: 'warning',
    })
    return
  }
  const response = await fetch("http://localhost:5000/api/requirement2", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      target: target.value,
      num1: num1.value,
      num2: num2.value,
      num3: num3.value,
      num4: num4.value,
      num5: num5.value,
      num6: num6.value,
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

const continue_ = ref(false)
const times = ref(0)

const wholeNum = computed(() => {
  return num1.value + num2.value + num3.value + num4.value + num5.value + num6.value;
})

const createTopic = async () => {
  if (target.value.length === 0 || (wholeNum.value === 0)) {
    ElMessage({
      message: '请选择需要的科目和题目数量',
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
  try {
    let textData = [];
    for (let child of examTitles.value.children) {
      textData.push(child.textContent);
    }
    const textContent = textData.join('\n');
    const response = await fetch("http://localhost:5000/api/whole", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        target: target.value,
        questionNeed: questionNeed.value,
        num1: num1.value,
        num2: num2.value,
        num3: num3.value,
        num4: num4.value,
        num5: num5.value,
        num6: num6.value,
        existing: textContent,
      }),
    });
    if (times.value === 0) {
      continue_.value = true;
      times.value += 1;
    } else if (times.value === 5) {
      continue_.value = false;
      times.value = 0;
      ElMessage({
        message: '生成题目次数过多，请稍后继续',
        type: 'info',
      })
    }
    if (!continue_) {
      examTitles.value.innerHTML = '';
    }
    generating.value = true;
    const aiBP = document.createElement("p");
    examTitles.value.appendChild(aiBP);
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
    generating.value = false;
    ElMessage({
      message: '本轮题目生成完毕',
      type: 'success',
    })
  } catch (e) {
    ElMessage({
      message: '生成题目失败',
      type: 'error',
    })
  }
}

const clearAll = () => {
  examTitles.value.innerHTML = '';
  times.value = 0;
  continue_.value = false;
}

function exportWord() {
  ElMessageBox.prompt('请输入您的文件名', '文件名', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    inputPattern:
        /^(?!\s*$).+/,
    inputErrorMessage: '无效输入',
  }).then(({value}) => {
    try {
      const fileName2 = dayjs().format('YYYYMMDDHHmmss');
      const fileName = value + fileName2 + '.docx';
      const fullText = examTitles.value.innerText;
      const doc = new docx.Document({
        //文档作者，显示在文档属性中
        creator: "BUPT_AI",
        title: fileName,
        description: 'AI出题，仅供参考',
        sections: [
          {
            properties: {},
            //主体内容
            children: fullText.split('\n').map((t: string) => {
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
    } catch (error) {
      ElMessage({
        type: 'info',
        message: '导出失败',
      })
    }

  }).catch(() => {
    ElMessage({
      type: 'info',
      message: '取消导出',
    })
  })
}

const p = {
  expandTrigger: 'hover' as const,
  multiple: true
}
const uploadShow = () => {
  emitter.emit('upload-show')
}

const generating = ref(false);

function toSingle() {
  router.push({
    name: "index2",
  })
}
</script>

<template>
  <DocUpload/>
  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <div class="grid grid-rows-1 grid-cols-2 pl-1 pr-1">
      <div class="pt-2">
        <span class="mt-1 text-[14px] text-[--black-light-color]">目标科目:</span>
        <el-cascader
            v-model="target"
            :options="buoptions"
            :props="p"
            class="w-[90%]"
            collapse-tags
            collapse-tags-tooltip
            placeholder="目标"
        />
      </div>
      <div class="pt-2">
        <span class="mt-1 text-[14px] text-[--black-light-color]">文件参考:</span>
        <br>
        <el-button class="opposans" type="primary" @click="uploadShow">
          <el-icon class="el-icon--left">
            <Upload/>
          </el-icon>
          选择文件
        </el-button>
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <el-input
        v-model="questionNeed"
        :rows="16"
        placeholder="输入您的具体需求"
        resize="none"
        type="textarea"
    />
    <div>
      <p class="text-[14px] text-[--black-light-color] mt-1">题目类型需求及数量</p>
      <div class="grid grid-cols-3 grid-rows-2 pl-1 pr-1 gap-1">
        <div class="pt-2">
          <span class="mt-1 text-[13px] text-[--black-light-color] opposans">单选题</span>
          <el-input-number v-model="num1" :max="10" :min="0" class="mx-4"/>
        </div>
        <div class="pt-2">
          <span class="mt-1 text-[13px] text-[--black-light-color] opposans">多选题</span>
          <el-input-number v-model="num2" :max="5" :min="0" class="mx-4"/>
        </div>
        <div class="pt-2">
          <span class="mt-1 text-[13px] text-[--black-light-color] opposans">填空题</span>
          <el-input-number v-model="num3" :max="10" :min="0" class="mx-4"/>
        </div>
        <div class="pt-2">
          <span class="mt-1 text-[13px] text-[--black-light-color] opposans">判断题</span>
          <el-input-number v-model="num4" :max="8" :min="0" class="mx-4"/>
        </div>
        <div class="pt-2">
          <span class="mt-1 text-[13px] text-[--black-light-color] opposans">解答题</span>
          <el-input-number v-model="num5" :max="6" :min="0" class="mx-4"/>
        </div>
        <div class="pt-2">
          <span class="mt-1 text-[13px] text-[--basic4] opposans">拔高题</span>
          <el-input-number v-model="num6" :max="2" :min="0" class="mx-4"/>
        </div>
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <div class="flex flex-row justify-center w-full">
      <el-button class="opposans w-1/5 " type="info" @click="randomRequire">生成随机需求</el-button>
      <el-button class="opposans w-1/5 " type="success" @click="createTopic">提交任务需求</el-button>
      <el-button class="opposans w-1/5 " type="warning" @click="toSingle">切换到单题</el-button>
    </div>
  </div>

  <div class="card bg-[--panel-color] shadow-2xl pl-2 pr-2">
    <div class="flex flex-col">
      <h1 class="opposans mt-1 text-[16px] text-[--black-light-color]">试题</h1>
      <div class="divider mt-1 mb-1"></div>
      <div class="h-4">
        <el-progress
            v-show="generating"
            :duration="2"
            :indeterminate="true"
            :percentage="30"
            class="w-full"
            status="success"
        />
      </div>
      <div ref="examTitles" class="h-[500px] overflow-y-auto opposans">
      </div>
    </div>
    <div class="divider mt-1 mb-1"></div>
    <el-button-group class="ml-auto mr-auto">
      <el-button v-if="continue_" class="opposans" type="info" @click="createTopic">
        <div class="flex flex-row gap-1">
          <i class="ri-arrow-right-double-fill"></i>
          <span>继续生成</span>
        </div>
      </el-button>
      <el-button class="opposans mr-auto ml-auto " type="primary" @click="exportWord">导出word</el-button>
      <el-button class="opposans mr-auto ml-auto " type="primary" @click="clearAll">一键清空</el-button>
    </el-button-group>
  </div>
</template>

<style scoped>
</style>