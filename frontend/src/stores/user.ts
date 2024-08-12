import {defineStore} from "pinia";
import {ref} from "vue";

type User = {
    uid: string;
    username: string;
};
export const useUserStore = defineStore(
    "user",
    () => {
        // 用户信息
        const user = ref<User>();
        // 设置用户，登录后使用
        const setUser = (u: User) => {
            user.value = u;
        };
        // 清空用户，退出后使用
        const delUser = () => {
            user.value = void 0;
        };
        return {user, setUser, delUser};
    },
);
