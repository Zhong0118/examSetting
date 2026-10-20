# ExamHub 前端

Vue 3、TypeScript 与 Vite 构建的学习工作台，包含题库浏览、题集编辑、练习记录、PDF 阅读、教学教练和评测界面。完整产品说明、模型配置与分享边界见[项目 README](../README.md)。

## 本地开发

需要 Node.js 22.19+ 与 pnpm 11+。先按[后端启动说明](../README.md#本地运行)运行 Flask，默认地址为 `http://127.0.0.1:5000`。从仓库根目录执行：

```sh
cd frontend
pnpm install --frozen-lockfile
pnpm dev --host 127.0.0.1
```

打开 Vite 输出的地址，通常是 `http://127.0.0.1:5173`。无需 Key 即可用访客身份体验原创示例、手工编辑和规则教练。

[vite.config.ts](vite.config.ts) 将 `/api` 代理到 Flask；所有请求通过 [src/lib/api.ts](src/lib/api.ts) 使用同源 cookie，写请求携带 `X-Requested-With: ExamHub` 和当前身份校验头。修改后端端口需同步代理配置。模型 Key 在设置页提交给后端后清空输入，不放入前端构建变量或浏览器持久化存储。

## 开发入口

| 位置 | 职责 |
| --- | --- |
| [src/App.vue](src/App.vue)、[src/router/index.ts](src/router/index.ts) | 应用外壳与页面路由 |
| [src/views/CollectionView.vue](src/views/CollectionView.vue) | 工作台 `/`、我的题库 `/library`、发现题集 `/discover` |
| [src/views/DetailView.vue](src/views/DetailView.vue)、[src/views/EditorView.vue](src/views/EditorView.vue) | 题目浏览、筛选、目录与编辑 |
| [src/views/PracticeView.vue](src/views/PracticeView.vue)、[src/views/HistoryView.vue](src/views/HistoryView.vue) | 练习提交、草稿与历史结果 |
| [src/views/DocumentReaderView.vue](src/views/DocumentReaderView.vue)、[src/lib/pdf.ts](src/lib/pdf.ts) | 私有教材阅读、页范围与本地 PDF.js 资源 |
| [src/views/TutorSessionView.vue](src/views/TutorSessionView.vue)、[src/components/TutorLiveEvaluation.vue](src/components/TutorLiveEvaluation.vue) | 教学会话、工具轨迹与真实评测界面 |
| [src/lib/](src/lib/)、[src/components/](src/components/) | API、身份状态、草稿和请求恢复逻辑，以及共享组件 |
| [src/assets/main.css](src/assets/main.css) | 布局、样式和过渡动画 |

题集列表使用服务端分页，每页 12 份，并按工作台、我的、收藏与公开范围校验访问，结合搜索和主题筛选。题目详情与编辑器每页 10 题，编辑器只展开当前题，保存前验证全题集；单题集最多 100 题。

## 测试与构建

以下命令在 `frontend/` 下执行：

```sh
pnpm test        # Node 内置测试：状态、请求恢复、身份边界与部分 Vue 渲染
pnpm type-check  # vue-tsc 类型检查
pnpm build       # 并行执行类型检查与 Vite 生产构建
```

[tests/](tests/) 使用现有 Vue、TypeScript 和 Node 测试设施，通过 API 替身验证交互与状态，无需启动后端或调用真实模型。构建产物位于 `dist/`；PDF.js worker、字体、CMap、WASM 与许可证随产物本地打包。

`pnpm preview` 仅预览静态构建，本项目只为开发服务器配置了 `/api` 代理。完整联调使用 `pnpm dev`；部署时需提供同源 `/api` 反向代理和 Vue Router 页面路由回退。CI 运行 `pnpm test` 与 `pnpm build`，测试数量以当次输出为准。

教学工具与持久化边界见[架构说明](../docs/architecture/teaching-agent.md)；已提交模型轨迹可按[离线复现命令](../README.md#测试与离线复现)核对，界面中启动真实模型评测会产生供应商调用。
