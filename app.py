from threading import Lock
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from service.ChatService.ChatService import ChatService
from service.UploadService.FileUpLoadService import FileUpLoadService
from service.RAGFlowService.RAGFlowClient import RAGFlowClient
from service.ModelsService.SiliconService import SiliconService
from utils.Pagination import Pagination
import requests
from threading import Semaphore


app = Flask(__name__)
CORS(app)

concurrency_limiter = Semaphore(4)

@app.route('/chat', methods=['POST'])
def chat_api():
    '''聊天接口'''
    if not concurrency_limiter.acquire(blocking=False):
        return jsonify({
            "error": "system bussy, pls wait"
        }), 503
    try:
        data = request.get_json()
        user_input = data.get('msg')
        call_mode = data.get('modelType')
        session_id = data.get("session_id")
        # file_ids = data.get('fileIds',None)
        # dataset_ids = data.get('datasetIds',None)

        chat_service = ChatService()
        # chat = chat_service.ragflow.client.list_chats(id=data.get('chat_id'))[0]
        # session = chat.list_sessions(id=data.get('session_id'))[0]

        # 默认使用知识库进行问答
        # 先获取datasetids和fileids
        dataset_ids, file_ids = RAGFlowClient().get_all_ids()
        if dataset_ids and file_ids:
            # print(f"文档的个数：{len(file_ids)}")
            # print(f"知识库的个数：{len(dataset_ids)}")
            chat_service.enable_rag_mode(dataset_ids=dataset_ids, file_ids=file_ids)

        if not user_input:
            return jsonify({"error": "User_input are required"}), 400
        
        chat_service.query=user_input


        def generate():
            try:
                if call_mode == 'local':
                    cnt = 0
                    for response_chunk in chat_service.handle_local_call(session_id):
                        cnt+=1
                        print("===========================",cnt)
                        yield response_chunk
                    # last_index=0
                    # for response in chat_service.chat(data,session):
                    #     current_content = response.content
                    #     response_chunk = current_content[last_index:]
                    #     last_index = len(current_content)
                    #     if(response_chunk=="##0$$。"):
                    #         continue
                    #     print(response_chunk, end='', flush=True)
                    #     yield response_chunk
                elif call_mode == 'cloud':
                    for response_chunk in chat_service.handle_cloud_call():
                        yield response_chunk
                else:
                    yield jsonify({"error": "Invalid call mode"})
                
                # 保存AI回复到上下文
                # chat_service.messages.append({'role': 'assistant', 'content': response_chunk})
            finally:
                # 释放锁
                concurrency_limiter.release()

        headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }

        return Response(stream_with_context(generate()), headers=headers)
    except Exception as e:
        concurrency_limiter.release()
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/datasets', methods=['POST'])
def handle_dataset_create():
    '''知识库创建接口'''
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
    '''文档上传接口'''
    dataset_id = request.form.get('dataset_id')     # 安全监控系统的systemId=0
    upload_service = FileUpLoadService()
    file = request.files['file']
    # print("===================================="+file.filename)
    response, status_code = upload_service.upload_file(file, dataset_id)
    return jsonify(response),status_code

@app.route('/delete_files', methods=['POST'])
def handle_files_delete():
    '''文档删除接口'''
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

@app.route('/datasets/list', methods=['POST'])
def handle_datasets_list():
    '''知识库列表接口'''
    try:
        data = request.get_json()
        page, per_page = Pagination.validate_params(data)
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400

    upload_service = FileUpLoadService()
    datasets, err, total_datasets = upload_service.list_datasets(
        data.get("name"),
        page,
        per_page
    )
    
    if err:
        return jsonify({"status": "error", "error": err}), 500
    return jsonify({
        "status": "success",
        "datasets": datasets,
        "total_datasets": total_datasets
    })
    

@app.route('/dataset',methods=['GET'])
def handle_dataset_config():
    """展示数据库配置"""
    ragflow_client = RAGFlowClient()
    dataset_id = request.args.get("dataset_id")
    return jsonify({
        "status": "success",
        "config": ragflow_client.show_dataset_config(dataset_id=dataset_id)
    }), 200

@app.route('/files/list', methods=['POST'])
def handle_files_list():
    '''文档列表接口'''
    try:
        data = request.get_json()
        page, per_page = Pagination.validate_params(data)
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400

    upload_service = FileUpLoadService()
    files, err, total_files = upload_service.list_files(
        data.get("dataset_id"),
        data.get("name"),
        page,
        per_page
    )
    
    if err:
        return jsonify({"status": "error", "error": err}), 500
    return jsonify({
        "status": "success",
        "files": files,
        "total_files": total_files
    })

@app.route('/files/parse', methods=["POST"])
def handle_files_parse():
    '''文档解析接口'''
    data = request.get_json()
    file_ids = data.get("file_ids")  # 数组类型
    dataset_id = data.get("dataset_id")

    upload_service = FileUpLoadService()
    res, err = upload_service.parse_files(file_ids,dataset_id)

    if not res:
        return jsonify({
            "status": "error",
            "message": f"文件解析失败: {str(err)}"
        }),500
    else:
        return jsonify({
            "status": "sucess",
            "message": "文件正在解析"
        }),200

@app.route('/files/unparse', methods=['POST'])
def handle_files_parse_cancel():
    '''停止文档解析'''
    data = request.json

    ragflow_client = RAGFlowClient()

    res, err = ragflow_client.stop_parse_file(data.get("document_ids"), data.get("dataset_id"))
    if not res:
        return jsonify({
            "status": "error",
            "message": f"文档停止解析失败: {str(err)}"
        }), 500
    else:
        return jsonify({
            "status": "success",
            "message": f"文档已停止解析"
        }), 200
    
@app.route('/files/parse_status', methods=['POST'])
def handle_files_parse_status():
    '''获取文档解析状态'''
    data = request.json
    ragflow_client = RAGFlowClient()
    res, err = ragflow_client.get_parse_status(data.get("dataset_id"), data.get("file_id"))
    if err:
        return jsonify({
            "status": "error",
            "message": f"获取解析状态失败: {str(err)}"
        }), 500
    else:
        return jsonify({
            "status": "success",
            "message": "成功获取文档解析状态",
            "parse_status": res
        }), 200



@app.route('/dataset', methods=['POST'])
def handle_dataset_update():
    '''知识库配置更新接口'''
    data = request.json

    try:
        ragflow_client = RAGFlowClient()
        if ragflow_client.update_dataset(data):
            return jsonify({'message': 'update success'}),200
        else:
            return jsonify({'message': 'file already have been parsed, update failed'}),409
    except Exception as e:
        return jsonify({'error': f'update failed: {str(e)}'}), 500    
    
@app.route('/file', methods=['POST'])
def handle_file_update():
    '''文档配置更新接口'''
    data = request.json
    ragflow_client = RAGFlowClient()
    res, e = ragflow_client.update_file(data)
    if res:
        return jsonify({'message': '文档配置更新成功'}),200
    else:
        return jsonify({'error': f'文档配置更新失败:{str(e)}'}), 500

@app.route('/dataset/retrieve', methods=['POST'])
def handle_retrieve_test():
    '''检索测试接口'''
    data = request.json
    ragflow_client = RAGFlowClient()

    dataset_id = data.get("dataset_id")
    file_ids = data.get("file_ids")
    query = data.get("query")
    similarity_threshold = data.get("similarity_threshold")
    vector_similarity_weight = data.get("vector_similarity_weight")
    rerank_id = data.get("rerank_id")
    top_k = data.get("top_k")

    try:
        contexts = ragflow_client.search(
            dataset_ids=[dataset_id], 
            query=query,
            document_ids=file_ids, 
            similarity_threshold=similarity_threshold,
            vector_similarity_weight=vector_similarity_weight,
            rerank_id=rerank_id,
            top_k=top_k
            )
        knowledge = '\n'.join([f'[片段{i+1}] {ctx}' for i,ctx in enumerate(contexts)])
        print(knowledge)
        return jsonify({
            "message": "检索成功",
            "chunks": contexts
        }),200
    except Exception as e:
        print(e)
        return jsonify({
            "message": "检索失败",
            "error": f"{str(e)}"
        }),500


@app.route('/file/chunks',methods=['POST'])
def handle_chunks_list():
    """显示当前文档的所有块"""
    data = request.get_json()
    page, per_page = Pagination.validate_params(data)
    dataset_id = data.get('dataset_id')
    file_id = data.get('file_id')
    ragflow_client = RAGFlowClient()
    try:
        chunks, chunk_cnt = ragflow_client.list_chunks(dataset_id, file_id, page, per_page)
        print(len(chunks))
        
        return jsonify({
        "status": "success",
        "chunks": [str(chunk) for chunk in chunks],
        "total_chunks": chunk_cnt
        })
    except Exception as e:
        return jsonify({
            "message": "error",
            "error": f"{str(e)}"
        }),500




@app.route('/models',methods=['POST'])
def handle_available_models():
    """模型列表"""
    silicon = SiliconService()
    headers = {"Authorization": f"Bearer {silicon.api_key}"}
    data = request.get_json()
    sub_type = data.get("sub_type")
    params = {
        "sub_type": sub_type
    }
    try:
        res = requests.get(url=silicon.url, headers=headers, params=params)
        res.raise_for_status()  # 检查响应状态码，如果不是 200 则抛出异常
        models_data = res.json()  # 将响应内容解析为 JSON 格式
        return jsonify({
            "status": "success",
            "models": models_data
        })
    except requests.exceptions.RequestException as e:
        return jsonify({
            "message": "error",
            "error": f"请求出错：{str(e)}"
        })
    except ValueError as e:
        return jsonify({
            "message": "error",
            "error": f"解析响应内容出错：{str(e)}"
        })
    except Exception as e:
        return jsonify({
            "message": "error",
            "error": f"获取模型出错：{str(e)}"
        })
    
@app.route('/sessions', methods=['POST'])
def handle_sessions_create():
    """创建会话"""
    data = request.get_json()
    chat_service = ChatService()

    session_id, err = chat_service.create_session(data.get("user_id"), data.get("platform"))
    if err:
        return jsonify({
            "status": "error",
            "error": f"创建会话失败: {err}"
        }), 500
    else:
        return jsonify({
            "status": "success",
            "session_id": session_id
        }), 200


@app.route('/sessions/list', methods=['POST'])
def handle_sessions_list():
    """列出会话列表"""
    data = request.get_json()
    chat_service = ChatService()

    sessions, err = chat_service.list_sessions(data.get("user_id"),data.get("platform"))

    if err:
        return jsonify({
            "status": "error",
            "error": f"获取会话列表失败: {err}"
        }), 500
    else:
        return jsonify({
            "status": "success",
            "sessions": sessions
        }), 200
    
@app.route('/sessions/delete', methods=['POST'])
def handle_sessions_delete():
    """删除会话"""
    data = request.get_json()
    chat_service = ChatService()

    try:
        chat_service.delete_sessions(data.get("session_id"))
        return jsonify({
            "status": "success",
            "message": f"成功删除会话"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"删除失败: {e}"
        }), 500



    
@app.route('/session/dialogs/list', methods=['POST'])
def handle_dialogs_list():
    """列出当前会话中的所有对话"""
    data = request.get_json()
    chat_service = ChatService()

    dialogs, err = chat_service.list_dialogs(data.get("session_id"))

    if err:
        return jsonify({
            "status": "error",
            "error": f"获取全部对话失败: {err}"
        }), 500
    else:
        return jsonify({
            "status": "success",
            "sessions": dialogs
        }), 200


@app.route('/data', methods=['POST'])
def handle_data_transmission():
    """接收数据传输"""
    file = request.files['file']

    upload_service = FileUpLoadService()

    save_path, _ = upload_service._save_file(file,file.name)
    print(save_path)

    return jsonify({
        "status": "success",
        "save_path": save_path
    })










# @app.route('/assistant', methods=['POST'])
# def handle_assistant_create():
#     """创建聊天助手"""
#     data =  request.json
#     try:
#         chat_service = ChatService()
#         assistant = chat_service.create_chat(data)
#         return jsonify({"message":"聊天助手创建成功！"}),200
#     except Exception as e:
#         return jsonify({"message": f"聊天助手创建失败： {str(e)}"}),500 



# @app.route('/assistant', methods=['DELETE'])
# def handle_assistant_delete():
#     """删除聊天助手"""
#     data = request.json
#     try:
#         chat_service = ChatService()
#         chat_service.delete_chat(data)
#         return jsonify({"message":"聊天助手删除成功！"}),200
#     except Exception as e:
#         return jsonify({"message": f"聊天助手删除失败： {str(e)}"}),500  
    
# @app.route('/assistant', methods=['PUT'])
# def handle_assistant_update():
#     """更新聊天助手"""
#     data = request.json
#     try:
#         chat_service = ChatService()
#         chat_service.update_chat(data)
#         return jsonify({"message":"聊天助手更新成功！"}),200
#     except Exception as e:
#         return jsonify({"message": f"聊天助手更新失败： {str(e)}"}),500  
    
# @app.route('/assistant', methods=['GET'])
# def handle_assistant_list():
#     """查找聊天助手"""
#     try:
#         chat_service = ChatService()
#         chat_ids = chat_service.list_chats()
#         return jsonify({"message":"查找聊天助手成功！",
#                         "chat_ids": chat_ids}),200
#     except Exception as e:
#         return jsonify({"message": f"查找聊天助手失败： {str(e)}"}),500  
    
# @app.route('/session', methods=['POST'])
# def handle_session_create():
#     """创建与聊天助手的会话"""
#     data = request.json
#     try:
#         chat_service = ChatService()
#         session_id = chat_service.create_session(data)
#         return jsonify({"message":"创建会话成功！",
#                         "session_id": session_id}),200
#     except Exception as e:
#         return jsonify({"message": f"创建会话失败： {str(e)}"}),500

# @app.route('/session', methods=['PUT'])
# def handle_session_update():
#     """更新与聊天助手的会话"""
#     data = request.json
#     try:
#         chat_service = ChatService()
#         chat_service.update_session(data)
#         return jsonify({"message":"更新会话成功！"}),200
#     except Exception as e:
#         return jsonify({"message": f"更新会话失败： {str(e)}"}),500
    
# @app.route('/session', methods=['GET'])
# def handle_session_list():
#     """查找与聊天助手的会话"""
#     data = request.json
#     try:
#         chat_service = ChatService()
#         session_ids = chat_service.list_session(data)
#         return jsonify({"message":"查找会话成功！", "session_ids":session_ids}),200
#     except Exception as e:
#         return jsonify({"message": f"查找会话失败： {str(e)}"}),500

# @app.route('/session', methods=['DELETE'])
# def handle_session_delete():
#     """删除与聊天助手的会话"""
#     data = request.json
#     try:
#         chat_service = ChatService()
#         chat_service.delete_session(data)
#         return jsonify({"message":"删除会话成功！"}),200
#     except Exception as e:
#         return jsonify({"message": f"删除会话失败： {str(e)}"}),500
    
# @app.route('/chat2', methods=['POST'])
# def handle_chat():
#     data = request.json
#     chat_service = ChatService()
#     chat = chat_service.ragflow.client.list_chats(id=data.get('chat_id'))[0]
#     session = chat.list_sessions(id=data.get('session_id'))[0]

#     def generate():
#         try:
#             # cont = ""
#             # for response in chat_service.chat(data,session):
#             #     print(response.content[len(cont):], end='', flush=True)
#             #     cont = response.content
#             #     # yield response.content
#             last_index=0
#             for response in chat_service.chat(data,session):
#                 current_content = response.content
#                 new_content = current_content[last_index:]
#                 last_index = len(current_content)
#                 if(new_content=="##0$$。"):
#                     continue
#                 print(new_content, end='', flush=True)
#                 yield new_content
#         except Exception as e:
#             raise 

#     # headers = {
#     #     'Content-Type': 'text/event-stream',
#     #     'Cache-Control': 'no-cache',
#     #     'X-Accel-Buffering': 'no',
#     # }
#     return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True,port=5000,host='0.0.0.0')