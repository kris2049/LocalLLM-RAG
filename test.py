from service.RAGFlowService import RAGFlowClient
ragflow = RAGFlowClient.RAGFlowClient()

agent = ragflow.client.list_agents()[0]
print(agent.id)
session = agent.list_sessions()[0]

print("\n===== Miss R ====\n")
print("Hello. What can I do for you?")

while True:
    question = input("\n===== User ====\n> ")
    print("\n==== Miss R ====\n")
    
    cont = ""
    for ans in session.ask(question, stream=True):
        print(ans.content[len(cont):], end='', flush=True)
        cont = ans.content