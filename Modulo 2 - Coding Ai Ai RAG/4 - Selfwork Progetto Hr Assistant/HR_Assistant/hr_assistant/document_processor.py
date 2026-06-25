from hashlib import sha1

from hr_assistant.config import Config


class DocumentProcessor:
    @staticmethod
    def process_documents():
        documents = []
        metadatas = []
        ids = []

        for file_path in sorted(Config.DOCUMENTS_DIR.glob("*.txt")):
            text = file_path.read_text(encoding="utf-8")
            chunks = [
                chunk.strip()
                for chunk in text.replace("\n", ".").split("### ")
                if chunk.strip()
            ]

            for index, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({"source": file_path.name})
                ids.append(DocumentProcessor.create_chunk_id(file_path.name, index))

        return documents, metadatas, ids

    @staticmethod
    def create_chunk_id(filename, index):
        raw_id = f"{filename}:{index}"
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
