#from llm import llm
from langchain.messages import SystemMessage
from memory_service import memory_service

from denpendancy import get_llm
from langchain_core.chat_history import InMemoryChatMessageHistory
llm = get_llm()
#history=InMemoryChatMessageHistory()
#REDIS
#from memory import memory_layer
#history = memory_layer._get_history("enterprise_session_001")
#from memory_service import memory_service
history = memory_service._history("enterprise_session_001")

history.add_message(
    SystemMessage(
        content="You are an enterprise AI assistant."
    )
)

print("ASK YOUR QUESTION:")
while True:
    user_input = input("ASK: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting the chat. Goodbye!")
        break
    #save user_input
    history.add_user_message(user_input)
     #Invoke model with full conversation history
    response = llm.invoke(history.messages)
    #save AI response
    history.add_ai_message(response.content)

    print(f"AI RESPONSE: {response.content}")
      #Display current token usage
    tokens = llm.get_num_tokens_from_messages(history.messages)
    if tokens > 1000:
        print(f"\nWarning: High token usage detected! Current tokens: {tokens}")
        history.clear()  # Clear history to manage token usage
    print(f"\nConversation Tokens: {tokens}\n")
print(history.messages )

