<script setup lang="ts">
import { ref } from "vue";
// @ts-ignore
import loginRigForForm from "./loginRigForForm.vue";
// @ts-ignore
import showPassword from "./showPassword.vue";
// import { useAuth } from "@/hooks/useAuth.js";
import Swal from "sweetalert2";

const formType = "register";
const title = "欢迎";
const subtitle = "你需要使用你的邮箱进行注册";
const buttonText = "注册";

const email = ref("");
const isVisible = ref(false); // 初始状态，密码不可见

const handleVisibilityChange = (newValue : boolean) => {
  isVisible.value = newValue;
};
// const { requestAuth, checkWhole } = useAuth();
//
// function registerIn(username : string, password : string) {
//   const e = email.value;
//   const info = { a: username, b: password, c: e };
//   if (checkWhole(info)) {
//     const config = {
//       method: "POST",
//       url: "/api/register",
//       data: { username, password, e },
//     };
//     requestAuth(config, "注册成功", "注册失败");
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
    @get-info="registerIn"
  >
    <label class="input-container form-control relative w-full">
      <div class="label">
        <span class="label-text text-xl text-[var(--login4)]">邮箱</span>
      </div>
      <div>
        <i
          class="pi pi-envelope absolute left-2.5 top-1/2 translate-y-[80%] text-[20px] opacity-70"
        ></i>
        <input
          v-model="email"
          class="input w-full grow pl-10"
          placeholder="Email"
          type="email"
        />
      </div>
    </label>
    <show-password @update:visible="handleVisibilityChange"></show-password>
  </loginRigForForm>
</template>

<style scoped></style>
