# AI 出题网站重做：独立竞品研究笔记

核验日期：2026-10-20。用途：评估“教材 → 题库 → 练习闭环”作为求职项目的价值。

## 结论

值得做，但“上传 PDF、AI 出题、错题本”已是常见能力。建议聚焦一门中文课程，把**教材证据可追溯、题目可校订、错题回到原文、再测可验证**做完整。差异化应落实到质量和闭环细节，不能宣称市场上没人做。

本笔记按 research 技能核验一手资料。仅采用官方帮助中心、官方产品页、作者仓库及 GitHub API；未登录实测商业产品、未运行开源项目。以下“已核验”指读到公开文档或代码，不代表实际可用性、准确率或学习效果已通过测试。未调研 cynicalight/reader，未修改项目代码。不记录未经验证的用户量、效果或价格。

## 产品比较

| 对象 | 已有能力与闭环 | 小团队值得借鉴 | 不能据此断言 |
| --- | --- | --- | --- |
| NotebookLM | 文档生成卡片/测验，解释附来源引用；当前帮助页记录进度、错卡复习、重做和 CSV 卡片导出 [N1][N2] | 来源选择与练习共用上下文；解释入口紧贴题目；后台生成不中断阅读 | 不能说它没有复习闭环，也未证实有完整跨教材错题调度 |
| Quizlet | 笔记/卡片生成 AI Practice Tests，题型、题量、计时可选，提交后评分；网页版卡片已有间隔复习 [Q1][Q2] | 学习与模拟考试分开；既有卡片可复用；到期复习有明确入口 | 文档中的地区、语言、年龄限制不能忽略；未证实所有模式共享同一掌握度 |
| Knowt | 文件转笔记/卡片，笔记出选择题；卡片测验支持错题重做、历史成绩；间隔复习按四档反馈安排 [K1–K4] | 同一资料多种练习；结果页直接再练错题；控制每日新卡量 | 笔记出题和卡片测验是不同流程，不能合并宣传为任意材料支持全部题型 |
| StudyFetch | 资料/卡片生成多题型测试；成绩与主题表现；逐题打开带上下文的 AI 讲解，再次测试 [S1–S3] | 资料范围先确认；高级配置折叠；当前题目直接进入导师对话 | 未证实主题分析算法、判分准确性或中文教材表现 |
| Exameow（过了喵） | 作者声明支持资料出题、多题型、题库与错题；源码确认 PDF 解析/OCR、错题本及按天练习统计 [O1–O6] | 优先复用解析器；进度与取消；小规模本地练习数据 | 本地存储不等于 AI 请求不出设备；未运行验证端到端生成质量 |

## 来源台账：实际核验与不确定点

### NotebookLM

- **[N1] 当前帮助页**：[Generate Flashcards or Quizzes](https://support.google.com/gemininotebook/answer/16958963?hl=en)。实际打开正文：后台生成、难度/提示自定义、解释、卡片记忆状态、进度恢复、结果重做、仅练错卡、卡片 CSV 下载。**不确定**：未登录验证账号开放范围；未证明测验错题进入长期跨资料复习队列。页面当前标题为 Gemini Notebook，本笔记保留用户指定的 NotebookLM 名称；不据此推断所有地区的品牌迁移情况。
- **[N2] 官方发布文章（2025-09-08）**：[6 ways to use NotebookLM to master any subject](https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-student-features/)。实际打开：卡片/测验解释带原始资料引用，Learning Guide 引导提问，OpenStax 教材合作。**不确定**：发布文章不是今天的逐账号验收；“基于来源”不等于无幻觉或每题均有精确页码。

### Quizlet

- **[Q1] 官方帮助页**：[Studying with Practice Tests](https://help.quizlet.com/hc/en-us/articles/25946589648013-Studying-with-Practice-Tests)。实际打开：笔记或卡片生成测试、题量/题型/时间配置、交卷评分复查、保存与分享；明确区别 AI Practice Tests 与普通 Test。文档写明英语界面及地区/年龄条件，非订阅账户只有有限访问。**不确定**：未测试中文资料及中国大陆账号；页面不能证明逐题原文引用、长期错题管理或全部订阅权益。
- **[Q2] 官方帮助页**：[Studying with Spaced Repetition](https://help.quizlet.com/hc/en-us/articles/48324742264077-Studying-with-Spaced-Repetition)。实际打开：翻卡后四档自评决定再现时机，设置每日新卡量，键盘操作；当前标注仅网页版支持。**不确定**：调度算法未公开在该页，不能说它使用 FSRS/SM-2；未证实和 AI 测试成绩联动。
- **[Q3] 官方入口，读取受限**：[Study Guides](https://quizlet.com/study-guides/upload/)。仅搜索返回摘要可见笔记/PDF 等输入描述，直接打开失败。**不确定**：完整当前流程未核验，因此不以此页支撑功能细节结论。

### Knowt

- **[K1] 官方入门指南**：[Student’s Guide](https://help.knowt.com/en/articles/10722204-student-s-guide-to-getting-started)。实际打开，页面日期 2026-09-10：PDF、幻灯片、图片或视频可生成笔记/卡片，并提供多个学习模式及考试日期设置。**不确定**：复杂公式、扫描教材识别与长书覆盖率未测。
- **[K2] 笔记出题**：[Practice test from notes](https://help.knowt.com/en/articles/10298080-how-can-i-take-a-practice-test-from-my-notes)。实际打开：超过 200 words 的笔记可生成选择题，可重测或生成新测试。**不确定**：中文如何计数、是否逐题回链原文，页面未交代。
- **[K3] 卡片测验**：[Practice Test mode](https://help.knowt.com/en/articles/10714642-how-do-i-use-practice-test-mode)。实际打开：题量、题型、收藏过滤及 Smart grading；逐题反馈、重做错题，保存分数/对错/跳过/日期。**不确定**：Smart grading 的模型、稳定性及人工申诉处理未在该页验证。
- **[K4] 间隔复习**：[Spaced Repetition mode](https://help.knowt.com/en/articles/10714645-how-do-i-use-spaced-repetition-mode)。实际打开：每日新卡量、Again/Hard/Good/Easy 四档、可调整间隔。**不确定**：具体调度实现和学习收益未验证；不把官方效果措辞当实验结论。

### StudyFetch

- **[S1] 官方创建教程**：[Create a Practice Test](https://sso.studyfetch.com/docs/docs/product-docs/6a63bfe5ee9569d818eecc3c)。实际打开：选择资料或卡片、确认资料、配置题型数量、语言及 Focus Topic；空/过短资料会阻止创建。**不确定**：未登录确认可用题型权益、具体语言覆盖及超长材料处理方式。
- **[S2] 官方答题教程**：[Take and Review a Practice Test](https://sso.studyfetch.com/docs/docs/practice-tests/take-and-review-a-practice-test)。实际打开：单题/整卷视图、答题导航、交卷成绩及主题表现、逐题对错；“Chat About This Question”自动限定当前题目，可重测。**不确定**：题目讲解未被证明全部带可点击教材证据；主题表现不等于可靠知识诊断，亦未核验长期调度。
- **[S3] 官方产品页**：[Quiz and Test Preparation](https://sso.studyfetch.com/use-case/quiz-and-test-prep)。实际打开 FAQ：列明 PDF、DOCX、PPTX、文本、图片以及 Google Docs、音视频等资料入口。**不确定**：这是产品声明，未实测导入兼容性、OCR 或中文效果。

### 开源：Exameow

- **[O1] 作者仓库**：[heshengtao/exameow](https://github.com/heshengtao/exameow)。实际读取 README 和目录：资料转题目、多题型、题库/练习/错题本地保存；存在 frontend、Rust core、workers。**不确定**：README 中“exam-quality”等措辞未实测；不把所有宣称当作已验证行为。
- **[O2] 维护状态**：[仓库 API](https://api.github.com/repos/heshengtao/exameow)、[默认分支最近提交](https://api.github.com/repos/heshengtao/exameow/commits?per_page=1)。实际读取：未归档，pushed_at 为 2026-10-06T11:58:30Z；核验 HEAD 为 `960edd5718846acb1266e3fc4c56b5e1725714a5`，提交时间 2026-10-06T11:47:49Z。**不确定**：一次近期更新不能证明长期维护质量、响应速度或生产稳定性。
- **[O3] 许可证与依赖**：[LICENSE](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/LICENSE)、[frontend/package.json](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/package.json)。实际读取许可证开头及包清单，并与 GitHub license 元数据交叉核对为 Apache-2.0；前端使用 Vue、Pinia、PDF.js、mammoth 和 OCR 依赖。**不确定**：未做全部第三方许可证、漏洞或模型资产审查；不能直接宣称整体可无条件商用。
- **[O4] PDF 实现**：[pdfParser.ts](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/src/utils/pdfParser.ts)。实际读取完整文件：PDF.js 逐页取文本；少于 30 字符时尝试 OCR；支持进度、取消和资源清理；最终返回拼接字符串。**不确定**：只证实此接口未返回结构化页码，不能推断整个项目没有其他来源追踪路径；OCR 与公式质量未测。
- **[O5] 练习数据**：[wrongQuestions.ts](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/src/stores/wrongQuestions.ts)、[practiceHistory.ts](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/frontend/src/stores/practiceHistory.ts)。实际读取错题存储相关行及完整练习历史文件：localStorage 持久化、错题次数、按天/题型累计正确数。**不确定**：未验证跨设备同步、迁移、容量上限及所有页面调用链。
- **[O6] AI 接口适配**：[workers/src/ai.ts](https://github.com/heshengtao/exameow/blob/960edd5718846acb1266e3fc4c56b5e1725714a5/workers/src/ai.ts)。实际读取关键行：Cloudflare AI 调用、输入截断、多返回格式与流式响应适配。**不确定**：未审计完整出题流程和 schema 校验；本地题库存储不意味着调用远程模型时教材内容不出设备。

## 可形成差异的方向（研究判断，尚非用户需求验证）

1. **中文单课程、按章节覆盖。** 先让用户确认教材版本和章节，再显示各章已生成/已练/待复习。价值在范围明确和覆盖可检验；不宣称竞品不支持中文。
2. **逐题证据与纠错闭环。** 每题保存教材版本、页码、证据片段；解释可返回原文。错误题可改答案、停用或重新生成，历史作答绑定题目版本。引用本身已有竞品提供，重点是把溯源贯通题库维护与练习记录。
3. **用新题检验同一知识点。** 错题先看证据，再做同知识点的另一题，分开展示“原题重做”与“新题结果”。这只是更好的项目评测设计，不能直接宣传为学习效果提升。

上述公开资料没有充分说明“一套中文教材的版本—页码证据—题目修订—错因—新题复测”的完整链条。这是可继续验证的产品切口，不是竞品缺失证明。

## 适合小团队的体验与实现建议

以下是基于竞品的方案建议，不是对商业产品内部架构的推测。

| 优先级 | 可交付范围 | 体验与实现取舍 | 验收证据 |
| --- | --- | --- | --- |
| 首版 | 一门课、文本 PDF、单选题、可编辑题库、作答/错题重做 | 章节范围确认后生成小批题；解析沿用成熟 PDF 工具，保存页码/原文偏移；持久化任务状态与失败原因 | 同一教材可以重复导入、生成、校订、练习；刷新恢复；失败可重试且不重复入库 |
| 首版 | 每题证据与基础质量检查 | 结构化字段保存题干/选项/答案/解析/证据；验证选项数量、答案索引、证据能在原文定位；人工确认再入正式题库 | 抽检“引用存在”与“引用支持答案”两个指标；坏题能停用，历史作答不被修改覆盖 |
| 下一步 | 错题复习及同知识点新题 | 从结果页直接回教材或再练；先按错题和到期时间排队，规则透明；有需要再引入成熟间隔复习算法 | 记录首次/复测结果、题目版本和复习时间；区分背答案与做新题 |
| 暂缓 | 多模态录课、语音导师、社交题库、多端客户端 | StudyFetch 的广度不适合首版照搬；Exameow 的跨端栈只作参考，优先复用旧项目已有技术 | 在核心闭环真实完成前不扩张范围 |

实现上，按章出题可先直接使用已选章节文本，不必一开始引入向量库、知识图谱或多代理。需要跨章节检索后再加检索层。错题排序与客观题判分用确定性逻辑，模型主要负责出题和解释。扫描 PDF、复杂公式作为明确的第二阶段范围。

求职展示应提供可复现的演示教材与评测集，记录题目可用率、答案/证据一致性、重复率、生成耗时及真实调用成本；这些是待测指标，本研究没有产生数值。展示一次“坏题被发现 → 定位教材 → 修订题目 → 保留旧记录 → 再练”的流程，比堆叠 AI 功能更能说明工程能力。
