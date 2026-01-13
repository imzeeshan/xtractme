from django import forms
from .models import Conversation, Message


class MessageForm(forms.ModelForm):
    """Form for creating a new message"""
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Type your message here...',
            'required': True,
        }),
        label='',
    )

    class Meta:
        model = Message
        fields = ['content']
