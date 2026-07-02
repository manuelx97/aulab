from hashlib import md5, sha1
import mimetypes
from pathlib import Path
import tempfile
from zipfile import ZipFile

from hr_assistant.config import Config
from hr_assistant.semantic_chunking import SemanticChunking


class DocumentProcessor:
    SUPPORTED_EXTENSIONS = {
        ".txt": "text",
        ".md": "text",
        ".pdf": "document",
        ".doc": "document",
        ".docx": "document",
        ".ppt": "presentation",
        ".pptx": "presentation",
        ".xls": "spreadsheet",
        ".xlsx": "spreadsheet",
        ".html": "web",
        ".htm": "web",
        ".csv": "data",
        ".json": "data",
        ".xml": "data",
        ".zip": "archive",
    }

    @staticmethod
    def get_file_hash(file_path):
        hash_md5 = md5()

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    @staticmethod
    def get_document_metadata(file_path):
        file_hash = DocumentProcessor.get_file_hash(file_path)
        extension = file_path.suffix.lower()

        return {
            "hash": f"{file_hash}:{Config.CHUNKING_VERSION}",
            "last_modified": file_path.stat().st_mtime,
            "source": file_path.name,
            "file_type": DocumentProcessor.SUPPORTED_EXTENSIONS.get(
                extension,
                "unknown",
            ),
            "mime_type": mimetypes.guess_type(file_path)[0] or "",
            "extension": extension,
        }

    @staticmethod
    def process_single_document(file_path):
        documents = []
        metadatas = []
        ids = []
        metadata = DocumentProcessor.get_document_metadata(file_path)
        extension = file_path.suffix.lower()
        file_type = DocumentProcessor.SUPPORTED_EXTENSIONS.get(extension)

        if not file_type:
            return documents, metadatas, ids

        text = DocumentProcessor.extract_text(file_path, file_type)
        semantic_chunking = SemanticChunking(
            breakpoint_percentile=Config.SEMANTIC_BREAKPOINT_PERCENTILE,
            buffer_size=Config.SEMANTIC_BUFFER_SIZE,
        )
        chunks = semantic_chunking.chunk_text(text)

        for index, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append(metadata)
            ids.append(
                DocumentProcessor.create_chunk_id(
                    metadata["source"],
                    metadata["hash"],
                    index,
                )
            )

        return documents, metadatas, ids

    @staticmethod
    def process_documents(database):
        current_files = {
            file_path.name: DocumentProcessor.get_document_metadata(file_path)
            for file_path in sorted(Config.DOCUMENTS_DIR.iterdir())
            if DocumentProcessor.is_supported(file_path)
        }

        existing_files = database.get_tracked_files()

        files_to_add = set(current_files) - set(existing_files)
        files_to_remove = set(existing_files) - set(current_files)
        files_to_update = {
            filename
            for filename in set(current_files) & set(existing_files)
            if current_files[filename]["hash"] != existing_files[filename]["hash"]
        }

        for filename in files_to_add:
            documents, metadatas, ids = DocumentProcessor.process_single_document(
                Config.DOCUMENTS_DIR / filename
            )
            database.add_documents(documents, metadatas, ids)

        for filename in files_to_update:
            database.remove_document_by_source(filename)
            documents, metadatas, ids = DocumentProcessor.process_single_document(
                Config.DOCUMENTS_DIR / filename
            )
            database.add_documents(documents, metadatas, ids)

        for filename in files_to_remove:
            database.remove_document_by_source(filename)

        return len(files_to_add), len(files_to_update), len(files_to_remove)

    @staticmethod
    def extract_text(file_path, file_type):
        if file_type == "archive":
            return DocumentProcessor.extract_zip_text(file_path)

        return DocumentProcessor.convert_to_markdown(file_path)

    @staticmethod
    def extract_zip_text(file_path):
        extracted_texts = []

        with tempfile.TemporaryDirectory() as temp_dir:
            with ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
                for nested_path in sorted(Path(temp_dir).rglob("*")):
                    if DocumentProcessor.is_supported(nested_path):
                        content = DocumentProcessor.convert_to_markdown(nested_path)
                        if content:
                            extracted_texts.append(
                                f"File: {nested_path.name}\n{content}"
                            )

        return "\n\n".join(extracted_texts)

    @staticmethod
    def convert_to_markdown(file_path):
        if file_path.suffix.lower() in {".txt", ".md", ".csv", ".json", ".xml"}:
            return file_path.read_text(encoding="utf-8", errors="ignore")

        try:
            from markitdown import MarkItDown
        except ImportError as error:
            raise RuntimeError(
                "Per leggere formati diversi da testo installa markitdown."
            ) from error

        try:
            result = MarkItDown().convert(str(file_path))
        except Exception as error:
            print(f"Errore nella conversione di {file_path}: {error}")
            return ""

        return result.text_content or ""

    @staticmethod
    def is_supported(file_path):
        return (
            file_path.is_file()
            and file_path.suffix.lower() in DocumentProcessor.SUPPORTED_EXTENSIONS
        )

    @staticmethod
    def create_chunk_id(filename, file_hash, index):
        raw_id = f"{filename}:{file_hash}:{index}"
        return sha1(raw_id.encode("utf-8")).hexdigest()

    @staticmethod
    def read_first_lines(file_path, limit=100):
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            extension = file_path.suffix.lower()
            file_type = DocumentProcessor.SUPPORTED_EXTENSIONS.get(extension)
            lines = DocumentProcessor.extract_text(file_path, file_type).splitlines()

        return [line.strip() for line in lines[:limit]]
