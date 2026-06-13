# tests/test_retriever.py
import pytest
from app.knowledge.retriever import KnowledgeRetriever

@pytest.mark.asyncio
async def test_knowledge_retriever_empty():
    retriever = KnowledgeRetriever()
    context = await retriever.retrieve_context("consulta de manzanilla")
    assert context == ""
