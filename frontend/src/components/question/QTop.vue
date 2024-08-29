<script lang="ts" setup>
import {onMounted, ref} from 'vue'
import {CircleCheck, CircleClose, Upload, Warning} from "@element-plus/icons-vue";
// @ts-ignore
import emitter from "@/utils/mitter.js";

import {buoptions, options, topics} from '@/utils/objects'
import DocUpload from "@/components/question/DocUpload.vue";
import {useQuestionStore} from "@/stores/question";

const questionStore = useQuestionStore()
const target = ref([])
const type = ref('')
// const type = ref([])
// collapse-tags
// collapse-tags-tooltip
// multiple
const types = [
  {
    value: topics[0],
    label: topics[0],
  },
  {
    value: topics[1],
    label: topics[1],
  },
  {
    value: topics[2],
    label: topics[2],
  },
  {
    value: topics[3],
    label: topics[3],
  },
  {
    value: topics[4],
    label: topics[4],
  },
]

// 题目类型
const p = {
  expandTrigger: 'hover' as const,
}

// 难度等级
const difficult = ref(0)
const colors = ref(['#88D66C', '#F7BA2A', '#FF4C4C'])
const icons = [CircleCheck, Warning, CircleClose]
const uploadShow = () => {
  emitter.emit('upload-show')
}
onMounted(() => {
// @ts-ignore
  questionStore.setQuestion({target, type, difficult})
})

</script>

<template>
  <DocUpload/>
  <div class="grid grid-rows-1 grid-cols-4 pl-1 pr-1">
    <div class="pt-2">
      <span class="mt-1 text-[14px] text-[--black-light-color]">目标科目:</span>
      <el-cascader
          v-model="target"
          :options="buoptions"
          :props="p"
          class="w-[90%]"
          placeholder="目标"
      />
    </div>
    <div class="pt-2">
      <span class="mt-1 text-[14px] text-[--black-light-color]">题目类型:</span>
      <el-select
          v-model="type"
          placeholder="类型"
          style="width: 90%"
      >
        <el-option
            v-for="item in types"
            :key="item.value"
            :label="item.label"
            :value="item.value"
        />
      </el-select>
    </div>
    <div class="pt-2">
      <span class="mt-1 text-[14px] text-[--black-light-color]">题目困难等级:</span>
      <el-rate v-model="difficult" :colors="colors"
               :icons="icons"
               :texts="['入门', '简单', '一般', '困难', '地狱']"
               :void-icon="CircleCheck"
               show-text/>
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
</template>

<style scoped>

</style>