import os
import shutil
from langchain_core.documents import Document
from config import Configuration
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

class ChromaManager:
    def __init__(self):
        self.db = Chroma(
            persist_directory=Configuration.CHROMA_PATH,
            embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        )

    def add_documents(self, documents: list[Document]):
        existing = self.db.get(include=[])
        existing_ids = set(existing["ids"])
        new_docs = [doc for doc in documents if doc.metadata["id"] not in existing_ids]
        new_ids = [doc.metadata["id"] for doc in new_docs]
        if new_docs:
            self.db.add_documents(new_docs, ids=new_ids)

    @staticmethod
    def clear_database():
        if os.path.exists(Configuration.CHROMA_PATH):
            shutil.rmtree(Configuration.CHROMA_PATH)