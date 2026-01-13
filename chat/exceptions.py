"""Custom exceptions for the chat app"""


class OllamaConnectionError(Exception):
    """Raised when unable to connect to Ollama"""
    pass


class OllamaAPIError(Exception):
    """Raised when Ollama API returns an error"""
    pass
