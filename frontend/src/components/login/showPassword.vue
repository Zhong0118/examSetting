<script setup>
import { ref, watch } from "vue";

const isVisible = ref(false);
const emit = defineEmits(["update:visible"]);
watch(isVisible, (newValue) => {
  emit("update:visible", newValue);
});
</script>

<template>
  <div class="other-select mt-2 flex justify-between">
    <div class="rem-pwd">
      <input id="check" v-model="isVisible" type="checkbox" />
      <label class="misans rem-pwd-tips cursor-pointer" for="check">
        {{ isVisible ? "隐藏" : "展示" }}密码</label
      >
    </div>
    <slot></slot>
  </div>
</template>

<style scoped>
.other-select {
  color: var(--login1);
}

.other-select #check:checked + .rem-pwd-tips {
  color: var(--title-icon-color);
}

.other-select input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  position: relative;
  border: 0;
}

.other-select input[type="checkbox"]::after {
  position: absolute;
  top: 0;
  color: #000;
  width: 20px;
  height: 20px;
  display: inline-block;
  visibility: visible;
  padding-left: 0;
  text-align: center;
  background-color: var(--login2);
  content: " ";
}

.other-select input[type="checkbox"]:checked::after {
  content: "√";
  color: var(--login3);
  font-size: 30px;
  line-height: 20px;
  background-color: var(--login2);
  border: 1px solid var(--login3);
  border-radius: 5px;
}
</style>