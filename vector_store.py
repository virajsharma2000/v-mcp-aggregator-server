import pinecone
import os
from sentence_transformers import SentenceTransformer
from uuid import uuid4

class ToolVectorDB:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_env = os.getenv("PINECONE_ENVIRONMENT")
        index_name = os.getenv("PINECONE_INDEX_NAME", "mcp-tools")

        pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)

        if index_name not in pinecone.list_indexes():
            pinecone.create_index(index_name, dimension=384)

        self.index = pinecone.Index(index_name)

    def add_tool(self, name: str, description: str, endpoint: str):
        vector = self.model.encode(description).tolist()
        metadata = {
            "name": name,
            "description": description,
            "endpoint": endpoint
        }
        self.index.upsert([(str(uuid4()), vector, metadata)])

    def search_tools(self, query: str, top_k: int = 3):
        vector = self.model.encode(query).tolist()
        results = self.index.query(vector=vector, top_k=top_k, include_metadata=True)
        return [match.metadata for match in results.matches]
