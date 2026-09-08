"""
Custom Exceptions
"""


class TokenBudgetExceeded(Exception):
    """
    Raised when the prompt
    cannot fit into the context window.
    """