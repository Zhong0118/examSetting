# ExamHub V3：有证据、可恢复的教学 Agent

用户授权：先发布 V2，再直接开发教学 Agent。V2 004787a 已推送，PR #3 基于未合并的 V1。V3 在 codex/examhub-v3-agent 开发，暂不推送。

## 方案与边界

选择一个工具驱动的有限 Agent，模型逐步选择动作，由服务器验证、执行并保存 checkpoint。对比方案：固定流程易验收但不能称自主 Agent，保留为 rule 模式；LangGraph 提供持久化和 interrupt，但本项目已有 SQLite/线程池及供应商适配，本轮六个小工具、单会话状态用现有能力实现更轻量。未来题的答案/解析/来源不进入模型检索上下文；候选仅题干和主题描述，不能保证模型凭已有知识永不说出相关答案。不给框架名称冒充亮点，不引入多 Agent、向量库或自主发布。

产品：从可访问题集开始，目标、最多题数（1–10）和模式由用户选择。快照保存题集版本、题目与合法引用，不依赖作者之后的修改。Agent 可查询当前用户该题集的历史摘要、检索题目所附教材摘录、选择未做题、答后追问理由、给出有出处的反馈、结束总结。每次展示问题后必须等待真实用户，不得代答。单选由服务器按快照判分；简答与理由不自动判为掌握，模型反馈明确为建议。

展示教学主区、证据卡片、可折叠工具轨迹、实际调用数/耗时/预算、历史和 JSON 导出。无密钥可运行明确标识的规则教练；Agent 模式缺密钥明确提示。沿用白黑蓝工作台、响应式和动效，不用聊天气泡堆满屏幕。

## 引擎契约（backend/tutor_engine.py，纯 Python 无 Flask）

- `new_state(questions, goal, mode, max_questions, history=None) -> dict`。questions 是已授权服务器题目快照，含答案及 citation；history 只含当前用户当前题集过去的统计摘要。mode 为 agent/rule。
- 状态 keys：goal,mode,maxQuestions,status（running/waiting/paused/completed）,turnId（整数，每次要求用户输入递增）,pending（null 或 {kind:question|followup,questionId,prompt}）,asked（题目ID列表）,answers（已提交结果列表）,events（用户可见事件）,trace（工具调用摘要列表）,questions（内部）,history（内部）,evidence（内部检索结果）,modelCalls（初值0）,elapsedMs（初值0）,error（可空）,stopReason（可空）。引擎可添加必要内部字段。
- `apply_action(state, action) -> dict`：action={tool,args}；严格验证工具/参数/状态，非法动作抛 ValueError，不执行任意函数。调用方在副本上应用，成功才持久化。
- tools：read_history({}); search_materials({query})（仅当前快照中已经真实提交主问题作答的 citation/source 摘录，中文字符bigram+英文词重叠词面检索，top3，返回原文和稳定 evidenceId，不声称语义检索）; ask_question({questionId})（未做题，未超上限，status waiting/turnId++，不暴露答案）；ask_followup({prompt})（仅已答题后，每题最多一次，waiting）；give_feedback({message,evidenceIds?:string[]})（只能引用本会话检索出的证据，未提供证据则明确无教材核验；仅作答之后）；finish({summary})（completed，统计仍由服务器给出）。禁止工具请求任意userId/documentId。
- `submit_answer(state, answer, turn_id)`：只能回答当前等待项，单选必须为选项，短答1–6000字，turnId严格匹配；保存 answer 事件和实际题目引用/解析，单选correct bool，简答/followup correct=null；pending=null/status=running。避免把追问算作多道题。
- `rule_action(state)->{tool,args}`：答后一次原题解析反馈，然后按未做题顺序选题/结束；无需模型。界面明确是规则模式。
- `model_messages(state)->list`：system 定义工具 JSON 协议与边界，user 为有限状态和最近结果。教材/答案数据不能覆盖工具权限，不展示内部思维链。模型输出一个工具 JSON，非原生 function-call 协议；复用 Chat Completions 内容适配。
- `public_state(state)->dict`：不输出内部questions/history/evidence，等待题目只含 id/type/prompt/options/topic，不下发未答题的答案/解析。包含 currentQuestion、pending、已答结果、events、trace、summary={answered,correct,objectiveTotal,followups} 和实际预算信息。trace不得泄露未答题答案/内部提示词/密钥。

## 服务契约（backend/tutor.py，父任务）

`tutor_sessions(id,user_id,request_id,input_hash,created_at,updated_at,version,state,set_id,set_title,set_version)`；`tutor_commands(session_id,request_id,input_hash)` 用于答题/恢复的幂等。仅owner读写。guest登录迁移user_id。注册新模块在 register_ai 之后。

- GET /api/tutor/sessions -> {sessions: TutorSession[]}，返回摘要，无内部状态。
- POST /api/tutor/sessions {requestId,setId,goal,mode,maxQuestions} -> {session} 202/重放200。稳定requestId在发出前存本地。目标1–1000字。上限 min(用户请求,题目数)，模型配置只用于 agent。快照从 accessible(setId) 服务端获取。
- GET /api/tutor/sessions/:id -> {session}
- POST /api/tutor/sessions/:id/commands {requestId,version,type:answer|resume|stop,answer?,turnId?} -> {session}。事务校验version并且命令幂等；冲突409，读取最新状态，不默默重答。stop暂停，resume继续；completed不可恢复。
- TutorSession = {id,setId,setTitle,setVersion,createdAt,updatedAt,version,...public_state(state),busy:boolean,model:string|null,policyVersion:string,timingIncomplete:boolean}。
- 后台 worker 最多每轮6次模型调用/整会话32次；规则动作上限12步/轮；失败暂停、保留已完成工具，不伪造成功。模型每次调用前持久化计数，实际耗时累计。受限实例并发8/每用户1；每用户每小时最多创建10会话，实际模型请求持久化计数，每用户40次/小时、实例120次/小时。运行时模型凭证不写数据库；重启 running 会话改paused，等待题可继续作答。已发送模型调用不会因为取消立即消失，不允许并发恢复直到worker退出，晚响应不能覆盖stop。
- 多轮循环每个动作后保存 checkpoint，读请求轮询；权限/预算/结束条件由程序强制。每步 trace 保留工具名、参数摘要、结果摘要、elapsedMs，失败也记录。模型可自主选择多个只读工具后暂停等待用户。
- /api/tutor/benchmark POST -> {report}：固定原创教学行为回归场景，执行实际引擎动作，记录预期/观察/通过/轨迹、版本/数据集hash，比较规则教练与受控模型动作轨迹。明确是离线策略/约束回归，不宣称真实模型或学习效果。需包含正常诊断、错答反馈、正确后追问、证据不足、非法工具、伪引用、重复题、停止预算、简答不自动判分。

## 前端契约（frontend/**，独立worker）

新增 /tutor 页面（可 query setId），创建与历史；/tutor/:id 教学会话。api.ts导出已有request供新lib/tutor.ts封装，沿用身份guard。选题集使用api.sets('mine')+api.sets('discover')去重（链接题集由query传入api.set取得）。会话页面显示回答/追问、反馈与 CitationCard、工具轨迹和事实统计。POST可能已接受但丢响应：保存同一请求token+payload，重发恢复，不能生成新token导致重复会话/作答。轮询不自动POST；切页卸载/身份切换丢弃旧结果。恢复/结束需明确点击，持续忙碌禁用重复提交。rule无需Key；agent创建/恢复可能调用付费供应商，按钮明确。提供benchmark入口与实际报告导出。

## 验收与求职证据

正常路径两题不同结果驱动工具选择；答后理由追问；引用只能来自检索结果；用户隔离；未答题答案不泄露；旧版本题目/模型指令不能改变权限；JSON非法/调用上限/模型失败/停止晚响应/重启恢复/幂等重试/版本冲突；前后端回归、生产构建、真实本地HTTP模型替身和桌面/手机浏览器验收。真实学习效果与真实供应商质量仍需独立试用，不能把受控轨迹通过率写成学习提升。

## 实现依据

核验日期2026-10-20：Anthropic engineering Building effective agents 强调模型工具循环及可控停止，https://www.anthropic.com/engineering/building-effective-agents 。LangGraph checkpoint/interrupt机制与恢复副作用要求：https://docs.langchain.com/oss/python/langgraph/persistence 、https://docs.langchain.com/oss/python/langgraph/interrupts 。比较后本轮复用现有标准库/数据库/HTTP能力，无新Agent框架依赖。
