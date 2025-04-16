from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from service.ChatService.ChatService import ChatService
from service.UploadService.FileUpLoadService import FileUpLoadService
from utils.VectorDBClient import VectorDBClient

app = Flask(__name__)
CORS(app)


@app.route('/chat', methods=['POST'])
def chat_api():
    chat_service = ChatService()
    data = request.get_json()
    user_input = data.get('msg')
    call_mode = data.get('modelType')
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
        chat_service.messages.append({'role': 'assistant', 'content': response_chunk})

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

@app.route('/delete', methods=['DELETE'])
def handle_delete():
    data = request.get_json()
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({
            "status": "error",
            "message": "Missing file_id"
        }),400
    
    upload_service = FileUpLoadService()
    response, status_code = upload_service.delete_file(file_id)

    return jsonify(response), status_code


@app.route('/list_files', methods=['GET'])
def list_files():
    upload_service = FileUpLoadService()
    return jsonify({
        "status": "success",
        "files": upload_service.get_all_uploaded_files()
    })





if __name__ == '__main__':
    app.run(debug=True,port=5050,host='0.0.0.0')