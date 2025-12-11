"""Ollama LLM client for local inference"""
import requests
from typing import Dict, Generator, Optional
import logging
import json

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for Ollama local LLM API
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "llama3:8b"
    ):
        """
        Initialize Ollama client
        
        Args:
            base_url: Base URL for Ollama API
            model_name: Name of the model to use
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        logger.info(f"Initialized Ollama client: {model_name} at {base_url}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = 150,
        stream: bool = False
    ) -> str:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Generated text
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            logger.info(f"Generating response from {self.model_name}")
            
            if stream:
                return self._stream_generate(url, payload)
            else:
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                return result.get('response', '')
        
        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")
    
    def _stream_generate(self, url: str, payload: Dict) -> Generator[str, None, None]:
        """Stream generation (for future use)"""
        with requests.post(url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        yield chunk['response']
    
    def check_model_availability(self) -> bool:
        """
        Check if the model is available
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            available_models = [m['name'] for m in models]
            
            is_available = self.model_name in available_models
            
            if is_available:
                logger.info(f"Model {self.model_name} is available")
            else:
                logger.warning(
                    f"Model {self.model_name} not found. "
                    f"Available models: {available_models}"
                )
            
            return is_available
        
        except requests.RequestException as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
