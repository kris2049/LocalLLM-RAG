from threading import Lock
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from service.ChatService.ChatService import ChatService
from service.UploadService.FileUpLoadService import FileUpLoadService
from config.config_loader import config

app = Flask(__name__)
CORS(app)


ollama_lock = Lock() # 全局唯一锁

@app.route('/chat', methods=['POST'])
def chat_api():
    if not ollama_lock.acquire(blocking=False):
        return jsonify({
            "error": "系统繁忙，请等待"
        }), 503
    data = request.get_json()

    user_input = data.get('msg')
    call_mode = data.get('modelType')
    # file_ids = data.get('fileIds',None)
    # dataset_ids = data.get('datasetIds',None)

    chat_service = ChatService()

    # 如果传入了文件名，使用本地知识库
    if len(config.ragflow.retrieval.file_ids)>0:
        # print(f"文档的个数：{len(file_ids)}")
        # print(f"知识库的个数：{len(dataset_ids)}")
        chat_service.enable_rag_mode(dataset_ids=config.ragflow.retrieval.dataset_ids, file_ids=config.ragflow.retrieval.file_ids)

    if not user_input:
        return jsonify({"error": "User_input are required"}), 400
    
    chat_service.query=user_input


    def generate():
        try:
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
        except Exception as e:
            ollama_lock.release() # 异常的时候释放锁
            raise
        finally:
            # 释放锁
            ollama_lock.release()

    headers = {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
    }

    return Response(stream_with_context(generate()), mimetype='text/event-stream', headers=headers)

@app.route('/datasets', methods=['POST'])
def handle_dataset_create():
    data = request.get_json()
    dataset_name = data.get("systemName")
    upload_service = FileUpLoadService()
    if not upload_service.create_dataset(dataset_name):
        return jsonify({
            "status": "error",
            "message": "创建数据集失败"
        }), 500
    return jsonify({
        "status": "success",
        "message": "创建数据集成功"
    }), 200


@app.route('/upload', methods=['POST'])
def handle_upload():
    dataset_id = request.form['datasetId']     # 安全监控系统的systemId=0
    upload_service = FileUpLoadService()
    file = request.files['file']
    response, status_code = upload_service.upload_file(file, dataset_id)
    return jsonify(response),status_code

@app.route('/files', methods=['DELETE'])
def handle_files_delete():
    data = request.get_json()
    file_ids = data.get("file_ids")  # 数组类型
    dataset_id = data.get("dataset_id")

    if not file_ids:
        return jsonify({
            "status": "error",
            "message": "Missing file_id"
        }),400
    
    upload_service = FileUpLoadService()
    response, status_code = upload_service.delete_file(file_ids, dataset_id)

    return jsonify(response), status_code

@app.route('/datasets', methods=['GET'])
def handle_datasets_list():
    upload_service = FileUpLoadService()
    return jsonify({
        "status": "success",
        "datasets": upload_service.list_datasets()
    })

@app.route('/files', methods=['GET'])
def handle_files_list():
    data = request.get_json()
    dataset_id = data.get("dataset_id")
    upload_service = FileUpLoadService()
    return jsonify({
        "status": "success",
        "files": upload_service.list_files(dataset_id)
    })

@app.route('/files/parse', methods=["POST"])
def handle_files_parse():
    data = request.get_json()
    file_ids = data.get("file_ids")  # 数组类型
    dataset_id = data.get("dataset_id")

    upload_service = FileUpLoadService()
    res = upload_service.parse_files(file_ids,dataset_id)

    if not res:
        return jsonify({
            "status": "error",
            "message": "文件解析失败"
        }),500
    else:
        return jsonify({
            "status": "sucess",
            "message": "文件解析成功"
        }),200




if __name__ == '__main__':
    app.run(debug=True,port=5000,host='0.0.0.0')