import os

class FileHandler:
    """Handles loading and processing of .rpy files."""
    def __init__(self):
        pass

    def get_rpy_files_from_paths(self, paths):
        """
        Filters a list of paths, returning only those that are .rpy files.
        This is useful for validating files selected by the user.
        """
        rpy_files = [path for path in paths if path.lower().endswith('.rpy')]
        return rpy_files

    def get_rpy_files_from_folder(self, folder_path):
        """
        Scans a directory and its subdirectories for all .rpy files.
        """
        rpy_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.rpy'):
                    rpy_files.append(os.path.join(root, file))
        return rpy_files
