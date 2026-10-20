# ExamHub 开源对照调研

核验日期：2026-10-20。ExamHub 是用户暂定项目名，不对应任何被检索到的同名产品。

## 范围与结论

只研究开源实现，选择 3 个各有用途的对照：**Quizfreely 最贴近共享学习集社区；Quizzle 适合参考轻量发布与练习链路；Exameow 适合参考 AI 出题、题库组卷和在线考试。** 不建议整站照搬，没有证据表明其中任何一个已经完整覆盖“人人出题—长期共享题库—个人答案档案—AI 自主教学”。

方法：检索发现候选后，核验作者 README、LICENSE、GitHub 提交记录，并下载或直接读取相关源码。以下“已实现”指存在对应实现证据，**没有部署、端到端实测、压力测试或教学效果验证**。GitHub REST API 返回限流，维护日期改由 GitHub 官方 commits Atom 获取；日期按 UTC。近期提交仅作为维护信号，不等于质量或安全保证。本项调研未修改业务源码。

## 1. Quizfreely：共享学习集与个人学习进度，优先对照

- **身份与技术栈**：作者组织 `quizfreely`；[前端 README](https://github.com/quizfreely/quizfreely/blob/main/README.md) 明确为 SvelteKit/Node.js，另有 Go GraphQL [后端仓库](https://github.com/quizfreely/api)。[官网](https://quizfreely.org/)明确提供闪卡、练习测试和单词条学习统计。
- **创建与发布**：编辑器实际调用 `updateStudyset(..., draft: false)`，同时提交 `private` 设置和词条增删改；不是只有展示页面。[编辑器源码](https://github.com/quizfreely/quizfreely/blob/5dccec343501c1ddd8dcfa4e76bc66ffef2bc6fc/src/lib/Edit.svelte#L729)
- **发现与做别人题**：搜索页调用 `searchStudysets`，返回作者、学习集、词条数量，并支持分页；学习集有练习测试路由。[搜索源码](https://github.com/quizfreely/quizfreely/blob/5dccec343501c1ddd8dcfa4e76bc66ffef2bc6fc/src/routes/search/%2Bpage.js#L14)、[学习集练习入口](https://github.com/quizfreely/quizfreely/blob/main/src/routes/studysets/%5Bid%5D/practice-test/%2Bpage.js)
- **个人记录**：统计页处理词条正误次数、正确率及本地/云端进度，官网也明确描述易混淆词条分析。应称“学习进度与统计”，不能直接写成已核验的任意题型、逐次原始答案永久档案。[统计实现](https://github.com/quizfreely/quizfreely/blob/5dccec343501c1ddd8dcfa4e76bc66ffef2bc6fc/src/routes/stats/%2Bpage.svelte)
- **许可证**：已读取前后端 LICENSE，均为 AGPL-3.0；借用代码时应按该许可证处理，不能按 MIT 使用。[前端 LICENSE](https://github.com/quizfreely/quizfreely/blob/main/LICENSE)、[后端 LICENSE](https://github.com/quizfreely/api/blob/main/LICENSE)
- **维护信号**：前端最近可见提交 2026-10-13，后端 2026-10-06；有近期界面和 FSRS 相关变动。[前端提交](https://github.com/quizfreely/quizfreely/commit/5dccec343501c1ddd8dcfa4e76bc66ffef2bc6fc)、[后端提交](https://github.com/quizfreely/api/commit/aad4d26786e715d3ad59cd0b3173818145dd78ee)
- **可复用部分（调研判断）**：学习集/词条/作者关系、公私有与草稿状态、公开搜索、练习与统计分离。特别适合研究“内容属于作者，学习记录属于学习者”的边界。
- **局限**：核心对象偏 term/definition 闪卡，不能直接等同于复杂试题库；完整自托管涉及独立后端。未证实具备 LLM 自主教学闭环，也未验证社区审核、题目版本与历史答案绑定等能力。

## 2. gnmyt/Quizzle：轻量发布练习与服务端判分

- **身份**：作者 `gnmyt`，LICENSE 署名 Mathias Wagner。[作者 README](https://github.com/gnmyt/Quizzle/blob/main/README.md)定位学校自托管测验，明确有现场测验和自主练习；它与 `quizzle.ai` 没有已核验的关联。
- **实际功能**：`server/routes/practice.js` 的创建接口要求登录，校验上传试题、生成练习码并落盘。练习获取逻辑剥离正确性信息；提交后服务端判分，以 attempt ID 保存 `userAnswer`、`correctAnswer`、得分和时间戳。[发布、出题交付与记录源码](https://github.com/gnmyt/Quizzle/blob/c93c5e9e0e137171618c51fb82fe5ca04bd92587/server/routes/practice.js)
- **重要边界**：创建练习时写入 **14 天过期时间**；答题记录按练习/attempt 保存，参与者可为匿名名称。不能把它描述为已有长期公共题库和跨题库个人档案。认证路由以初始化、登录为主，另有管理员创建用户；本次没有核验到面向公众自由注册、公开题库发现的完整社区链路。[认证源码](https://github.com/gnmyt/Quizzle/blob/main/server/routes/auth.js)、[管理员路由](https://github.com/gnmyt/Quizzle/blob/main/server/routes/admin.js)
- **许可证**：MIT，已读取实际 LICENSE。[许可证](https://github.com/gnmyt/Quizzle/blob/main/LICENSE)
- **维护信号**：main 最近可见提交为 2026-05-06 的版本号 2.6.3；同日有人类作者的音乐模块、依赖更新。距调研日约五个半月，维护频率弱于另外两项，不能仅凭存在仓库称为持续活跃。[版本提交](https://github.com/gnmyt/Quizzle/commit/c93c5e9e0e137171618c51fb82fe5ca04bd92587)、[作者提交](https://github.com/gnmyt/Quizzle/commit/23c9e13f7ab1acbf270e3d010acab4029eeab9a6)
- **可复用部分（调研判断）**：发布练习码、答题时不提前发答案、逐题判分、提交顺序校验与 attempt 记录结构。它是缩小 MVP 范围的好例子。
- **局限**：文件式持久化和短期课堂会话语义不能直接承担长期多人题库社区；未核验 AI 教学能力。适合借鉴局部链路，不适合作为完整产品直接换皮。

## 3. Exameow（过了喵）：AI 出题与从题库发布考试

- **身份核验**：最终采用作者仓库 [heshengtao/exameow](https://github.com/heshengtao/exameow)。最初搜索命中 `Ailyt/Quiz`，但其 README 的 clone/release 链接指向作者仓库；两者 main 提交进度不同。最终已重新读取作者仓库固定提交的 README、LICENSE、发布服务和练习存储源码，不以搜索命中副本代表上游最新状态。
- **README 声明**：资料导入生成题目、顺序/随机练习、错题、模拟考试、题库导入导出，以及从多个本地题库组卷，分享六位码/链接供别人作答。[作者 README](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/README.md)
- **实现核验**：Rust relay 有 `publish_handler`、`submit_handler`、SQLite 结果写入与成绩查询；发布/参加/结果不是只有营销描述。[发布考试服务](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/packages/server/src/relay.rs)
- **个人记录的边界**：题库与练习 session 使用 localStorage，练习历史按天保存答题总数、正确数和题型计数。在线考试服务定义 `MAX_AGE_MS = 7 天`，清理过期考试和结果；因此“本地练习记录”和“云端长期个人原始答案档案”不能混用。[题库存储](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/src/stores/practice.ts)、[练习历史](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/src/stores/practiceHistory.ts)
- **AI 教学边界**：2026-10-06 有“和 AI 一起学”流式对话模式提交，当前路由确有 `/learn`。这里只核验了提交与路由，未运行对话或评估教学效果；不能推导为已实现掌握度诊断、自动课程规划、教学评测闭环。[功能提交](https://github.com/heshengtao/exameow/commit/0ee5a9378f6074329c9b248e925c526cc4454c3b)、[学习路由](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/src/router/index.ts)
- **许可证**：作者仓库 LICENSE 为 Apache-2.0，已实际读取。[许可证](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/LICENSE)
- **维护信号**：main 最近可见提交 2026-10-06，新增 macOS Intel 发布构建；同日有 v1.6.0 版本提交及学习功能开发。[最近提交](https://github.com/heshengtao/exameow/commit/960edd5718846acb1266e3fc4c56b5e1725714a5)、[版本提交](https://github.com/heshengtao/exameow/commit/80c832b440635c3708e088e8e5e466f41303bcaf)
- **可复用部分（调研判断）**：资料到题目的流程、题型与题库模型、导入映射、模拟考试配置、发布考试与答题数据隔离。
- **局限**：本地优先与短期分享语义，没有核验到全站公开题库搜索、持久作者社区和跨设备个人档案。多端、OCR、录屏等功能会扩大求职项目工作量，不应整包照搬。“本地优先”也不代表调用远程模型时不联网或不向模型服务发送内容。

## 指定线索的处理结果

- **Quizzle / Quizzle AI**：确认 `gnmyt/Quizzle` 开源；[quizzle.ai 官网](https://quizzle.ai/)是另一条同名 AI 测验产品线索。限定检索未找到足以将其归为上述开源项目的作者关联、公开代码及许可证证据，故不合并身份，也不认定它绝对没有开源代码。
- **OpnForm**：确实存在。[作者 README](https://github.com/OpnForm/OpnForm)展示的是表单创建、发布、提交收集与分析；[根 LICENSE](https://github.com/OpnForm/OpnForm/blob/main/LICENSE)和 README 区分 AGPL 核心与 `api/app/Enterprise/` 的专有许可。2026-10-14 有[修复提交](https://github.com/OpnForm/OpnForm/commit/c851f9fb3c581d9c36571cefc0d1d4e735c34cfd)。本次未取得共享题库、判分、重复练习、个人学习记录完整链路的证据，故不占三项推荐名额；仅可旁证发布表单与收集提交的实现。
- **OpExams**：[官方站点](https://opexams.com/)有考试和 AI 题目生成产品，但本轮检索及官网未建立作者公开仓库与许可证链路。免费工具不等于开源，不纳入开源对照，也不继续扩展商业竞品调研。
- **ExamHub**：依用户澄清，停止同名项目检索，不将任何同名仓库与用户项目绑定。

## 给主调研的交接判断

建议用 Quizfreely 对照社区内容与学习记录，用 Quizzle 对照发布和服务端判分，用 Exameow 对照 AI 出题与考试分享。用户项目值得自行设计的差异集中在：长期共享题库、题目修改后历史答案可解释、个人跨题库学习记录，以及可验证的 AI 教学闭环。以上是基于对照的设计判断，不是这些项目已经承诺或已经证明缺失的完整功能审计。
