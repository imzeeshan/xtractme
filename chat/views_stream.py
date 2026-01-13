"""Streaming views for Server-Sent Events (SSE)"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from .models import Conversation
from .services import (
    add_message,
    get_conversation_history,
    stream_ollama_response,
)


@login_required
@require_http_methods(["POST"])
def stream_message(request, conversation_id):
    """Stream AI response using Server-Sent Events"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    user_message = request.POST.get('content', '').strip()
    if not user_message:
        return StreamingHttpResponse(
            iter([f"data: {{'error': 'Empty message'}}\n\n"]),
            content_type='text/event-stream'
        )
    
    # Add user message
    add_message(conversation, 'user', user_message)
    
    # Get conversation history
    history = get_conversation_history(conversation)
    
    def event_stream():
        """Generator function for SSE"""
        full_response = ''
        try:
            for chunk in stream_ollama_response(history):
                full_response += chunk
                # Format as SSE data
                yield f"data: {chunk}\n\n"
            
            # Save the complete response
            add_message(conversation, 'assistant', full_response)
            
            # Send completion event
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = str(e)
            yield f"data: Error: {error_msg}\n\n"
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable buffering for nginx
    return response
