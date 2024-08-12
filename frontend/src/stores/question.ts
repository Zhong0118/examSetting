import {defineStore} from "pinia";
import {ref} from "vue";

type Question = {
    target: Array<string>,
    type: string,
    difficult: number
};
export const useQuestionStore = defineStore(
    "question",
    () => {
        // 用户信息
        const question = ref<Question>();
        // 设置用户，登录后使用
        const setQuestion = (q: Question) => {
            question.value = q;
        };
        // 清空用户，退出后使用
        const delQuestion = () => {
            question.value = void 0;
        };
        return {question, setQuestion, delQuestion};
    },
);
