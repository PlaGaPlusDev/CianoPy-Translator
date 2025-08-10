import re
from dataclasses import dataclass

@dataclass
class TranslatableString:
    """Represents a string that can be translated."""
    line_number: int
    original: str
    prefix: str
    is_translated: bool = False
    translation: str = ""

# Regex patterns for different Ren'Py script lines
PATTERNS = {
    'dialogue': re.compile(r'^\s*(".*")$'),  # "Dialogue"
    'char_dialogue': re.compile(r'^\s*([a-zA-Z0-9_]+)\s+(".*")$'),  # char "Dialogue"
    'menu': re.compile(r'^\s*menu:'),
    'menu_choice': re.compile(r'^\s*(".*"):$'), # "Menu choice":
    'old_new': re.compile(r'^\s*(old|new)\s+(".*")$'), # old "string" or new "string"
    'comment': re.compile(r'^\s*#.*$'), # Comment line
}

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
        # Use a more robust placeholder format
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


def extract_translatable_strings(file_content):
    """
    Extracts translatable strings from the content of an .rpy file.
    """
    lines = file_content.split('\n')
    translatable_strings = []

    for i, line in enumerate(lines):
        if PATTERNS['comment'].match(line):
            continue

        # Check for 'old "..."' and 'new "..."' to identify already translated lines
        old_new_match = PATTERNS['old_new'].match(line)
        if old_new_match:
            # If we find a 'new' line, the previous 'old' line is considered translated
            if old_new_match.group(1) == 'new' and i > 0:
                # Find the corresponding 'old' line to mark it as translated
                prev_line = lines[i-1]
                if PATTERNS['old_new'].match(prev_line) and PATTERNS['old_new'].match(prev_line).group(1) == 'old':
                    # Find the matching string in our list and mark it
                    original_text = PATTERNS['old_new'].match(prev_line).group(2)
                    for ts in reversed(translatable_strings):
                        if ts.original == original_text:
                            ts.is_translated = True
                            ts.translation = old_new_match.group(2)
                            break
            continue # Skip processing this line further

        # Dialogue: char "string"
        char_dialogue_match = PATTERNS['char_dialogue'].match(line)
        if char_dialogue_match:
            prefix = f"{char_dialogue_match.group(1)} "
            original = char_dialogue_match.group(2)
            translatable_strings.append(TranslatableString(i, original, prefix))
            continue

        # Dialogue: "string"
        dialogue_match = PATTERNS['dialogue'].match(line)
        if dialogue_match:
            prefix = ""
            original = dialogue_match.group(1)
            translatable_strings.append(TranslatableString(i, original, prefix))
            continue

        # Menu Choice: "choice":
        menu_choice_match = PATTERNS['menu_choice'].match(line)
        if menu_choice_match:
            prefix = ""
            original = menu_choice_match.group(1)
            # The actual string to translate is the choice itself, not the colon
            translatable_strings.append(TranslatableString(i, original, prefix))
            continue

    return translatable_strings

if __name__ == '__main__':
    test_content = """
e "This is a line of dialogue."
"This is another line."

menu:
    "Choice one":
        e "You picked one."
    "Choice two":
        e "You picked two."

# This is a translated block
translate spanish:
    old "This is a line of dialogue."
    new "Esta es una linea de dialogo."
"""
    strings = extract_translatable_strings(test_content)
    for s in strings:
        print(s)

    # Test protection
    original_text = '"This has {b}bold{/b} and [variable]."'
    print(f"\nOriginal: {original_text}")
    protected, mapping = protect_code(original_text)
    print(f"Protected: {protected}")
    unprotected = unprotect_code('"TRADUCIDO: ' + protected.strip('"') + '"', mapping)
    print(f"Unprotected: {unprotected}")
