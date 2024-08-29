from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from zhipuai import ZhipuAI

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

client = ZhipuAI(api_key="557c1b1736b88908bc81eeba0b8f46ee.atOnzh84zSgaRzSx")  # 请填写您自己的APIKey
# 出单个题
system_basic_info1 = """
你是智能出题系统，请根据我为你提供的基础信息进行出题。你需要明确不同年级、不同科目、不同知识点的出题要求，以及出题的难度等级和出题类型。
对于每一道题请以严格的格式进行区分。
题目请以'题目要求：'为开头，如果是单选题和多选题的话，请以'题干：'为开头，以'A.选项1'、'B.选项2'、'C.选项3'、'D.选项4'等格式进行选项的描述。
同时提供答案解析和评分标准，请分别以'答案解析：'和'评分标准：'为开头。
"""
difficulties = {'1': '非常简单', '2': '简单', '3': '正常', '4': '较难', '5': '困难'}
title_types = {'单选': '单选题', '多选': '多选题', '填空': '填空题', '判断': '判断题', '解答': '解答题'}
title_info = ''
# 单个题目评分解析
system_basic_info2 = """
你是智能出题系统，此时你已得知题目需求以及用户答案，请为用户的答案进行评分评价和建议。
"""
# 单个题目的chat
system_basic_info3 = """
你是智能出题系统，默认得知了题目需求和结果，请根据用户发来的信息进行对话交流。
"""
# 成套题目的背景信息
system_basic_info4 = """
你是智能出题系统，你会得到我提供给你的相应年级的某学科考察的一些不同知识点，同时会得到为你提供的单选题、多选题、填空题、判断题、解答题和拔高题的数量需求，
你需要根据这些要求进行出题。对于单选、多选、填空、判断和解答题，请出正常及正常偏难的题目，对于拔高题请出非常困难的题目，不过拔高题可以是解答题也可以是其他类型
请根据需求依次给出题目和答案解析，同时需要题目序号。同时你也可能会得到一些已经存在了的题目，请不要重复出题。
"""

system_basic_info5 = """
你是智能出题系统，你会得到我提供给你的相关专业、学科和知识点组成的文本信息，请根据我提供给你的难度和题目类型为我生成合适的题目要求和目的，
这个并不是题目本身，而是一些背景条件和考察范围。
"""

system_basic_info6 = """
你是智能出题系统，你会得到我提供给你的相关专业、学科和知识点组成的文本信息，请根据我提供给你的多个知识点为我生成合适的题目要求和目的，
这个并不是题目本身，而是一些背景条件和考察范围。
"""


# 流式输出
def generate_stream(ai_response):
    try:
        for chunk in ai_response:
            # Simulating a delay for each message chunk
            yield f"{chunk.choices[0].delta.content}"
    except GeneratorExit:
        print("Client disconnected")


@app.route('/api/requirement', methods=['POST'])
def auto_requirement():
    data = request.json
    # 类型
    tt = data.get('type')
    title_type = title_types.get(tt)
    # 难度
    dd = data.get('difficult')
    difficult = difficulties.get(str(dd))
    target = data.get('target')
    target_str = ''
    for i in target:
        target_str += i
    title_need = f"题目考察范围：{target_str}\n题目类型：{title_type}\n出题难度：{difficult}"
    ai_response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": system_basic_info5},
            {"role": "user", "content": title_need}
        ],
        stream=True,
    )
    return Response(generate_stream(ai_response), content_type='text/event-stream')


@app.route('/api/requirement2', methods=['POST'])
def auto_requirement2():
    data = request.json
    target = data.get('target')
    print(target)
    target_set = []
    for i in range(len(target)):
        for j in target[i]:
            if j not in target_set:
                target_set.append(j)
    target_str = ''
    for i in target_set:
        target_str += i + '、'
    ai_response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": system_basic_info6},
            {"role": "user", "content": target_str}
        ],
        stream=True,
    )
    return Response(generate_stream(ai_response), content_type='text/event-stream')


# 生成单个题的API
@app.route('/api/single', methods=['POST'])
def single_chat():
    global title_info
    data = request.json
    # 类型
    tt = data.get('type')
    title_type = title_types.get(tt)
    # 难度
    dd = data.get('difficult')
    difficult = difficulties.get(str(dd))
    # 题目要求
    need = data.get('questionNeed')
    # 年级、学科、知识点
    target = data.get('target')
    target_str = ''
    for i in target:
        target_str += i
    title_need = f"题目考察范围：{target_str}\n题目类型：{title_type}\n出题难度：{difficult}\n题目要求：{need}"
    ai_response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": system_basic_info1},
            {"role": "user", "content": title_need}
        ],
    )
    title_info = ai_response.choices[0].message.content
    return jsonify({'info': 'success', 'message': title_info}), 200


# 直接获得分析的结果，非对话
@app.route('/api/check', methods=['POST'])
def check_chat():
    global title_info
    data = request.json
    user_message = data.get('message')
    ai_response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": system_basic_info2 + '。题目信息是：' + title_info},
            {"role": "user", "content": user_message}
        ],
        stream=True,
    )
    return Response(generate_stream(ai_response), content_type='text/event-stream')


# 对话
@app.route('/api/chat', methods=['POST'])
def chat():
    global title_info
    data = request.json
    user_message = data.get('message')
    ai_response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": system_basic_info3 + '。题目信息是：' + title_info},
            {"role": "user", "content": user_message}
        ],
        stream=True,
    )
    return Response(generate_stream(ai_response), content_type='text/event-stream')


generation_state = {}


# 给出套题
@app.route('/api/whole', methods=['GET', 'POST'])
def ai_assistant():
    if request.method == 'GET':
        return jsonify({'success': True, 'message': 'AI assistant is running'})
    else:
        data = request.json
        need = data.get('questionNeed')
        num1 = data.get('num1')
        num2 = data.get('num2')
        num3 = data.get('num3')
        num4 = data.get('num4')
        num5 = data.get('num5')
        num6 = data.get('num6')
        title_type = f"{num1}道单选题、{num2}道多选题、{num3}道填空题、{num4}道判断题、{num5}道解答题、{num6}道拔高题"
        target = data.get('target')
        existing = data.get('existing')
        print(target)
        target_set = []
        for i in range(len(target)):
            for j in target[i]:
                if j not in target_set:
                    target_set.append(j)
        target_str = ''
        for i in target_set:
            target_str += i + '、'
        user_message = f"请忘记之前的相关内容。题目考察范围：{target_str}\n题目所需类型及数量：{title_type}\n题目要求：{need}\n已有题目：{existing}"
        ai_response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "system", "content": system_basic_info4},
                {"role": "user", "content": user_message}
            ],
            stream=True,
        )
        return Response(generate_stream(ai_response), content_type='text/event-stream')


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run(debug=True)
