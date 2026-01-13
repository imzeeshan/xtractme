"""Service layer for chat operations and Ollama API integration"""
import ollama
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Conversation, Message
from .constants import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_HOST
from .exceptions import OllamaConnectionError, OllamaAPIError


def get_ollama_config():
    """Get Ollama configuration from settings"""
    ollama_host = getattr(settings, 'OLLAMA_HOST', DEFAULT_OLLAMA_HOST)
    ollama_model = getattr(settings, 'OLLAMA_MODEL', DEFAULT_OLLAMA_MODEL)
    return ollama_host, ollama_model


def get_conversation_history(conversation):
    """Get conversation history as messages format for Ollama"""
    messages = conversation.messages.all()
    return [
        {'role': msg.role, 'content': msg.content}
        for msg in messages
    ]


def create_conversation(user, title=None):
    """Create a new conversation"""
    if not title:
        title = f"Chat {timezone.now().strftime('%Y-%m-%d %H:%M')}"
    return Conversation.objects.create(user=user, title=title)


def add_message(conversation, role, content):
    """Add a message to a conversation"""
    return Message.objects.create(
        conversation=conversation,
        role=role,
        content=content
    )


def get_ollama_response(messages, model=None):
    """Get response from Ollama API"""
    ollama_host, default_model = get_ollama_config()
    model = model or default_model
    
    # Set Ollama host if configured
    if ollama_host != DEFAULT_OLLAMA_HOST:
        import os
        os.environ['OLLAMA_HOST'] = ollama_host
    
    try:
        response = ollama.chat(model=model, messages=messages, stream=False)
        return response.get('message', {}).get('content', '')
    except Exception as e:
        error_msg = str(e)
        if 'Connection' in error_msg or 'connect' in error_msg.lower():
            raise OllamaConnectionError(f"Could not connect to Ollama at {ollama_host}. Please ensure Ollama is running.")
        raise OllamaAPIError(f"Error with Ollama API: {error_msg}")


def stream_ollama_response(messages, model=None):
    """Stream response from Ollama API"""
    ollama_host, default_model = get_ollama_config()
    model = model or default_model
    
    # Set Ollama host if configured
    if ollama_host != DEFAULT_OLLAMA_HOST:
        import os
        os.environ['OLLAMA_HOST'] = ollama_host
    
    try:
        stream = ollama.chat(model=model, messages=messages, stream=True)
        for chunk in stream:
            if 'message' in chunk and 'content' in chunk['message']:
                yield chunk['message']['content']
    except Exception as e:
        error_msg = str(e)
        if 'Connection' in error_msg or 'connect' in error_msg.lower():
            raise OllamaConnectionError(f"Could not connect to Ollama at {ollama_host}. Please ensure Ollama is running.")
        raise OllamaAPIError(f"Error with Ollama API: {error_msg}")
