# examSetting

一个基于大模型 API 的智能出题系统。项目整体是“前端表单 + 后端提示词工程 + 智谱 AI 接口”的结构，可以生成单题或整套试卷，并支持将生成内容导出为 Word 文档。

## 项目结构

```text
examSetting-main/
├─ backend/
│  ├─ app.py          # Flask 后端、提示词、智谱 AI API 调用
│  └─ models.py       # 目前为空，未实际使用
├─ frontend/
│  ├─ src/            # Vue 3 前端源码
│  ├─ package.json    # 前端依赖和启动脚本
│  └─ vite.config.ts  # Vite 配置
└─ README.md
```

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus、Tailwind CSS、DaisyUI
- 后端：Flask、Flask-CORS
- 大模型：智谱 AI `zhipuai` SDK，当前模型写死为 `glm-4`
- 导出：前端使用 `docx` 生成 `.docx` 文件

## 主要功能

### 1. 整卷出题

入口：前端首页 `/index`

功能：

- 选择目标科目、专业、课程或知识点。
- 输入整卷出题要求。
- 设置题型数量：
  - 单选题
  - 多选题
  - 填空题
  - 判断题
  - 解答题
  - 拔高题
- 点击“生成随机需求”，让大模型根据已选知识点生成一段出题需求。
- 点击“提交任务需求”，生成整套试题。
- 点击“继续生成”，可以基于当前已有题目继续生成，后端会把已有题目一起传给模型，提示模型不要重复出题。
- 点击“导出 word”，将当前试题内容导出为 `.docx`。
- 点击“一键清空”，清空当前试题结果。
- 点击“切换到单题”，进入单题出题页面。

对应后端接口：

- `POST /api/requirement2`：生成整卷随机需求。
- `POST /api/whole`：生成整套试题。
- `GET /api/whole`：健康检查，会返回 AI assistant is running。

### 2. 单题出题

入口：前端 `/index2`

功能：

- 选择目标科目、题目类型和难度等级。
- 支持题型：
  - 单选
  - 多选
  - 填空
  - 判断
  - 解答
- 支持 1 到 5 级难度，后端映射为：
  - 1：非常简单
  - 2：简单
  - 3：正常
  - 4：较难
  - 5：困难
- 点击“生成随机需求”，由大模型生成题目要求和考察范围。
- 点击“提交任务需求”，生成单个题目。
- 生成结果会拆成：
  - 题目要求/题干
  - 答案解析
  - 评分标准
- 点击“导出 word”，将单题、答案解析和评分标准导出为 `.docx`。
- 点击“切换到整卷”，返回整卷页面。

对应后端接口：

- `POST /api/requirement`：生成单题随机需求。
- `POST /api/single`：生成单个题目。

### 3. AI 评价和 AI 对话

后端已经写了两个接口：

- `POST /api/check`：根据当前生成的单题和用户答案，让模型评分、评价并给建议。
- `POST /api/chat`：围绕当前生成的单题继续和模型对话。

不过前端 `AnswerPage.vue` 里相关 UI 目前被注释掉了，所以页面上默认看不到“提交答案”和“AI交流”按钮。如果需要恢复，可以取消 `frontend/src/components/AnswerPage.vue` 中对应模板代码的注释。

### 4. 登录/注册页面

入口：`/login`

当前状态：

- 登录、注册、忘记密码页面主要是前端 UI。
- 实际请求 `/api/login`、`/api/register`、`/api/forget` 的代码都被注释了。
- 后端也没有实现这些用户接口。

所以当前项目没有真正的用户系统。

### 5. 文件参考上传

前端有“选择文件”按钮，支持选择：

- `.pdf`
- `.doc`
- `.docx`
- `.jpg`
- `.png`
- `.jpeg`

但当前后端没有实现 `POST /api/postlib`，因此文件不会真正被后端处理，也不会参与出题。这个功能目前属于未完成状态。

## 如何运行

需要同时启动后端和前端。

### 1. 启动后端

进入后端目录：

```bash
cd backend
```

安装 Python 依赖：

```bash
pip install flask flask_cors zhipuai
```

启动 Flask：

```bash
python app.py
```

默认后端地址：

```text
http://localhost:5000
```

### 2. 启动前端

进入前端目录：

```bash
cd frontend
```

安装依赖：

```bash
pnpm install
```

启动开发服务器：

```bash
pnpm dev
```

Vite 默认会输出访问地址，通常是：

```text
http://localhost:5173
```

打开该地址即可使用。

## API Key 在哪里换

大模型配置在：

```text
backend/app.py
```

当前代码顶部有这一行：

```python
client = ZhipuAI(api_key="这里是你的智谱 API Key")
```

把字符串替换成你自己的智谱 AI API Key 即可。

当前所有大模型接口都使用：

```python
model="glm-4"
```

如果要更换模型，需要在 `backend/app.py` 中搜索 `model="glm-4"`，将它们替换为新的模型名。

涉及接口包括：

- `/api/requirement`
- `/api/requirement2`
- `/api/single`
- `/api/check`
- `/api/chat`
- `/api/whole`

注意：当前 API Key 是硬编码在代码里的，不适合公开仓库或生产环境。更推荐改成读取环境变量，例如：

```python
import os

client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
```

然后在本地设置：

```bash
set ZHIPUAI_API_KEY=你的key
```

PowerShell 可以使用：

```powershell
$env:ZHIPUAI_API_KEY="你的key"
```

## 前后端地址配置

前端请求地址目前写死为：

```text
http://localhost:5000
```

主要分布在这些文件：

- `frontend/src/components/QuestionPage.vue`
- `frontend/src/components/WholePage.vue`
- `frontend/src/components/AnswerPage.vue`
- `frontend/src/components/question/DocUpload.vue`
- `frontend/src/utils/requests.ts`

如果后端端口或部署地址改变，需要把这些位置里的 `http://localhost:5000` 改成新的后端地址。

## 后端接口说明

### `POST /api/requirement`

生成单题随机需求。

请求字段：

- `target`：目标知识点路径数组。
- `type`：题型，取值如 `单选`、`多选`、`填空`、`判断`、`解答`。
- `difficult`：难度，1 到 5。

返回：

- 流式文本。

### `POST /api/single`

生成单题。

请求字段：

- `target`
- `type`
- `difficult`
- `questionNeed`

返回 JSON：

```json
{
  "info": "success",
  "message": "模型生成的题目、答案解析和评分标准"
}
```

前端依赖模型输出中包含：

- `答案解析：`
- `评分标准：`

如果模型没有按这个格式输出，前端拆分结果时可能会出错。

### `POST /api/check`

根据当前单题和用户答案生成评分评价。

请求字段：

- `message`：用户答案。

返回：

- 流式文本。

注意：它依赖后端全局变量 `title_info`，也就是最近一次 `/api/single` 生成的题目。

### `POST /api/chat`

围绕当前单题继续对话。

请求字段：

- `message`：用户输入。

返回：

- 流式文本。

注意：同样依赖后端全局变量 `title_info`。

### `POST /api/requirement2`

生成整卷随机需求。

请求字段：

- `target`：多选的目标知识点路径数组。

返回：

- 流式文本。

### `POST /api/whole`

生成整套试卷。

请求字段：

- `target`：目标知识点路径数组。
- `questionNeed`：整卷要求。
- `num1`：单选题数量。
- `num2`：多选题数量。
- `num3`：填空题数量。
- `num4`：判断题数量。
- `num5`：解答题数量。
- `num6`：拔高题数量。
- `existing`：当前页面已有题目文本，用于提示模型避免重复。

返回：

- 流式文本，前端会用 Markdown 渲染。

## 当前限制和注意事项

- 项目核心是提示词工程，没有数据库，也没有真正的用户权限体系。
- API Key 写在 `backend/app.py` 中，建议改为环境变量。
- 前端请求地址多处写死为 `http://localhost:5000`。
- `/api/postlib`、登录、注册、忘记密码等接口没有后端实现。
- `/api/check` 和 `/api/chat` 依赖后端全局变量 `title_info`，多人同时使用时会互相覆盖上下文。
- 单题结果解析依赖模型严格输出 `答案解析：` 和 `评分标准：`，如果模型格式漂移，前端可能解析失败。
- 整卷生成采用流式输出，内容只保存在浏览器页面中，刷新页面会丢失。

## 常见问题

### 前端页面能打开，但生成失败

检查后端是否启动：

```text
http://localhost:5000
```

如果没有启动，前端请求会失败。

### 后端启动报 `No module named flask`

安装依赖：

```bash
pip install flask flask_cors zhipuai
```

### 生成题目时报 API 相关错误

检查：

- `backend/app.py` 中的智谱 API Key 是否有效。
- 当前模型名 `glm-4` 是否仍可用。
- 网络是否能访问智谱 AI 服务。

### 点击文件上传失败

这是正常的当前状态。前端写了上传 UI，但后端没有 `/api/postlib` 接口，需要后续补充。
