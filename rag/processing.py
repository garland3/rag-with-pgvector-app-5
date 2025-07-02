from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from config import settings

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

def get_embeddings(texts):
    embeddings = OpenAIEmbeddings(openai_api_key=settings.gemini_api_key)
    return embeddings.embed_documents(texts)
