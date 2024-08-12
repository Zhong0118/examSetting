// useAuth.js
import http from "@/utils/requests";
import Swal from "sweetalert2";
import { useUserStore } from "@/store/user";

const userStore = useUserStore();

export function useAuth() {
  async function requestAuth(config, successMessage, failMessage) {
    try {
      const response = await http.request(config);
      if (response.status === 200) {
        Swal.fire({
          text: successMessage,
          toast: true,
          position: "top",
          icon: "success",
          showConfirmButton: false,
          timer: 1000,
        }).then(() => {
          // 假设 _id 是数字类型并且可以直接使用
          const user = {
            uid: response.data.user._id,
            username: response.data.user.username,
            avatar: response.data.user.avatar,
            vip: response.data.user.vip,
          };
          userStore.setUser(user); // 存储用户信息
          window.location.href = "/editor"; // 跳转到编辑界面
        });
      } else {
        const errorMessage = response.data.message || "未知错误";
        await Swal.fire({
          title: failMessage,
          icon: "error",
          text: errorMessage,
          confirmButtonText: "关闭",
          timer: 5000,
          timerProgressBar: true,
        });
      }
    } catch (error) {
      // 这里处理请求过程中可能发生的错误
      let errorMessage = "未知错误";
      if (error.response) {
        // 服务器返回了响应，但状态码不是 2xx
        errorMessage = error.response.data.message || errorMessage;
      } else if (error.request) {
        // 请求已发出但没有收到响应
        errorMessage = "请求无法发出，请检查您的网络连接。";
      } else {
        // 发生了触发请求错误的问题
        errorMessage = error.message;
      }
      await Swal.fire({
        title: "登录失败",
        icon: "error",
        text: errorMessage,
        confirmButtonText: "关闭",
        timer: 5000,
        timerProgressBar: true,
      });
    }
  }

  function checkWhole(obj) {
    // 遍历对象的所有属性
    for (const key in obj) {
      // 检查当前属性值是否为空
      if (obj[key] === null || obj[key] === undefined || obj[key] === "") {
        // 如果发现空值，返回 false
        return false;
      }
    }
    // 如果所有属性值都非空，返回 true
    return true;
  }

  return {
    requestAuth,
    checkWhole,
  };
}
