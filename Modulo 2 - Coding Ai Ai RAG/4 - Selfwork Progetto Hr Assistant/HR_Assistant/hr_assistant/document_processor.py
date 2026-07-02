from hashlib import md5, sha1

from hr_assistant.config import Config
from hr_assistant.semantic_chunking import SemanticChunking


class DocumentProcessor:
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
        return {
            "hash": f"{file_hash}:{Config.CHUNKING_VERSION}",
            "last_modified": file_path.stat().st_mtime,
            "source": file_path.name,
        }

    @staticmethod
    def process_single_document(file_path):
        documents = []
        metadatas = []
        ids = []
        metadata = DocumentProcessor.get_document_metadata(file_path)

        text = file_path.read_text(encoding="utf-8")
        chunks = SemanticChunking().chunk_text(text)

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
            for file_path in sorted(Config.DOCUMENTS_DIR.glob("*.txt"))
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
    def create_chunk_id(filename, file_hash, index):
        raw_id = f"{filename}:{file_hash}:{index}"
        return sha1(raw_id.encode("utf-8")).hexdigest()

    @staticmethod
    def read_first_lines(file_path, limit=100):
        lines = []

        with file_path.open("r", encoding="utf-8") as file:
            for index, line in enumerate(file):
                if index >= limit:
                    break
                lines.append(line.strip())

        return lines
