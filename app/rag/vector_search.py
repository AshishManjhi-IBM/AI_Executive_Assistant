"""
Vector Search Module

Provides semantic search functionality for emails using ChromaDB.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorSearch:
    """
    Semantic search engine for emails.
    
    Features:
    - Semantic similarity search
    - Metadata filtering
    - Date range filtering
    - Sender filtering
    """
    
    def __init__(self, email_store):
        """
        Initialize vector search.
        
        Args:
            email_store: EmailStore instance
        """
        self.email_store = email_store
        self.collection = email_store.collection
        self.embedding_model = email_store.embedding_model
        
        logger.info("VectorSearch initialized")
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        sender: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for emails semantically.
        
        Args:
            query: Search query
            n_results: Number of results to return
            sender: Filter by sender email
            date_from: Filter by date from (ISO format)
            date_to: Filter by date to (ISO format)
            thread_id: Filter by thread ID
            
        Returns:
            List of matching emails with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                query,
                convert_to_numpy=True
            ).tolist()
            
            # Build where clause for filtering
            where_clause = self._build_where_clause(
                sender=sender,
                date_from=date_from,
                date_to=date_to,
                thread_id=thread_id
            )
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = self._format_results(results)
            
            logger.info(f"Search completed: {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []
    
    def _build_where_clause(
        self,
        sender: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB where clause for filtering.
        
        Args:
            sender: Filter by sender
            date_from: Filter by date from
            date_to: Filter by date to
            thread_id: Filter by thread ID
            
        Returns:
            Where clause dictionary or None
        """
        conditions = []
        
        if sender:
            conditions.append({"from": {"$eq": sender}})
        
        if thread_id:
            conditions.append({"thread_id": {"$eq": thread_id}})
        
        # Note: Date filtering would require custom logic
        # as ChromaDB doesn't support date comparisons directly
        # We'll filter dates in post-processing
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {"$and": conditions}
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format search results.
        
        Args:
            results: Raw ChromaDB results
            
        Returns:
            Formatted results list
        """
        formatted = []
        
        if not results['ids'] or not results['ids'][0]:
            return formatted
        
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        return formatted
    
    def search_by_sender(
        self,
        sender: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search emails by sender.
        
        Args:
            sender: Sender email address
            n_results: Number of results
            
        Returns:
            List of emails from sender
        """
        return self.search(
            query=f"emails from {sender}",
            n_results=n_results,
            sender=sender
        )
    
    def search_by_date_range(
        self,
        query: str,
        days_back: int = 7,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search emails within a date range.
        
        Args:
            query: Search query
            days_back: Number of days to look back
            n_results: Number of results
            
        Returns:
            List of matching emails
        """
        date_from = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        results = self.search(
            query=query,
            n_results=n_results * 2,  # Get more results for filtering
            date_from=date_from
        )
        
        # Filter by date in post-processing
        filtered_results = []
        for result in results:
            email_date = result['metadata'].get('date', '')
            if email_date >= date_from:
                filtered_results.append(result)
                if len(filtered_results) >= n_results:
                    break
        
        return filtered_results
    
    def search_recent(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search recent emails (last 7 days).
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of recent matching emails
        """
        return self.search_by_date_range(
            query=query,
            days_back=7,
            n_results=n_results
        )
    
    def find_similar_emails(
        self,
        email_id: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find emails similar to a given email.
        
        Args:
            email_id: Reference email ID
            n_results: Number of similar emails to return
            
        Returns:
            List of similar emails
        """
        try:
            # Get the reference email
            email = self.email_store.get_email(email_id)
            if not email:
                logger.error(f"Email not found: {email_id}")
                return []
            
            # Search using the email's document text
            return self.search(
                query=email['document'],
                n_results=n_results + 1  # +1 to exclude the reference email
            )[1:]  # Skip first result (the reference email itself)
            
        except Exception as e:
            logger.error(f"Error finding similar emails: {e}")
            return []
    
    def search_with_context(
        self,
        query: str,
        n_results: int = 3,
        context_window: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Search with thread context.
        
        Args:
            query: Search query
            n_results: Number of results
            context_window: Number of emails before/after to include
            
        Returns:
            List of emails with context
        """
        # Get initial results
        results = self.search(query=query, n_results=n_results)
        
        # For each result, get thread context
        enriched_results = []
        for result in results:
            thread_id = result['metadata'].get('thread_id')
            if thread_id:
                # Get other emails in the thread
                thread_emails = self.search(
                    query="",
                    n_results=context_window * 2,
                    thread_id=thread_id
                )
                result['thread_context'] = thread_emails
            
            enriched_results.append(result)
        
        return enriched_results

# Made with Bob
