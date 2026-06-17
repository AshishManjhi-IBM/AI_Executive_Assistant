"""
Email Store Module

Handles storing emails in ChromaDB vector store with embeddings.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmailStore:
    """
    Manages email storage in ChromaDB vector database.
    
    Features:
    - Store emails with embeddings
    - Update existing emails
    - Delete emails
    - Batch operations
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/chromadb",
        collection_name: str = "email_store",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the email store.
        
        Args:
            persist_directory: Path to store ChromaDB data
            collection_name: Name of the collection
            embedding_model: Sentence transformer model name
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Email storage with semantic search"}
        )
        
        logger.info(f"EmailStore initialized with collection: {collection_name}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _prepare_email_text(self, email: Dict[str, Any]) -> str:
        """
        Prepare email text for embedding.
        
        Args:
            email: Email dictionary
            
        Returns:
            Combined text for embedding
        """
        parts = []
        
        # Add subject
        if email.get('subject'):
            parts.append(f"Subject: {email['subject']}")
        
        # Add sender
        if email.get('from'):
            parts.append(f"From: {email['from']}")
        
        # Add body
        if email.get('body'):
            parts.append(f"Body: {email['body']}")
        
        return "\n".join(parts)
    
    def store_email(self, email: Dict[str, Any]) -> bool:
        """
        Store a single email in the vector store.
        
        Args:
            email: Email dictionary with keys:
                - id: Unique email ID
                - subject: Email subject
                - from: Sender email
                - to: Recipient email
                - date: Email date
                - body: Email body text
                - thread_id: Thread ID (optional)
                
        Returns:
            True if successful, False otherwise
        """
        try:
            email_id = email.get('id')
            if not email_id:
                logger.error("Email ID is required")
                return False
            
            # Prepare text for embedding
            email_text = self._prepare_email_text(email)
            
            # Generate embedding
            embedding = self._generate_embedding(email_text)
            
            # Prepare metadata
            metadata = {
                'subject': email.get('subject', ''),
                'from': email.get('from', ''),
                'to': email.get('to', ''),
                'date': email.get('date', ''),
                'thread_id': email.get('thread_id', ''),
                'stored_at': datetime.now().isoformat()
            }
            
            # Store in ChromaDB
            self.collection.add(
                ids=[email_id],
                embeddings=[embedding],
                documents=[email_text],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored email: {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing email: {e}")
            return False
    
    def store_emails_batch(self, emails: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Store multiple emails in batch.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            Dictionary with success and failure counts
        """
        results = {'success': 0, 'failed': 0}
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for email in emails:
            try:
                email_id = email.get('id')
                if not email_id:
                    results['failed'] += 1
                    continue
                
                # Prepare text and embedding
                email_text = self._prepare_email_text(email)
                embedding = self._generate_embedding(email_text)
                
                # Prepare metadata
                metadata = {
                    'subject': email.get('subject', ''),
                    'from': email.get('from', ''),
                    'to': email.get('to', ''),
                    'date': email.get('date', ''),
                    'thread_id': email.get('thread_id', ''),
                    'stored_at': datetime.now().isoformat()
                }
                
                ids.append(email_id)
                embeddings.append(embedding)
                documents.append(email_text)
                metadatas.append(metadata)
                
            except Exception as e:
                logger.error(f"Error preparing email {email.get('id')}: {e}")
                results['failed'] += 1
        
        # Store batch
        if ids:
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                results['success'] = len(ids)
                logger.info(f"Stored {len(ids)} emails in batch")
            except Exception as e:
                logger.error(f"Error storing batch: {e}")
                results['failed'] += len(ids)
        
        return results
    
    def delete_email(self, email_id: str) -> bool:
        """
        Delete an email from the store.
        
        Args:
            email_id: Email ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[email_id])
            logger.info(f"Deleted email: {email_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting email: {e}")
            return False
    
    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an email by ID.
        
        Args:
            email_id: Email ID
            
        Returns:
            Email data or None if not found
        """
        try:
            result = self.collection.get(
                ids=[email_id],
                include=['documents', 'metadatas']
            )
            
            # Check if result is None or empty
            if result is None:
                return None
            
            # Safely check if we have valid results
            if result.get('ids') and len(result['ids']) > 0:
                documents = result.get('documents')
                metadatas = result.get('metadatas')
                
                return {
                    'id': result['ids'][0],
                    'document': documents[0] if documents and len(documents) > 0 else None,
                    'metadata': metadatas[0] if metadatas and len(metadatas) > 0 else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving email: {e}")
            return None
    
    def count_emails(self) -> int:
        """
        Get total number of stored emails.
        
        Returns:
            Number of emails in the store
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting emails: {e}")
            return 0
    
    def clear_store(self) -> bool:
        """
        Clear all emails from the store.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Email storage with semantic search"}
            )
            logger.info("Email store cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing store: {e}")
            return False

# Made with Bob
