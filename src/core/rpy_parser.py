import re
from dataclasses import dataclass, field
from typing import List, Literal

@dataclass
class TranslatableString:
    line_number: int
    original: str
    prefix: str
    type: Literal['dialogue', 'menu', 'existing']
    new_line_number: int = -1
    is_translated: bool = False
    translation: str = ""

PATTERNS = {
    'dialogue': re.compile(r'^\s*(".*")$'),
    'char_dialogue': re.compile(r'^\s*([a-zA-Z0-9_]+)\s+(".*")$'),
    'menu_choice': re.compile(r'^\s*(".*"):$'),
    'old_new': re.compile(r'^\s*(old|new)\s+(".*")$'),
    'comment': re.compile(r'^\s*#.*$'),
    'translate_block': re.compile(r'^(\s*)translate\s+[a-zA-Z0-9_]+:.*$'),
}

TAG_REGEX = re.compile(r'({[^}]+})')
VAR_REGEX = re.compile(r'(\[[^\]]+\])')
FORMAT_REGEX = re.compile(r'(%\([^\)]+\)s|%s)')

def protect_code(text_no_quotes):
    protections = []
    def protector(match):
        item = match.group(0)
        placeholder = f'<span class="notranslate">__P_{(len(protections))}_</span>'
        protections.append(item)
        return placeholder
    protected_text = TAG_REGEX.sub(protector, text_no_quotes)
    protected_text = VAR_REGEX.sub(protector, protected_text)
    protected_text = FORMAT_REGEX.sub(protector, protected_text)
    return protected_text, protections

def unprotect_code(translated_text, protections):
    for i, item in enumerate(protections):
        placeholder = f'<span class="notranslate">__P_{i}_</span>'
        # The placeholder might have been translated with spaces, so we need a flexible regex
        # This looks for the placeholder text, ignoring surrounding tags or spaces
        pattern = re.compile(f'__P_{i}_')
        translated_text = pattern.sub(item, translated_text, 1)
    return translated_text

def get_indent_level(line):
    return len(line) - len(line.lstrip(' '))

def find_next_meaningful_line(lines, start_index):
    for i in range(start_index, len(lines)):
        line = lines[i].strip()
        if line and not PATTERNS['comment'].match(line):
            return i, lines[i]
    return -1, ""

def extract_translatable_strings(file_content):
    lines = file_content.split('\n')
    translatable_strings = []
    translate_block_indent = -1

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()
        indent = get_indent_level(line)

        if not stripped_line or PATTERNS['comment'].match(stripped_line):
            i += 1
            continue

        if translate_block_indent != -1 and indent <= translate_block_indent:
            translate_block_indent = -1

        translate_match = PATTERNS['translate_block'].match(line)
        if translate_match:
            translate_block_indent = get_indent_level(line)
            i += 1
            continue

        old_match = PATTERNS['old_new'].match(stripped_line)
        if old_match and old_match.group(1) == 'old':
            next_line_index, next_line_full = find_next_meaningful_line(lines, i + 1)
            if next_line_index != -1:
                next_line_indent = get_indent_level(next_line_full)
                if translate_block_indent != -1 and next_line_indent > translate_block_indent:
                    new_match = PATTERNS['old_new'].match(next_line_full.strip())
                    if new_match and new_match.group(1) == 'new':
                        old_text = old_match.group(2)
                        new_text = new_match.group(2)

                        if old_text == new_text and old_text != '""':
                            translatable_strings.append(TranslatableString(
                                i, old_text, "", 'existing', next_line_index))
                        else:
                            translatable_strings.append(TranslatableString(
                                i, old_text, "", 'existing', next_line_index, True, new_text))

                        i = next_line_index + 1
                        continue

        if translate_block_indent != -1:
            i += 1
            continue

        char_dialogue_match = PATTERNS['char_dialogue'].match(stripped_line)
        if char_dialogue_match:
            translatable_strings.append(TranslatableString(
                i, char_dialogue_match.group(2), f"{char_dialogue_match.group(1)} ", 'dialogue'))
            i += 1
            continue

        dialogue_match = PATTERNS['dialogue'].match(stripped_line)
        if dialogue_match:
            translatable_strings.append(TranslatableString(
                i, dialogue_match.group(1), "", 'dialogue'))
            i += 1
            continue

        menu_choice_match = PATTERNS['menu_choice'].match(stripped_line)
        if menu_choice_match:
            translatable_strings.append(TranslatableString(
                i, menu_choice_match.group(1), "", 'menu'))
            i += 1
            continue

        i += 1

    return translatable_strings
