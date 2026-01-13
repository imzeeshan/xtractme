"""Views for the chat app"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import Conversation, Message
from .forms import MessageForm
from .services import (
    create_conversation,
    add_message,
    get_conversation_history,
    get_ollama_response,
)


@login_required
def chat_home(request):
    """Homepage showing recent conversations"""
    conversations = Conversation.objects.filter(user=request.user)[:10]
    return render(request, 'chat/homepage.html', {
        'conversations': conversations
    })


@login_required
def chat_detail(request, conversation_id):
    """Chat interface for a specific conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    chat_messages = conversation.messages.all()
    form = MessageForm()
    
    return render(request, 'chat/chat.html', {
        'conversation': conversation,
        'messages': chat_messages,
        'form': form,
    })


@login_required
def chat_new(request):
    """Create a new conversation and redirect to chat"""
    conversation = create_conversation(request.user)
    return redirect('chat_detail', conversation_id=conversation.id)


@login_required
def send_message(request, conversation_id):
    """Send a message and get AI response"""
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data['content']
            
            # Add user message
            add_message(conversation, 'user', user_message)
            
            # Get conversation history
            history = get_conversation_history(conversation)
            
            # Get AI response
            try:
                ai_response = get_ollama_response(history)
                
                # Add AI response
                add_message(conversation, 'assistant', ai_response)
                
                # Return JSON response for HTMX
                return JsonResponse({
                    'user_message': user_message,
                    'ai_response': ai_response,
                })
            except Exception as e:
                messages.error(request, f'Error getting AI response: {str(e)}')
                return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
