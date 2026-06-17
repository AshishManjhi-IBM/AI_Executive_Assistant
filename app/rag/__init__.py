"""
RAG (Retrieval-Augmented Generation) Module

This module provides semantic search and retrieval capabilities for emails
using ChromaDB vector store and embeddings.
"""

from .email_store import EmailStore
from .vector_search import VectorSearch
from .retriever import EmailRetriever

__all__ = ['EmailStore', 'VectorSearch', 'EmailRetriever']

# Made with Bob
