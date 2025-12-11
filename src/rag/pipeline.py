"""End-to-end RAG pipeline"""
from typing import Dict, List, Optional
import logging
from .retriever import Retriever
from .llm_client import OllamaClient

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline: retrieve -> generate
    """
    
    def __init__(self, retriever: Retriever, llm_client: OllamaClient):
        """
        Initialize RAG pipeline
        
        Args:
            retriever: Document retriever
            llm_client: LLM client
        """
        self.retriever = retriever
        self.llm_client = llm_client
    
    def query(
        self,
        question: str,
        top_k: int = 3,
        temperature: float = 0.3,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Answer a question using RAG with optional conversation context
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
            temperature: LLM temperature
            conversation_history: Previous messages for context awareness
            
        Returns:
            Dictionary with answer, sources, and context
        """
        logger.info(f"Processing question: {question}")
        
        # 1. Retrieve relevant documents
        documents = self.retriever.retrieve(question, top_k=top_k)
        
        if not documents:
            return {
                'answer': "I don't have specific documentation about that, but I can help with general Abaqus questions. Could you rephrase or ask something more specific?",
                'sources': [],
                'context': ''
            }
        
        # 2. Format context
        context = self.retriever.format_context(documents)
        
        # 3. Build prompt with conversation history
        prompt = self._build_prompt(question, context, conversation_history)
        
        # 4. Generate answer
        answer = self.llm_client.generate(
            prompt=prompt,
            temperature=temperature
        )
        
        # 5. Extract sources
        sources = self.retriever.get_sources(documents)
        
        return {
            'answer': answer.strip(),
            'sources': sources,
            'context': context
        }
    
    def _build_prompt(self, question: str, context: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Build optimized prompt for natural, conversational answers
        
        Args:
            question: User question
            context: Retrieved context
            conversation_history: Previous conversation for context
            
        Returns:
            Formatted prompt for natural answer format
        """
        # Build conversation context if available
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            # Include last 2 exchanges for context (limit to avoid token bloat)
            recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
            conv_lines = []
            for msg in recent_history:
                role = msg.get('role', '')
                content = msg.get('content', '')[:100]  # Truncate for brevity
                if role == 'user':
                    conv_lines.append(f"User asked: {content}")
                elif role == 'assistant':
                    conv_lines.append(f"You said: {content}")
            
            if conv_lines:
                conversation_context = "\n**Context:** " + " | ".join(conv_lines) + "\n\n"
        
        # Natural conversational prompt - no "according to" or doc references
        # Can answer general questions + use documentation when available
        prompt = f"""You are an expert Abaqus assistant. Answer naturally and directly.

{conversation_context}**Documentation:**
{context}

**Question:** {question}

**Instructions:**
- Keep answers SHORT (2-3 sentences max)
- Answer directly - NO phrases like "According to", "Based on", "The documentation states"
- Match the user's tone (technical, simple, ELI5, etc.)
- Use documentation when relevant, but also general Abaqus knowledge
- If continuing a conversation, acknowledge context briefly
- ONE proactive suggestion if helpful

**Answer:**
"""
        return prompt
