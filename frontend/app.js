// API configuration
const API_BASE_URL = 'http://localhost:8000';

// Conversation history for context awareness
let conversationHistory = [];

// Debug logging
console.log('Abaqus Assistant JS loaded successfully');

// Add message to chat
function addMessage(text, isUser, sources = []) {
    const chatMessages = document.getElementById('chat-messages');
    
    // Remove welcome message on first interaction
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg && isUser) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = text;
    
    contentDiv.appendChild(textDiv);
    
    // Add sources if present
    if (!isUser && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        
        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'sources-title';
        sourcesTitle.textContent = '📚 Sources:';
        sourcesDiv.appendChild(sourcesTitle);
        
        sources.forEach((source, index) => {
            const sourceLink = document.createElement('a');
            sourceLink.className = 'source-link';
            sourceLink.href = source.url;
            sourceLink.target = '_blank';
            sourceLink.textContent = `${index + 1}. ${source.title}`;
            sourcesDiv.appendChild(sourceLink);
        });
        
        contentDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send question to API
async function sendQuestion() {
    console.log('sendQuestion called');
    const input = document.getElementById('question-input');
    const sendButton = document.getElementById('send-button');
    const buttonText = document.getElementById('button-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    const question = input.value.trim();
    console.log('Question:', question);
    
    if (!question) {
        console.log('Empty question, returning');
        return;
    }
    
    // Add user message
    addMessage(question, true);
    
    // Add to conversation history for context awareness
    conversationHistory.push({
        role: 'user',
        content: question
    });
    
    // Clear input
    input.value = '';
    
    // Disable button while processing
    sendButton.disabled = true;
    buttonText.style.display = 'none';
    loadingSpinner.style.display = 'inline-block';
    
    try {
        // Call API with optimized parameters and conversation history
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                top_k: 3,
                temperature: 0.3,
                conversation_history: conversationHistory
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant message
        addMessage(data.answer, false, data.sources);
        
        // Add to conversation history
        conversationHistory.push({
            role: 'assistant',
            content: data.answer
        });
        
        // Limit history to last 10 messages (5 exchanges) to avoid token bloat
        if (conversationHistory.length > 10) {
            conversationHistory = conversationHistory.slice(-10);
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessage(
            `❌ Error: ${error.message}\n\nPlease make sure the API server is running:\npython -m uvicorn src.api.main:app --reload`,
            false
        );
    } finally {
        // Re-enable button
        sendButton.disabled = false;
        buttonText.style.display = 'inline';
        loadingSpinner.style.display = 'none';
        
        // Focus input
        input.focus();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Allow Enter to send (Shift+Enter for new line)
    document.getElementById('question-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });
    
    // Check API health on load
    checkAPIHealth();
});

async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            console.log('API Status:', data);
            
            if (data.vector_store_count === 0) {
                addMessage(
                    '⚠️ Warning: Vector store is empty. Please run the indexer first:\npython scripts/index_docs.py',
                    false
                );
            } else if (!data.ollama_available) {
                addMessage(
                    '⚠️ Warning: Ollama model not available. Please make sure Ollama is running:\nollama serve',
                    false
                );
            }
        }
    } catch (error) {
        console.error('API health check failed:', error);
        addMessage(
            '⚠️ Cannot connect to API server. Please start it:\npython -m uvicorn src.api.main:app --reload',
            false
        );
    }
}
