import re
from typing import List


def remove_repeating_sentences(text: str) -> str:
    """Remove repeating sentences from the text.
    
    Args:
        text: The input text that may contain repeating sentences
        
    Returns:
        str: The text with repeating sentences removed
    """
    # Split text into sentences (handling common sentence endings)
    sentences = []
    current = ""
    
    # Split by newlines first to handle paragraph breaks
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        # Split by common sentence endings
        parts = paragraph.split('. ')
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                current += part + '. '
            else:
                current += part
        
        if current.strip():
            sentences.append(current.strip())
        current = ""
    
    # Remove duplicates while preserving order
    seen = set()
    unique_sentences = []
    for sentence in sentences:
        # Normalize sentence for comparison (remove extra whitespace)
        normalized = ' '.join(sentence.split())
        if normalized not in seen:
            seen.add(normalized)
            unique_sentences.append(sentence)
    
    # Join sentences back together with proper spacing
    return '\n\n'.join(unique_sentences)


def convert_newlines(text: str) -> str:
    """Convert escaped newlines to actual newlines.
    
    Args:
        text: The input text that may contain escaped newlines
        
    Returns:
        str: The text with proper newlines
    """
    # Replace escaped newlines with actual newlines
    text = text.replace('\\n', '\n')
    # Handle double newlines
    text = text.replace('\n\n', '\n')
    # Remove any trailing newlines
    text = text.rstrip('\n')
    return text


def filter_model_metadata(text: str) -> str:
    """Filter out model-specific metadata tokens from the text.
    
    Args:
        text: The input text that may contain model metadata
        
    Returns:
        str: The text with metadata removed
    """
    # Common patterns to remove
    patterns = [
        r'end\s*$',  # "end" at the end of text
        r'end\s*#\s*of\s*lines\s*$',  # "end # of lines"
        r'#\s*of\s*words:\s*\d+\s*\(~.*?\)\s*$',  # "# of words: X (~Y)"
        r'#\s*of\s*characters:\s*\d+\s*\(~.*?\)\s*$',  # "# of characters: X (~Y)"
        r'#\s*of\s*unique\s*words:\s*\d+\s*\(~.*?\)\s*$',  # "# of unique words: X (~Y)"
        r'\\end\{code\}\s*$',  # "\end{code}"
        r'\\begin\{code\}\s*$',  # "\begin{code}"
        r'\\section\*\s*\{[.\s]*\}\s*$',  # "\section* {....}" with any number of dots
        r'\\section\*.*$',  # Any \section* command to the end of line
        r'\{[\s.]*\}\s*$',  # Any {...} with only spaces and dots
        r'[.\s]{50,}\s*$',  # Any long sequence of dots and spaces (50+ characters)
    ]
    
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)
    
    # Remove any trailing whitespace
    text = text.rstrip()
    return text


def postprocess_text(text: str) -> str:
    """Apply all postprocessing functions to the text.
    
    Args:
        text: The input text to postprocess
        
    Returns:
        str: The postprocessed text
    """
    text = convert_newlines(text)
    text = remove_repeating_sentences(text)
    text = filter_model_metadata(text)
    return text 