> **Historical translation**
>
> This translation documents the original examSetting release, before the ExamHub workbench rebuild. The current application, installation steps, technology stack, pagination, and evaluation evidence are described in the [current ExamHub README](README.md). The instructions below are retained as historical documentation.

# examSetting

An intelligent question generation system based on Large Language Model (LLM) APIs. The project follows a "frontend form + backend prompt engineering + Zhipu AI API" architecture. It can generate single questions or complete exams and supports exporting the generated content to Word documents.

## Project Structure

```text
examSetting-main/
├─ backend/
│  ├─ app.py          # Flask backend, prompt engineering, Zhipu AI API calls
│  └─ models.py       # Currently empty, not yet in use
├─ frontend/
│  ├─ src/            # Vue 3 frontend source code
│  ├─ package.json    # Frontend dependencies and startup scripts
│  └─ vite.config.ts  # Vite configuration
└─ README.md
```

## Tech Stack

- Frontend: Vue 3, Vite, TypeScript, Pinia, Vue Router, Element Plus, Tailwind CSS, DaisyUI
- Backend: Flask, Flask-CORS
- Large Model: Zhipu AI `zhipuai` SDK, model currently hardcoded as `glm-4`
- Export: Frontend uses `docx` to generate `.docx` files

## Main Features

### 1. Generate Full Exam

Entry: Frontend homepage `/index`

Features:

- Select target subject, major, course, or knowledge points.
- Input exam generation requirements.
- Set question type quantities:
  - Single-choice
  - Multiple-choice
  - Fill-in-the-blank
  - True/False
  - Short Answer
  - Advanced/Extension
- Click "Generate Random Requirements" to let the LLM generate a prompt based on the selected knowledge points.
- Click "Submit Requirements" to generate the full exam.
- Click "Continue Generating" to generate more questions based on the existing ones. The backend sends the existing questions to the model, instructing it to avoid duplicates.
- Click "Export Word" to export the current questions to `.docx`.
- Click "Clear All" to clear the current question results.
- Click "Switch to Single Question" to go to the single question page.

Corresponding backend endpoints:

- `POST /api/requirement2`: Generates random exam requirements.
- `POST /api/whole`: Generates the full exam.
- `GET /api/whole`: Health check, returns "AI assistant is running".

### 2. Generate Single Question

Entry: Frontend `/index2`

Features:

- Select target subject, question type, and difficulty level.
- Supported question types:
  - Single-choice
  - Multiple-choice
  - Fill-in-the-blank
  - True/False
  - Short Answer
- Supports difficulty levels 1 to 5, mapped by the backend as:
  - 1: Very Easy
  - 2: Easy
  - 3: Normal
  - 4: Hard
  - 5: Very Hard
- Click "Generate Random Requirements" for the LLM to generate the prompt and scope.
- Click "Submit Requirements" to generate a single question.
- The generated result is split into:
  - Prompt / Question Stem
  - Answer Explanation
  - Grading Rubric
- Click "Export Word" to export the single question, explanation, and rubric to `.docx`.
- Click "Switch to Full Exam" to return to the full exam page.

Corresponding backend endpoints:

- `POST /api/requirement`: Generates random single question requirements.
- `POST /api/single`: Generates a single question.

### 3. AI Evaluation and AI Chat

The backend has two endpoints already implemented:

- `POST /api/check`: Scores, evaluates, and provides suggestions based on the current question and user answer.
- `POST /api/chat`: Continues the conversation with the model regarding the current question.

However, the related UI in `AnswerPage.vue` on the frontend is currently commented out, so the "Submit Answer" and "AI Chat" buttons are hidden by default. To restore them, uncomment the corresponding template code in `frontend/src/components/AnswerPage.vue`.

### 4. Login/Register Pages

Entry: `/login`

Current Status:

- Login, register, and password recovery pages are mostly frontend UI.
- Actual requests to `/api/login`, `/api/register`, and `/api/forget` are commented out.
- The backend has not implemented these user endpoints.

Therefore, there is no actual user system in the project currently.

### 5. Reference File Upload

The frontend has a "Select File" button supporting:

- `.pdf`
- `.doc`
- `.docx`
- `.jpg`
- `.png`
- `.jpeg`

However, `POST /api/postlib` is not implemented on the backend yet, so files are not processed or used for question generation. This feature is currently incomplete.

## How to Run

Both backend and frontend need to be started.

### 1. Start Backend

Navigate to the backend directory:

```bash
cd backend
```

Install Python dependencies:

```bash
pip install flask flask_cors zhipuai
```

Start Flask:

```bash
python app.py
```

Default backend address:

```text
http://localhost:5000
```

### 2. Start Frontend

Navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
pnpm install
```

Start dev server:

```bash
pnpm dev
```

Vite will output the access address by default, usually:

```text
http://localhost:5173
```

Open the address to start using it.

## Where to Change the API Key

Large model configuration is in:

```text
backend/app.py
```

The current code has this line at the top:

```python
client = ZhipuAI(api_key="这里是你的智谱 API Key")
```

Replace the string with your own Zhipu AI API Key.

Currently, all large model endpoints use:

```python
model="glm-4"
```

To change the model, search for `model="glm-4"` in `backend/app.py` and replace them with the new model name.

Affected endpoints include:

- `/api/requirement`
- `/api/requirement2`
- `/api/single`
- `/api/check`
- `/api/chat`
- `/api/whole`

Note: The API Key is currently hardcoded, which is not suitable for public repositories or production environments. It is recommended to change it to read from environment variables, e.g.:

```python
import os

client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
```

Then set it locally:

```bash
set ZHIPUAI_API_KEY=你的key
```

PowerShell can use:

```powershell
$env:ZHIPUAI_API_KEY="你的key"
```

## Frontend/Backend Address Configuration

The frontend request address is currently hardcoded to:

```text
http://localhost:5000
```

Mainly distributed in these files:

- `frontend/src/components/QuestionPage.vue`
- `frontend/src/components/WholePage.vue`
- `frontend/src/components/AnswerPage.vue`
- `frontend/src/components/question/DocUpload.vue`
- `frontend/src/utils/requests.ts`

If the backend port or deployment address changes, update `http://localhost:5000` in these locations to the new backend address.

## Backend API Documentation

### `POST /api/requirement`

Generates random requirements for a single question.

Request fields:

- `target`: Array of target knowledge point paths.
- `type`: Question type (e.g., `Single-choice`, `Multiple-choice`, `Fill-in-blank`, `True/False`, `Short-answer`).
- `difficult`: Difficulty level, 1 to 5.

Response:

- Streaming text.

### `POST /api/single`

Generates a single question.

Request fields:

- `target`
- `type`
- `difficult`
- `questionNeed`

Response JSON:

```json
{
  "info": "success",
  "message": "模型生成的题目、答案解析和评分标准"
}
```

The frontend relies on the model output containing:

- `Answer Explanation:`
- `Grading Rubric:`

If the model does not output in this format, the frontend may fail to parse the results.

### `POST /api/check`

Generates scoring and evaluation based on the current single question and user answer.

Request fields:

- `message`: User answer.

Response:

- Streaming text.

Note: It relies on the backend global variable `title_info`, which is the question generated by the most recent `/api/single`.

### `POST /api/chat`

Continues the conversation around the current single question.

Request fields:

- `message`: User input.

Response:

- Streaming text.

Note: Also relies on the backend global variable `title_info`.

### `POST /api/requirement2`

Generates random requirements for the full exam.

Request fields:

- `target`: Array of selected target knowledge point paths.

Response:

- Streaming text.

### `POST /api/whole`

Generates the complete exam paper.

Request fields:

- `target`: Target knowledge point path array.
- `questionNeed`: Full exam requirements.
- `num1`: Number of single-choice questions.
- `num2`: Number of multiple-choice questions.
- `num3`: Number of fill-in-the-blank questions.
- `num4`: Number of true/false questions.
- `num5`: Number of short answer questions.
- `num6`: Number of advanced questions.
- `existing`: Text of existing questions on the page, used to prompt the model to avoid duplicates.

Response:

- Streaming text, which the frontend will render using Markdown.

## Current Limitations & Notes

- The project core relies on prompt engineering; there is no database or true user permission system.
- API Key is written in `backend/app.py`; it is recommended to change it to an environment variable.
- Frontend request addresses are hardcoded to `http://localhost:5000` in multiple places.
- Endpoints like `/api/postlib`, login, register, and password recovery lack backend implementation.
- `/api/check` and `/api/chat` rely on the backend global variable `title_info`, which will overwrite context when used by multiple people simultaneously.
- Single question result parsing relies on the model strictly outputting `Answer Explanation:` and `Grading Rubric:`. If the model's format drifts, the frontend may fail to parse.
- Full exam generation uses streaming output; content is only stored in the browser session, so refreshing the page will lose the data.

## FAQ

### Frontend page opens, but generation fails

Check if the backend is running:

```text
http://localhost:5000
```

If not running, frontend requests will fail.

### Backend startup reports `No module named flask`

Install dependencies:

```bash
pip install flask flask_cors zhipuai
```

### Reports API-related errors when generating questions

Check:

- Whether the Zhipu API Key in `backend/app.py` is valid.
- Whether the current model name `glm-4` is still available.
- Whether the network can access the Zhipu AI service.

### Clicking file upload fails

This is the expected current state. The frontend UI for upload is written, but the backend lacks the `/api/postlib` endpoint, which will be added later.
