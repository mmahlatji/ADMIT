class FileEmptyException(Exception):
    """Raised when a file upload is too large, empty or not in the allowed types"""

class FileTooLargeException(Exception):
    """Raised when a file upload is too large, empty or not in the allowed types"""

class FileNotAllowedException(Exception):
    """Raised when a file upload is too large, empty or not in the allowed types"""

class FileAlreadyExistsException(Exception):
    """Raised when a file already exists"""


class FileUploadFailedException(Exception):
    """Raised when a file upload has failed"""
