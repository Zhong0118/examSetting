<script lang="ts" setup>
import {RouterLink, useRouter} from "vue-router";
import {onMounted, onUnmounted, ref} from "vue";

const router = useRouter();

function toHome() {
  router.push({
    name: "index",
  });
}

const isSticky = ref(false);

function handleScroll() {
  const scrollTop =
      window.pageYOffset ||
      document.documentElement.scrollTop ||
      document.body.scrollTop ||
      0;
  isSticky.value = scrollTop > 0;
}

// 监听滚动事件
onMounted(() => {
  window.addEventListener("scroll", handleScroll);
});

// 卸载组件时移除滚动事件监听
onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll);
});

const props = defineProps({
  sections: Object,
});
</script>

<template>
  <div
      :class="{
      'bg-sky-100': !isSticky,
      'bg-slate-50': isSticky,
      'drop-shadow-md': isSticky,
    }"
      class="navbar fixed pl-[5%] pr-[5%] z-10"
  >
    <div class="navbar-start">
      <button
          class="playwrite-it-moderna btn btn-ghost text-xl"
          @click="toHome"
      >
        <span class="title-icon"></span> BU-Exam
      </button>
    </div>
    <div class="navbar-center lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li v-for="(section, index) in sections" :key="index" class="mr-2">
          <a :href="'#' + index">
            {{ section }}
          </a>
        </li>
      </ul>
    </div>
    <div class="navbar-end">
      <RouterLink class="btn btn-outline btn-secondary" to="/login"
      >登录/注册
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.title-icon {
  width: 30px;
  height: 30px;
  background-image: url("../../public/title.svg"); /* 设置背景图像 */
  background-repeat: no-repeat; /* 背景图像不重复 */
  background-size: cover; /* 背景图像覆盖整个元素 */
}

ul li a {
  font-family: OPPOSans, sans-serif;
  font-size: 16px;
}

</style>