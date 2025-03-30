"""
This module provides functions for text processing, including removing special characters, excess spaces, empty lines, short lines, and emojis.
It also includes functions for capitalizing text appropriately and filtering out non-ASCII characters, making it useful for cleaning and formatting text data.

Functions:
---------
    capitalize_smartly:
        Removes illogical capital letters and ensures the text starts with a capital letter.
    remove_excess_spaces:
        Removes excess spaces from the text.
    remove_special_characters:
        Removes specified special characters from the text and cleans up unnecessary spaces.
    remove_special_characters_on_edges:
        Removes special characters from the edges of the text and cleans up unnecessary spaces.
    remove_empty_lines:
        Removes empty lines from the text.
    remove_short_lines:
        Removes lines that have fewer than a specified number of characters.
    remove_emojis:
        Removes all emojis from the text.
    ASCII_filter:
        Filters out unwanted characters from the input string, allowing only printable ASCII characters.
"""

from re import compile as cpl, UNICODE, escape, sub


def clipboard_encode(text):
    """
    Filters out characters that can't be encoded with the 'mbcs' codec.
    Essentially restricts text to a subset closer to ASCII or basic extended characters.
    """
    def can_encode_char(char: str) -> bool:
        try:
            char.encode('mbcs')
            return True
        except UnicodeEncodeError:
            return False
    filtered_text = ''.join(char for char in text if can_encode_char(char))
    return filtered_text


def capitalize_smartly(text: str) -> str:
    """
    Removes illogical capital letters and ensures the text starts with a capital letter.

    Parameters:
    ----------
        text (str): The input text.

    Returns:
    -------
        str: The processed text with appropriate capitalization.
    """
    text = sub(r'([.!?]\s+)(\w)', lambda match: match.group(1) + match.group(2).upper(), text.lower())
    if text:
        text = text[0].upper() + text[1:]
    return text

def remove_excess_spaces(text: str) -> str:
    """
    Removes excess spaces from the text.

    Parameters:
    ----------
        text (str): The input text.

    Returns:
    -------
        str: The text with excess spaces removed.
    """
    cleaned_lines = []
    for line in text.splitlines():
        cleaned_line = sub(r'(?<!\n)\s+', ' ', line)
        cleaned_line = cleaned_line.strip()
        cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)

def remove_special_characters(text: str, special_chars: list[str]=[
        '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '{', '}',
        '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/', '~', '`',
        '£', '¤', 'µ', '§', '°', '”', '¢', '¥', '¦', '©', 'ª', 'Æ', 'æ', 'ø', '˵', '˶', '‘', '’',
        '«', '»'
    ]) -> str:
    """
    Removes specified special characters from the text and cleans up unnecessary spaces.

    Parameters:
    ----------
        text (str): The input text.
        special_chars (list[str]): List of special characters to be removed from the text.

    Returns:
    -------
        str: The text with specified special characters removed and unnecessary spaces cleaned up.
    """
    cleaned_lines = []
    for line in text.splitlines():
        cleaned_line = ''
        for char in line:
            if char not in set(special_chars):
                cleaned_line += char
            else:
                cleaned_line += ' '
        cleaned_line = ' '.join(cleaned_line.split())
        cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)

def remove_special_characters_on_edges(
        text: str,
        special_chars: list[str]=[
            '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '{', '}',
            '[', ']', '|', '\\', ':', ';', '"', "'", '<', '>', ',', '.', '?', '/', '~', '`',
            '£', '¤', 'µ', '§', '°'
        ]
    ) -> str:
    """
    Removes special characters from the edges of the text and cleans up unnecessary spaces.

    Parameters:
    ----------
        text (str): The input text.
        special_chars (list[str]): List of special characters to be removed from the edges of the text.

    Returns:
    -------
        str: The text with special characters removed from the edges and unnecessary spaces cleaned up.
    """
    escaped_special_chars = ''.join(escape(char) for char in special_chars)
    return sub(f'^[{escaped_special_chars}\\s]+|[{escaped_special_chars}\\s]+$', '', text)

def remove_empty_lines(text: str) -> str:
    """
    Removes empty lines from the text.

    Parameters:
    ----------
        text (str): The input text.

    Returns:
    -------
        str: The text with empty lines removed.
    """
    return sub(r'\n\s*\n', '\n', text)

def remove_short_lines(text: str, min_characters: int=4) -> str:
    """
    Removes lines that have fewer than a specified number of characters.

    Parameters:
    ----------
        text (str): The input text.
        min_characters (int): Minimum number of characters a line must have to be kept.

    Returns:
    -------
        str: The text with short lines removed.
    """
    return '\n'.join([line for line in text.splitlines() if len(line.strip()) >= min_characters])

def remove_emojis(text: str) -> str:
    """
    Removes all emojis from the text.

    Parameters:
    ----------
        text (str): The input text.

    Returns:
    -------
        str: The text with all emojis removed.
    """
    emoji_pattern = cpl(f'[\U0001F600-\U0001F77F]|[\U0001F300-\U0001F5FF]|[\U0001F680-\U0001F6FF]|[\U0001F000-\U0001F1FF]', flags=UNICODE)
    text_without_emojis = emoji_pattern.sub('', text)
    return text_without_emojis

def ASCII_filter(input_string: str) -> str:
    """
    Filters out unwanted characters from the input string, allowing only printable ASCII characters.

    Parameters:
    ----------
        input_string (str): The input string.

    Returns:
    -------
        str: The filtered string with only printable ASCII characters.
    """
    return ''.join(cpl(r'[\x20-\x7E]+').findall(input_string))


