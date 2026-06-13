# app/knowledge/retriever.py
class KnowledgeRetriever:
    def __init__(self, docs_directory: str = "./knowledge_base"):
        self.docs_directory = docs_directory

    async def retrieve_context(self, query: str) -> str:
        # Fase 1: Retorna vacío. En Fase 2 (RAG) se implementará la búsqueda en Markdowns.
        return ""
