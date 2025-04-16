from vanna.ollama import Ollama
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)


vn = MyVanna(config={'model':'deepseek-r1:1.5b'})

vn.connect_to_mysql(host='172.16.49.81', dbname='shh-safety-monitor-his', user='root', password='root', port=3306)

df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")

plan = vn.get_training_plan_generic(df_information_schema)

print(plan)




















# from langchain_community.utilities import SQLDatabase
# from langchain_ollama import OllamaLLM
# from sqlalchemy import create_engine, text
# from operator import itemgetter
# from config.config_loader import config
# from langchain_community.tools import QuerySQLDataBaseTool
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import PromptTemplate
# from langchain.chains.sql_database.query import create_sql_query_chain
# class SQLQueryAgent:
#     def __init__(self):
#         self.engine = create_engine(
#             'mysql+pymysql://root:root@172.16.49.81:3306/shh-safety-monitor-his'
#         )
#         self.db = SQLDatabase(engine=self.engine)
#         self.llm = OllamaLLM(model=config.database.llm, base_url=config.model.local.ollama_url, num_predict=2048, top_k=10)
#         self.execute_query = QuerySQLDataBaseTool(db=self.db)
#         # tookit = SQLDatabaseToolkit(db=self.db,llm=self.llm)

#         self.sql_chain = create_sql_query_chain(llm=self.llm,db=self.db)

#         self.answer_prompt = PromptTemplate.from_template(
#     """“给出以下用户问题、相应的 SQL 查询和 SQL 结果，回答用户问题。

# 问题：{question}
# SQL 查询：{query}
# SQL 结果：{result}
# 答案："""
# )
#         self.chain = (
#             RunnablePassthrough.assign(query=self.sql_chain).assign(
#                 result=itemgetter("query") | self.execute_query
#             )
#             | self.answer_prompt
#             | self.llm
#             | StrOutputParser()  
#         )
    
#     def run(self, user_input):
#         with self.engine.connect() as conn:
#             result = conn.execute(text("SHOW TABLES;"))
#             print("实际表列表:", [row[0] for row in result])
#         input_dict = {"question": user_input}
#         result = self.chain.invoke(input_dict)
#         return result
        # try:
        #     sql_query = self.agent_executor.invoke(f"生成SQL查询以{user_input}，但不要执行它")

        #     # 提取SQL语句（假设输出格式为 ```sql ... ```）
        #     if '```sql' in sql_query:
        #         start = sql_query.find('```sql') + len('```sql')
        #         end = sql_query.find('```', start)
        #         sql_statement = sql_query[start:end].strip()

        #         # 直接执行提取的SQL查询
        #         result = self.db.run(sql_statement)
        #         print("查询结果:", result)
        #     else:
        #         print("未能从LLM输出中提取有效的SQL语句。")
        # except Exception as e:
        #     print(f"发生错误: {e}")
        #     if 'Could not parse LLM output' in str(e):
        #         print("提示：模型输出无法解析，请尝试更明确的查询语句。")       
        # return result
