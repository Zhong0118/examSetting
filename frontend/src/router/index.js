import {createRouter, createWebHistory} from "vue-router";
import NProgress from "nprogress"; // 导入 nprogress
import "nprogress/nprogress.css";

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: "/",
            redirect: "/index",
        },
        {
            path: "/index",
            name: "index",
            component: () => import("@/views/WholeExamPage.vue"),
            meta: {
                title: "BU-Exam | 新时代AI出题助手", // 定义标题
            },
        },
        {
            path: "/login",
            name: "login",
            component: () => import("@/views/LoginPage.vue"),
            meta: {
                title: "BU-Exam | 登陆注册", // 定义标题
            },
        },
        {
            path: "/index2",
            name: "index2",
            component: () => import("@/views/SingleExamPage.vue"),
            meta: {
                title: "BU-Exam | 新时代AI出题助手", // 定义标题
            },
        },

    ],
});
NProgress.configure({
    easing: "ease", // 动画方式
    speed: 1000, // 递增进度条的速度
    showSpinner: false, // 是否显示加载ico
    trickleSpeed: 200, // 自动递增间隔
    minimum: 0.3, // 更改启动时使用的最小百分比
    parent: "body", //指定进度条的父容器
});

router.beforeEach((pre, next) => {
    NProgress.start(); // 开启进度条
});
router.afterEach(() => {
    NProgress.done(); // 结束进度条
});
router.afterEach((to) => {
    document.title = to.meta.title || "editor";
});

export default router;
