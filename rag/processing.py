from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from config import settings

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

def get_embeddings(texts):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.gemini_api_key)
    return embeddings.embed_documents(texts)

def get_completion(query, context):
    chat = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.gemini_api_key)
    
    messages = [
        SystemMessage(content="You are a helpful assistant that answers questions based on the provided context."),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:")
    ]
    
    response = chat(messages)
    return response.content
