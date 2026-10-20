# V4 真实模型教学评测

用户已授权：发布 V3，继续补真实模型教学效果证据；首轮 DeepSeek 总调用最多20次。随后用户另行追加20次，用于同场景修复复测；两轮分别计数，不共享或隐含追加额度。V4 最初留本地供验收；后续用户再次明确授权最多20次测试其余两个场景、补独立辅助评分，验收后提交 GitHub。第三轮单独计数，发布采用基于 V3 的分支和 PR，不自动合并。

## 取舍

复用 V3 的真实教学引擎与模型消息，不在评测器里预编排 Agent 动作。固定学生回答只模拟输入，不模拟学习。选择本地 SQLite 作业和 JSON 报告；独立评测数据集与人工量表，不引入新的通用编排框架。

参考 AgentEvals (MIT) 的轨迹评测和 Promptfoo (MIT) 的模型对比；二者覆盖通用评测，但当前的题目快照、服务端工具约束和人工复核均已有基础。当前直接复用，保留标准消息/JSON 导出，后续可接外部平台。

## 交付

1. 独立原创 live 数据集，四个场景（概念混淆、正确后的理由追问、无出处的简答、资料指令干扰），固定历史、题目与学生回答。同一场景运行规则和模型，各 1–3 次可选重复。Agent 自主选择六个工具；不要求唯一动作顺序。
2. 可持久化评测作业：创建幂等，所有者隔离，启动前明确付费，最多 20 次调用/作业、每 trial 最多 10 次、最多 40 动作。最多 1 作业/用户和 2 作业/实例；调用预留与保存先于网络，作业按小时限制用户 40 / 实例 120 次调用。异常、取消、预算耗尽、重启均保留未完成 trial 在分母，绝不自动补跑付费请求。保存数据集/提示哈希、模型/供应商、生成参数、返回模型名、实际 usage（缺失即 null）、耗时、请求消息、原始 content、动作与工具结果；不保留密钥、HTTP headers 或隐藏思维链。
3. 自动结果只称行为证据：完成、真实模拟答题、反馈、引用、理由追问、非法动作、模型调用与延迟。失败和未运行均保留分母，重复结果以 trial 展示，不能把正确率或工具调用率当学习收益。
4. 可导出遮蔽策略的复核包：随机 blindId、打乱顺序，保留场景、回答、教材和反馈，不含条件/模型/运行 ID/轨迹。单独报告存映射；这是辅助遮蔽，不保证正式双盲。人工四维 0–2 分（事实正确、证据支持、误区诊断、下一步可执行），每项说明、复核者及 type=human/ai-assisted 明确。无复核即 null。写入需版本校验，不算到模型行为通过率。
5. Vue 页面沿用现有白蓝工作台，数据集、调用预算、开始/取消、进度、失败、规则对比、原始 JSON、人工复核；identity guard、重试沿用同一 requestId，刷新不自动创建作业。界面明确固定学生并非真人。
6. 真人学习收益：提供匿名前测/后测/延迟测试的 CSV 模板、研究协议与 stdlib 分析命令；逐人原始分数、组均值与增益描述，缺失保持缺失、不补造，重复 ID 和不合法分数拒绝。没有真人数据时不显示提升结论。

## API 与接口

- GET /api/tutor/live-evaluations/dataset -> {dataset:{id,version,hash,cases:[{id,title,goal}],limitations}}
- POST /api/tutor/live-evaluations {requestId,caseIds:string[1..4],repeats:1..3,maxCalls:1..20} -> {evaluation} 202/重放200
- GET /api/tutor/live-evaluations -> {evaluations}
- GET /api/tutor/live-evaluations/:id -> {evaluation}
- POST /api/tutor/live-evaluations/:id/cancel -> {evaluation}
- GET /api/tutor/live-evaluations/:id/blind -> {package:{kind,version,datasetHash,rubric,items:[{blindId,caseTitle,goal,questions,answers,events}]}}
- PUT /api/tutor/live-evaluations/:id/reviews/:blindId {version,reviewer,reviewerType:'human'|'ai-assisted',scores:{accuracy,grounding,diagnosis,actionability}:0..2,notes} -> {evaluation}; version 冲突409

Evaluation: {id,version,status:'queued'|'running'|'completed'|'cancelled'|'interrupted'|'failed',createdAt,updatedAt,model,provider,datasetHash,promptHash,maxCalls,modelCalls,error,report}. report={kind:'live-tutor-evaluation',graderVersion,caseSnapshots,datasetId,datasetVersion,datasetHash,promptHash,parameters,learner:'fixed-script',trials,summary,limitations,rubric}. Trial={id,blindId,caseId,title,strategy:'rule'|'agent',repeat,status:'pending'|'running'|'completed'|'failed'|'budget'|'cancelled'|'interrupted',error,modelCalls,elapsedMs,usage:null|{prompt_tokens,completion_tokens,total_tokens},steps,session,checks:[{code,message,passed}],review:null|{reviewer,reviewerType,scores,notes,updatedAt}}. summary 每策略={trials,completed,passed,checks,passedChecks,modelCalls}; trials/denominator 包含未运行。

模型适配器 call_model_response(settings,messages,*,max_tokens=6000,thinking=None) 返回 {content,usage,model}，原 call_model 保持返回字符串兼容；live 使用 max_tokens=2000、DeepSeek thinking=disabled，temperature=0.4，参数进报告。

## 成功标准

现有全部测试/build 通过；新增真实 HTTP 替身验证协议、调用上限、失败分母、幂等、权限、取消迟到、重启中断、复核版本与 guest迁移；浏览器检查桌面与手机。用用户提供的配置真实运行两场景、最多20次调用，保留成功或真实错误报告。不生成付费的备用模拟学生或模型裁判。若供应商失败如实保留，不能声称已得到教学质量或学习收益结果。


## 首轮实测后的补充约定

首轮20次真实调用已经用完，两个模型 trial 均未完整结束；不追加调用。保留原提示哈希、原始统计与 `live-behavior-v1` 判据，其动作检查包含正常完成要求。新版本 `live-behavior-v2` 将动作合法性和完成分开，未执行 trial 的动作检查仍不能通过。后续对比须匹配判据版本。

新模型上下文补充 historyRead、最近六个工具摘要与最后一次检索结果数；检索将已答题的题干、主题作为词面元数据，但仍仅返回原 source/citation。首轮结束时两处改进只通过回归，尚未真实复测；追加授权后的结果见下文，不能回写首轮失败为成功。

独立审查要求在序列化前移除原始及 JSON 转义的当前密钥；可识别的思考标签须在存储前去除，异常协议仍保留失败。对任意未标记自然语言不承诺语义上的思维链识别。取消与模型动作写入须有同一个原子提交边界，已预留额度不因中断回退。

## 追加20次同场景复测

成功标准：保留原题目、出处、历史、目标和固定回答，重测 TCP 与事务场景；逐次记录调用上限、实用量、提示版本、失败与成功。修正须复用现有引擎和严格工具校验，不通过替模型编排动作制造通过。原始 content 可离线回放，无额外付费请求。

实际使用4+6+5+5=20次。首次 TCP 因反馈参数错误失败，随后系统提示明确参数必须放入 args；后续 TCP 一次及事务两次均正常结束并通过全部行为检查。四份原始报告与限制详见 [真实复测记录](../../evaluation/live-model-evaluation.md)。本轮未补写质量评分、独立留出集或真人学习收益，不以三个成功样本宣称长期稳定。

## 第三轮与发布验收

再次授权最多20次，实际使用1+4+3+4+3=15次，剩余5次不调用。保留无出处首次提前结束但未达目标的负例；仅补清无教材仍应先提问的系统提示，后两次无出处完成，资料指令干扰两次完成。最终提示为 `tutor-v3.4`，数据集不变，成功轨迹不能跨提示拼成最终版本通过率。

两位未参与开发的 AI 助手分别只读策略遮蔽包，补评前轮8条及本轮10条；通过原 API 保存，公开附件包含实际输入、原快照哈希、评分依据，原执行快照不改写。标签始终为 `ai-assisted`，只评反馈／追问，不包括 finish 总结；独立真人评分和学习收益仍未实现。

发布前审查复现畸形引号包裹转义密钥／思考标签的遗漏，修复共用脱敏入口，回归覆盖原始内容、合法外层 JSON 和元数据。敏感或过深转义的异常字符串保守隐藏，不用清理后的字符串执行动作；普通无敏感内容保持原字节。
