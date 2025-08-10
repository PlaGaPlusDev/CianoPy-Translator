import re
from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class TranslatableString:
    """Represents a string that can be translated."""
    line_number: int
    original: str
    prefix: str
    type: Literal['dialogue', 'menu', 'existing']
    new_line_number: int = -1  # Line number of the 'new' statement, if applicable
    is_translated: bool = False
    translation: str = ""

# Regex patterns for different Ren'Py script lines
PATTERNS = {
    'dialogue': re.compile(r'^\s*(".*")$'),
    'char_dialogue': re.compile(r'^\s*([a-zA-Z0-9_]+)\s+(".*")$'),
    'menu_choice': re.compile(r'^\s*(".*"):$'),
    'old_new': re.compile(r'^\s*(old|new)\s+(".*")$'),
    'comment': re.compile(r'^\s*#.*$'),
    'translate_block': re.compile(r'^\s*translate\s+[a-zA-Z0-9_]+:.*$'),
}

# ... (protect_code and unprotect_code remain the same) ...
# Regex to find Ren'Py style text tags, e.g., {b}, {color=#fff}
TAG_REGEX = re.compile(r'({[^}]+})')
# Regex to find Python-style variables, e.g., [player_name]
VAR_REGEX = re.compile(r'(\[[^\]]+\])')
# Regex for Python format strings, e.g., %(name)s, %s
FORMAT_REGEX = re.compile(r'(%\([^\)]+\)s|%s)')

def protect_code(text):
    """
    Replaces code elements in a string with non-translatable placeholders.
    Returns the protected string and a list of the original code elements.
    """
    protections = []

    def protector(match):
        item = match.group(0)
        placeholder = f"__P_{(len(protections))}_"
        protections.append(item)
        return placeholder

    text_no_quotes = text.strip().strip('"')
    protected_text, protections = protect_code(text_no_quotes)
    return f'"{protected_text}"', protections

def unprotect_code(text, protections):
    """
    Restores the original code elements from placeholders.
    """
    text_no_quotes = text.strip().strip('"')
    unprotected_text = unprotect_code(text_no_quotes, protections)
    return f'"{unprotected_text}"'

def find_next_meaningful_line(lines, start_index):
    """Finds the next non-comment, non-empty line."""
    for i in range(start_index, len(lines)):
        line = lines[i].strip()
        if line and not PATTERNS['comment'].match(line):
            return i, line
    return -1, ""

def extract_translatable_strings(file_content):
    """
    Extracts translatable strings from the content of an .rpy file,
    now with support for pre-existing 'old'/'new' blocks.
    """
    lines = file_content.split('\n')
    translatable_strings = []
    in_translate_block = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        if PATTERNS['comment'].match(stripped_line) or not stripped_line:
            i += 1
            continue

        if PATTERNS['translate_block'].match(stripped_line):
            in_translate_block = True
            i += 1
            continue

        # Reset context if indentation decreases
        if in_translate_block and not stripped_line.startswith(' '):
            in_translate_block = False

        # Handle existing 'old'/'new' blocks
        old_match = PATTERNS['old_new'].match(stripped_line)
        if old_match and old_match.group(1) == 'old':
            old_text = old_match.group(2)

            next_line_index, next_line = find_next_meaningful_line(lines, i + 1)

            if next_line_index != -1:
                new_match = PATTERNS['old_new'].match(next_line)
                if new_match and new_match.group(1) == 'new':
                    new_text = new_match.group(2)

                    # This is a block to be translated
                    if old_text == new_text:
                        ts = TranslatableString(
                            line_number=i,
                            original=old_text,
                            prefix="",  # Prefix is handled by the 'new' line structure
                            type='existing',
                            new_line_number=next_line_index
                        )
                        translatable_strings.append(ts)
                    # This block is already translated
                    else:
                        # We can store it as translated if needed for "skip" logic
                        ts = TranslatableString(
                            line_number=i,
                            original=old_text,
                            prefix="",
                            type='existing',
                            new_line_number=next_line_index,
                            is_translated=True,
                            translation=new_text
                        )
                        translatable_strings.append(ts)

                    i = next_line_index + 1 # Skip past the 'new' line
                    continue

        # If we are inside a translate block, we should not process simple dialogue
        if in_translate_block:
            i += 1
            continue

        # Handle simple dialogue and menu choices (only if not in a translate block)
        char_dialogue_match = PATTERNS['char_dialogue'].match(stripped_line)
        if char_dialogue_match:
            prefix = f"{char_dialogue_match.group(1)} "
            original = char_dialogue_match.group(2)
            translatable_strings.append(TranslatableString(i, original, prefix, 'dialogue'))
            i += 1
            continue

        dialogue_match = PATTERNS['dialogue'].match(stripped_line)
        if dialogue_match:
            prefix = ""
            original = dialogue_match.group(1)
            translatable_strings.append(TranslatableString(i, original, prefix, 'dialogue'))
            i += 1
            continue

        menu_choice_match = PATTERNS['menu_choice'].match(stripped_line)
        if menu_choice_match:
            prefix = ""
            original = menu_choice_match.group(1)
            translatable_strings.append(TranslatableString(i, original, prefix, 'menu'))
            i += 1
            continue

        i += 1

    return translatable_strings
