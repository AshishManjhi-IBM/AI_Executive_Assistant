"""
Email Retriever Module

RAG (Retrieval-Augmented Generation) retriever for email question answering.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)


class EmailRetriever:
    """
    RAG retriever for answering questions about emails.
    
    Features:
    - Retrieve relevant emails for a query
    - Format context for LLM
    - Generate answers using RAG
    """
    
    def __init__(self, vector_search, llm: Optional[ChatOllama] = None):
        """
        Initialize the retriever.
        
        Args:
            vector_search: VectorSearch instance
            llm: Optional ChatOllama instance
        """
        self.vector_search = vector_search
        
        # Initialize LLM if not provided
        if llm is None:
            model = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
            base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.llm = ChatOllama(
                model=model,
                base_url=base_url,
                temperature=0.3
            )
        else:
            self.llm = llm
        
        logger.info("EmailRetriever initialized")
    
    def retrieve_context(
        self,
        query: str,
        n_results: int = 3,
        **search_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant emails for a query.
        
        Args:
            query: User query
            n_results: Number of emails to retrieve
            **search_kwargs: Additional search parameters
            
        Returns:
            List of relevant emails
        """
        try:
            results = self.vector_search.search(
                query=query,
                n_results=n_results,
                **search_kwargs
            )
            
            logger.info(f"Retrieved {len(results)} emails for query")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def format_context(self, emails: List[Dict[str, Any]]) -> str:
        """
        Format retrieved emails as context for LLM.
        
        Args:
            emails: List of email dictionaries
            
        Returns:
            Formatted context string
        """
        if not emails:
            return "No relevant emails found."
        
        context_parts = ["Here are the relevant emails:\n"]
        
        for i, email in enumerate(emails, 1):
            metadata = email.get('metadata', {})
            document = email.get('document', '')
            
            context_parts.append(f"\n--- Email {i} ---")
            context_parts.append(f"From: {metadata.get('from', 'Unknown')}")
            context_parts.append(f"Subject: {metadata.get('subject', 'No subject')}")
            context_parts.append(f"Date: {metadata.get('date', 'Unknown')}")
            context_parts.append(f"Content:\n{document}")
            context_parts.append(f"Relevance Score: {email.get('similarity', 0):.2f}")
        
        return "\n".join(context_parts)
    
    def answer_question(
        self,
        question: str,
        n_results: int = 3,
        **search_kwargs
    ) -> str:
        """
        Answer a question using RAG.
        
        Args:
            question: User question
            n_results: Number of emails to retrieve
            **search_kwargs: Additional search parameters
            
        Returns:
            Answer string
        """
        try:
            # Retrieve relevant emails
            emails = self.retrieve_context(
                query=question,
                n_results=n_results,
                **search_kwargs
            )
            
            if not emails:
                return "I couldn't find any relevant emails to answer your question."
            
            # Format context
            context = self.format_context(emails)
            
            # Create prompt
            prompt = self._create_rag_prompt(question, context)
            
            # Generate answer
            response = self.llm.invoke(prompt)
            
            # Extract content and ensure it's a string
            if hasattr(response, 'content'):
                content = response.content
                # Handle case where content might be a list
                if isinstance(content, list):
                    answer = str(content)
                else:
                    answer = str(content)
            else:
                answer = str(response)
            
            logger.info("Generated answer using RAG")
            return answer
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Error generating answer: {str(e)}"
    
    def _create_rag_prompt(self, question: str, context: str) -> str:
        """
        Create RAG prompt for LLM.
        
        Args:
            question: User question
            context: Retrieved email context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are an AI assistant helping to answer questions about emails.

Context (Retrieved Emails):
{context}

Question: {question}

Instructions:
1. Answer the question based ONLY on the information in the retrieved emails above
2. If the emails don't contain enough information to answer, say so
3. Cite specific emails when providing information (e.g., "According to Email 1...")
4. Be concise and direct
5. Include relevant dates, senders, and details from the emails

Answer:"""
        
        return prompt
    
    def summarize_emails(
        self,
        query: str,
        n_results: int = 5
    ) -> str:
        """
        Summarize emails matching a query.
        
        Args:
            query: Search query
            n_results: Number of emails to summarize
            
        Returns:
            Summary string
        """
        try:
            # Retrieve emails
            emails = self.retrieve_context(query=query, n_results=n_results)
            
            if not emails:
                return "No emails found matching your query."
            
            # Format context
            context = self.format_context(emails)
            
            # Create summary prompt
            prompt = f"""Summarize the following emails concisely:

{context}

Provide a brief summary highlighting:
1. Main topics discussed
2. Key senders
3. Important dates or deadlines
4. Action items if any

Summary:"""
            
            # Generate summary
            response = self.llm.invoke(prompt)
            
            # Extract content and ensure it's a string
            if hasattr(response, 'content'):
                content = response.content
                # Handle case where content might be a list
                if isinstance(content, list):
                    summary = str(content)
                else:
                    summary = str(content)
            else:
                summary = str(response)
            
            logger.info("Generated email summary")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing emails: {e}")
            return f"Error generating summary: {str(e)}"
    
    def find_action_items(
        self,
        n_results: int = 10
    ) -> str:
        """
        Find action items from recent emails.
        
        Args:
            n_results: Number of emails to analyze
            
        Returns:
            Action items summary
        """
        query = "action items tasks todo deadlines follow-up required"
        
        try:
            emails = self.retrieve_context(query=query, n_results=n_results)
            
            if not emails:
                return "No action items found in recent emails."
            
            context = self.format_context(emails)
            
            prompt = f"""Analyze the following emails and extract action items:

{context}

List all action items, tasks, deadlines, and follow-ups mentioned in these emails.
Format as a numbered list with:
- Action item description
- Who it's for (if mentioned)
- Deadline (if mentioned)
- Source email

Action Items:"""
            
            response = self.llm.invoke(prompt)
            
            # Extract content and ensure it's a string
            if hasattr(response, 'content'):
                content = response.content
                # Handle case where content might be a list
                if isinstance(content, list):
                    action_items = str(content)
                else:
                    action_items = str(content)
            else:
                action_items = str(response)
            
            logger.info("Extracted action items")
            return action_items
            
        except Exception as e:
            logger.error(f"Error finding action items: {e}")
            return f"Error extracting action items: {str(e)}"

# Made with Bob
