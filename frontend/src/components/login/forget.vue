<script setup lang="ts">
import { ref } from "vue";
// @ts-ignore
import showPassword from "@/components/login/showPassword.vue";
// import { useUserStore } from "@/store/user";
// import { useAuth } from "@/hooks/useAuth";
import Swal from "sweetalert2";

const username = ref("");
const password = ref("");
const email = ref("");
const isVisible = ref(false);
const handleVisibilityChange = (newValue : boolean) => {
  isVisible.value = newValue;
};
const title = "忘记密码";
const subtitle = "输入对应的用户名和邮箱进行密码重置";
const buttonText = "确认";

// const userStore = useUserStore();
// const { requestAuth, checkWhole } = useAuth();
//
// function resetPassword(username : string, password : string, email : string) {
//   const info = { a: username, b: password, c: email };
//   if (checkWhole(info)) {
//     const config = {
//       method: "POST",
//       url: "/api/forget",
//       data: { username, password, email },
//     };
//     requestAuth(config, "重置成功", "重置失败");
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
  <div class="wholeForm">
    <div class="form-title">
      <h1 class="alidaoli mb-2.5 text-5xl font-bold">{{ title }}</h1>
      <h4 class="alidaoli">{{ subtitle }}</h4>
    </div>
    <!--    absolute left-2.5 top-1/2 h-5 w-5 translate-y-1/2 opacity-70-->
    <div class="form mt-4">
      <label class="input-container form-control relative w-full">
        <div class="label">
          <span class="label-text text-xl" style="color: var(--login4)"
            >用户名</span
          >
        </div>
        <div>
          <i
            class="pi pi-user absolute left-2.5 top-1/2 translate-y-[80%] text-[20px] opacity-70"
          ></i>
          <input
            v-model="username"
            class="input w-full pl-10"
            placeholder="Username"
            type="text"
          />
        </div>
      </label>
      <label class="input-container form-control relative w-full">
        <div class="label">
          <span class="label-text text-xl" style="color: var(--login4)"
            >邮箱</span
          >
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
      <label class="input-container form-control relative w-full">
        <div class="label">
          <span class="label-text text-xl" style="color: var(--login4)"
            >新密码</span
          >
        </div>
        <div>
          <i
            class="pi pi-key absolute left-2.5 top-1/2 translate-y-[80%] text-[20px] opacity-70"
          ></i>
          <input
            v-model="password"
            :type="isVisible ? 'text' : 'password'"
            class="input w-full pl-10"
            placeholder="Password"
          />
        </div>
      </label>
      <show-password @update:visible="handleVisibilityChange"></show-password>
      <button
        class="alidongfang btn btn-primary btn-wide mt-6 font-bold"
        style="font-size: 20px"
        @click="resetPassword(username, password, email)"
      >
        {{ buttonText }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.wholeForm {
  width: 70%;
  top: 18%;
  position: absolute;
}
</style>
