from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from service.ChatService import chat_service

app = Flask(__name__)
CORS(app)
chat_service = chat_service.ChatService()


@app.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    user_input = data.get('user_input')
    call_mode = data.get('call_mode')
    if not user_input:
        return jsonify({"error": "User_input are required"}), 400
    chat_service.messages.append({'role': 'user', 'content': user_input})

    def generate():
        if call_mode == 'local':
            for response_chunk in chat_service.handle_local_call():
                yield response_chunk
        elif call_mode == 'cloud':
            for response_chunk in chat_service.handle_cloud_call():
                yield response_chunk
        else:
            yield jsonify({"error": "Invalid call mode"})
        
        # 保存AI回复到上下文
        chat_service

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }

    return Response(stream_with_context(generate()), mimetype='text/event-stream', headers=headers)


if __name__ == '__main__':
    app.run(debug=True,port=5000,host='0.0.0.0')