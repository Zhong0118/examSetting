<script lang="ts" setup>
import {onMounted, onUnmounted, ref} from "vue";
import {ElLoading, ElMessage, ElMessageBox, type UploadFile} from "element-plus";
import Swal from "sweetalert2";
// @ts-ignore
import emitter from "@/utils/mitter";

const libDialog = ref(false);

const libList = ref<UploadFile[]>([]);
const showLoading = () => {
  ElLoading.service({
    lock: true,
    text: "导出中，请稍候...",
    background: "rgba(0, 0, 0, 0.7)",
  });
};
const libUpload = () => {
  libDialog.value = true;
};

const libBeforeRemove = (file: UploadFile, libList: UploadFile[]) => {
  return new Promise((resolve, reject) => {
    ElMessageBox.confirm("此操作将删除该文件, 是否继续?", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    })
        .then(() => {
          resolve(true);
        })
        .catch(() => {
          reject(false);
        });
  });
};

// 删除文件时的逻辑
const libHandleRemove = (file: UploadFile, fileList: UploadFile[]) => {
  const index = libList.value.findIndex((f) => f.uid === file.uid);
  if (index !== -1) {
    libList.value.splice(index, 1);
  }
};

const libHandleSuccess = (file: UploadFile, libList: UploadFile[]) => {
  ElMessage({message: "文件上传成功", type: "success"});
};

const loading = ref(false);

const doLib = async () => {
  if (!libList.value.length) {
    await Swal.fire({
      text: "请选择文件",
      icon: "info",
      toast: true,
      position: "top",
      timer: 2000,
      timerProgressBar: true,
    });
    return;
  } // 如果没有文件，不执行上传
  const loadingInstance = ElLoading.service({
    lock: true,
    text: "上传中，请稍候...",
    background: "rgba(0, 0, 0, 0.7)",
  });
  loading.value = true;
  let formData = new FormData();
  libList.value.map((file) => {
    formData.append("files", file.raw!);
  });
  const response = await fetch("http://localhost:5000/api/postlib", {
    method: "POST",
    body: formData,
  });

  if (response.status === 200) {
    await Swal.fire({
      text: "上传成功",
      icon: "success",
      toast: true,
      position: "top",
      timer: 2000,
      timerProgressBar: true,
    });
    loading.value = false;
    loadingInstance.close();
  } else {
    await Swal.fire({
      text: "上传失败",
      icon: "error",
      toast: true,
      position: "top",
      timer: 2000,
      timerProgressBar: true,
    });
    loading.value = false;
    loadingInstance.close();
  }
};

onMounted(() => {
  emitter.on("upload-show", libUpload);
})

onUnmounted(() => {
  emitter.off("upload-show", libUpload);
})


</script>

<template>
  <div
      v-show="libDialog"
      class="fixed left-1/2 top-1/4 h-[450px] w-[600px] -translate-x-1/2 rounded-[8px] bg-[--panel2-color] z-10"
  >
    <div class="flex flex-row justify-between p-2">
      <h3 class="alidongfang text-[24px] font-bold">选择文件</h3>
      <button
          class="btn btn-circle btn-ghost btn-sm"
          @click="libDialog = false"
      >
        <i class="ri-close-line text-[24px]"></i>
      </button>
    </div>
    <el-upload
        :auto-upload="false"
        :before-remove="libBeforeRemove"
        :file-list="libList"
        :on-progress="showLoading"
        :on-remove="libHandleRemove"
        :on-success="libHandleSuccess"
        accept=".pdf,.doc,.docx,.jpg,.png,.jpeg"
        action="#"
        multiple
    >
      <template #trigger>
        <button class="opposans btn btn-secondary btn-sm m-2">
          <i class="ri-add-box-line"></i>添加
        </button>
      </template>
      <button class="opposans btn btn-primary btn-sm m-2" @click="doLib">
        <i class="ri-upload-line"></i>上传
      </button>
    </el-upload>
  </div>
</template>

<style scoped>

</style>