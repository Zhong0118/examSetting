<script setup>

import Heading from "@/components/Heading.vue";
import WholePage from "@/components/WholePage.vue";
</script>

<template>
  <div class="w-full h-[100dvh] bg flex flex-col">
    <Heading/>
    <div class="mr-[1%] ml-[1%] mt-[5%] h-[88dvh] grid grid-rows-1 grid-cols-2 gap-4">
      <WholePage/>
    </div>
  </div>
</template>

<style scoped>
.bg {
  position: relative;
  background-image: url("../assets/images/bg.svg");
  background-repeat: repeat;
  background-position: top;
  background-attachment: fixed;
}


</style>