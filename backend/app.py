from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from zhipuai import ZhipuAI

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

client = ZhipuAI(api_key="557c1b1736b88908bc81eeba0b8f46ee.atOnzh84zSgaRzSx")  # 请填写您自己的APIKey
system_basic_info1 = """
你是智能出题系统，请根据我为你提供的基础信息进行出题。你需要明确不同年级、不同科目、不同知识点的出题要求，以及出题的难度等级和出题类型。
对于每一道题请以严格的格式进行区分。
题目请以'题目要求：'为开头，如果是单选题和多选题的话，请以'题干：'为开头，以'A.选项1'、'B.选项2'、'C.选项3'、'D.选项4'等格式进行选项的描述。
同时提供答案解析，请以'答案解析：'为开头。
"""
difficulties = {'1': '非常简单', '2': '简单', '3': '正常', '4': '较难', '5': '困难'}
title_types = {'单选': '单选题', '多选': '多选题', '填空': '填空题', '判断': '判断题', '解答': '解答题'}
title_info = ''
system_basic_info2 = """
你是智能出题系统，此时你已得知题目需求以及用户答案，请为用户的答案进行评分评价和建议
"""
system_basic_info3 = """
你是智能出题系统，请根据我为你提供的基础信息进行出题。你需要明确不同年级、不同科目、不同知识点的出题要求，以及出题的难度等级和出题类型。
"""


def generate_stream(ai_response):
    try:
        for chunk in ai_response:
            # Simulating a delay for each message chunk
            yield f"{chunk.choices[0].delta.content}"
    except GeneratorExit:
        print("Client disconnected")


@app.route('/api/single', methods=['POST'])
def single_chat():
    global title_info
    data = request.json
    tt = data.get('type')
    title_type = title_types.get(tt)
    dd = data.get('difficult')
    difficult = difficulties.get(str(dd))
    need = data.get('questionNeed')
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
    print(title_info)
    return jsonify({'info': 'success', 'message': title_info}), 200


@app.route('/api/check', methods=['POST'])
def check_chat():
    global title_info
    data = request.json
    user_message = data.get('message')
    whole_info = '题目为：' + title_info + '。用户答案是：' + user_message
    ai_response = client.chat.completions.create(
        model="glm-4",
        messages=[
            {"role": "system", "content": system_basic_info2},
            {"role": "user", "content": whole_info}
        ],
        stream=True,
    )
    return Response(generate_stream(ai_response), content_type='text/event-stream')


@app.route('/api/whole', methods=['GET', 'POST'])
def ai_assistant():
    if request.method == 'GET':
        return jsonify({'success': True, 'message': 'AI assistant is running'})
    else:
        data = request.json
        user_message = data.get('message')
        # 使用智谱AI的API进行消息处理
        ai_response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "system", "content": system_basic_info3},
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
