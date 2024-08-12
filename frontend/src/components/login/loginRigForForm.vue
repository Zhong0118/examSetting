<script setup>
import { defineEmits, defineProps, ref } from "vue";
const username = ref("");
const password = ref("");
const props = defineProps({
  formType: String,
  title: String,
  subtitle: String,
  buttonText: String,
  isVisible: Boolean,
});

const emit = defineEmits(["get-info"]);
const returnInfo = () => {
  emit("get-info", username.value, password.value);
};
</script>

<template>
  <div :class="{ formType }" class="wholeForm">
    <div class="form-title">
      <h1 class="alidaoli mb-[10px] text-5xl font-bold">{{ title }}</h1>
      <h4 class="alidaoli">{{ subtitle }}</h4>
    </div>
    <div class="form mt-4">
      <label class="input-container form-control relative w-full">
        <div class="label">
          <span class="label-text text-xl text-[--login4]">用户名</span>
        </div>
        <div>
          <i class="pi pi-user absolute left-2.5 top-1/2 translate-y-[80%] text-[20px] opacity-70"></i>
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
          <span class="label-text text-xl text-[--login4]">密码</span>
        </div>
        <div>
          <i class="pi pi-key absolute left-2.5 top-1/2 translate-y-[80%] text-[20px] opacity-70"></i>
          <input
            v-model="password"
            :type="isVisible ? 'text' : 'password'"
            class="input w-full pl-10"
            placeholder="Password"
          />
        </div>
      </label>

      <slot />
      <button
        class="alidongfang btn btn-primary btn-wide mt-6 font-bold"
        style="font-size: 20px"
        @click.prevent="returnInfo()"
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
