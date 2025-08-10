import os
import shutil
import time
import multiprocessing
from functools import partial
from .file_handler import FileHandler
from .translator import GoogleTranslator, DeepLTranslator, YandexTranslator
from .rpy_parser import extract_translatable_strings, protect_code, unprotect_code

def _get_translator(engine, api_key):
    """Helper function to instantiate a translator. Can be called from a worker process."""
    if engine == "Google Translate":
        return GoogleTranslator()
    elif engine == "DeepL":
        return DeepLTranslator(api_key)
    elif engine == "Yandex Translate":
        return YandexTranslator(api_key)
    else:
        raise ValueError(f"Unsupported engine: {engine}")

def _process_file_worker(filepath, settings):
    """
    Worker function to be run in a separate process.
    Processes a single file and returns a list of log messages.
    """
    logs = []
    log = logs.append

    try:
        translator = _get_translator(settings.get("engine"), settings.get("api_key"))
    except Exception as e:
        log(f"Error initializing translator for {os.path.basename(filepath)}: {e}")
        return logs

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
            lines = original_content.split('\n')
    except Exception as e:
        log(f"Error reading file {filepath}: {e}")
        return logs

    if settings.get("backup", False):
        try:
            shutil.copy2(filepath, filepath + ".bak")
            log(f"Backup created for {filepath}")
        except Exception as e:
            log(f"Error creating backup for {filepath}: {e}")

    translatable_strings = extract_translatable_strings(original_content)
    if not translatable_strings:
        log(f"No translatable strings found in {filepath}.")
        return logs

    new_lines = list(lines)
    lines_added = 0
    strings_translated = 0

    for ts in translatable_strings:
        if settings.get("skip_translated", False) and ts.is_translated:
            continue

        original_text_no_quotes = ts.original.strip().strip('"')
        protected_text, protections = protect_code(original_text_no_quotes)

        success, translated_text = translator.translate(
            protected_text,
            settings.get("source_lang"),
            settings.get("target_lang")
        )

        if not success:
            log(f"  ERROR translating line {ts.line_number + 1} in {os.path.basename(filepath)}: {translated_text}")
            continue

        final_text = unprotect_code(translated_text, protections)

        original_line = lines[ts.line_number]
        indentation = len(original_line) - len(original_line.lstrip(' '))
        indent_space = ' ' * indentation

        old_line = f'{indent_space}old {ts.original}'
        new_line = f'{indent_space}new "{final_text}"'

        insert_pos = ts.line_number + lines_added
        new_lines[insert_pos] = old_line
        new_lines.insert(insert_pos + 1, new_line)
        lines_added += 1
        strings_translated += 1

    if strings_translated > 0:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            log(f"Finished writing {strings_translated} translations to {filepath}")
        except Exception as e:
            log(f"Error writing to file {filepath}: {e}")
    else:
        log(f"No new strings were translated in {filepath}.")

    return logs

class TranslationManager:
    """Orchestrates the entire translation process."""
    def __init__(self, settings, progress_callback=None, log_callback=None):
        self.settings = settings
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.file_handler = FileHandler()

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def run_translation(self):
        self._log("Starting translation process...")

        rpy_files = self.settings.get("rpy_files", [])
        game_folder = self.settings.get("game_folder", "")
        if game_folder:
            rpy_files.extend(self.file_handler.get_rpy_files_from_folder(game_folder))

        rpy_files = sorted(list(set(rpy_files)))

        if not rpy_files:
            self._log("No .rpy files found to translate.")
            return

        use_multiprocessing = self.settings.get("multiprocess", False)

        if use_multiprocessing:
            self._run_parallel(rpy_files)
        else:
            self._run_sequential(rpy_files)

        self._log("Translation process completed.")

    def _run_sequential(self, rpy_files):
        total_files = len(rpy_files)
        for i, filepath in enumerate(rpy_files):
            self._log(f"Processing file {i+1}/{total_files}: {filepath}")
            logs = _process_file_worker(filepath, self.settings)
            for log_msg in logs:
                self._log(f"  {log_msg}")
            if self.progress_callback:
                self.progress_callback(int((i + 1) / total_files * 100))

    def _run_parallel(self, rpy_files):
        total_files = len(rpy_files)
        # Use functools.partial to pass the settings dict to the worker
        worker_func = partial(_process_file_worker, settings=self.settings)

        try:
            # Use 'spawn' start method for better compatibility across platforms
            ctx = multiprocessing.get_context('spawn')
            with ctx.Pool() as pool:
                results = []
                # Use map_async to avoid blocking the main thread
                map_result = pool.map_async(worker_func, rpy_files, callback=results.extend)

                # Monitor progress
                completed_count = 0
                while not map_result.ready():
                    newly_completed = map_result._number_left * map_result._chunksize - (total_files - completed_count)
                    if newly_completed > 0:
                        completed_count += newly_completed
                        # Process results as they come in
                        for res in results:
                            for log_msg in res:
                                self._log(f"  {log_msg}")
                        results.clear()
                        if self.progress_callback:
                            self.progress_callback(int(completed_count / total_files * 100))
                    time.sleep(0.5)

                # Process any final results
                for res in map_result.get():
                    for log_msg in res:
                        self._log(f"  {log_msg}")
                if self.progress_callback:
                    self.progress_callback(100)

        except Exception as e:
            self._log(f"An error occurred during multiprocessing: {e}")
