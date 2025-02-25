from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from service.ChatService.ChatService import ChatService
from service.UploadService.FileUpLoadService import FileUpLoadService

app = Flask(__name__)
CORS(app)


@app.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    user_input = data.get('user_input')
    call_mode = data.get('call_mode')
    if not user_input:
        return jsonify({"error": "User_input are required"}), 400
    ChatService.messages.append({'role': 'user', 'content': user_input})


    def generate():
        if call_mode == 'local':
            for response_chunk in ChatService.handle_local_call():
                yield response_chunk
        elif call_mode == 'cloud':
            for response_chunk in ChatService.handle_cloud_call():
                yield response_chunk
        else:
            yield jsonify({"error": "Invalid call mode"})
        
        # 保存AI回复到上下文
        ChatService

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }

    return Response(stream_with_context(generate()), mimetype='text/event-stream', headers=headers)

@app.route('/upload', methods=['POST'])
def handle_upload():
    upload_service = FileUpLoadService()
    file = request.files['file']
    response, status_code = upload_service.upload_file(file)
    return jsonify(response),status_code



if __name__ == '__main__':
    app.run(debug=True,port=5050,host='0.0.0.0')