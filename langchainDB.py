from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain import hub
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

llm = OllamaLLM(model="deepseek-r1:14b", base_url="http://172.16.49.9:11434")
db = SQLDatabase.from_uri("mssql+pyodbc://sa:3Shine%40123456@localhost:1433/KJ70N?driver=ODBC+Driver+17+for+SQL+Server")

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

tools = toolkit.get_tools()

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")

assert len(prompt_template.messages) == 1
prompt_template.messages[0].pretty_print()

system_message = prompt_template.format(dialect="SQL Server", top_k=5)

agent_executor = create_react_agent(llm,tools,prompt=system_message)

question = "最近一次报警什么时候？"

for step in agent_executor.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()