import {defineStore} from "pinia";
import {ref} from "vue";

type Title = {
    question: string,
    answer: string,
    standard: string,
};
export const useTitleStore = defineStore(
    "title",
    () => {
        const title = ref<Title>();
        const setTitle = (q: Title) => {
            title.value = q;
        };
        const delTitle = () => {
            title.value = void 0;
        };
        return {title, setTitle, delTitle};
    },
);
