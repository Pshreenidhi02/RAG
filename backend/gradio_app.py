import gradio as gr

from userQuery.user_query import ask


def chat_with_rag(message, history):
    try:
        answer = ask(message)
        return answer

    except Exception as e:
        return f"Error: {str(e)}"


def create_gradio_app():

    demo = gr.ChatInterface(
        fn=chat_with_rag,
        title="RAG Assistant",
        description="Ask questions about the documents stored in the knowledge base."
    )

    return demo