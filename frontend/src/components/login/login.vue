<script setup lang="ts">
import { defineEmits, ref } from "vue";
import loginRigForForm from "@/components/login/loginRigForForm.vue";
import showPassword from "@/components/login/showPassword.vue";
// import { useAuth } from "@/hooks/useAuth.js";
import Swal from "sweetalert2";

const formType = "login";
const title = "你好";
const subtitle = "请输入你的用户名和密码";
const buttonText = "登录";

const isVisible = ref(false); // 初始状态，密码不可见

const handleVisibilityChange = (newValue : boolean) => {
  isVisible.value = newValue;
};

const emit = defineEmits(["toForgetForm"]);
const onForgetPasswordClick = () => {
  emit("toForgetForm", "forget-pwd");
};

// const { requestAuth, checkWhole } = useAuth();
//
// function loginIn(username : string, password : string) {
//   const info = { a: username, b: password };
//   if (checkWhole(info)) {
//     const config = {
//       method: "POST",
//       url: "/api/login",
//       data: { username, password },
//     };
//     requestAuth(config, "登陆成功", "登录失败");
//   } else {
//     Swal.fire({
//       title: "请填写所有输入项",
//       icon: "error",
//       confirmButtonText: "关闭",
//       timer: 5000,
//       timerProgressBar: true,
//     });
//   }
// }
</script>
<template>
  <loginRigForForm
    :button-text="buttonText"
    :form-type="formType"
    :is-visible="isVisible"
    :subtitle="subtitle"
    :title="title"
    @get-info="loginIn"
  >
    <show-password @update:visible="handleVisibilityChange">
      <span class="forget-pwd-btn cursor-pointer" @click="onForgetPasswordClick"
        >忘记密码？</span
      >
    </show-password>
  </loginRigForForm>
</template>

<style scoped></style>
