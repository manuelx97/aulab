from math import sqrt
import re

from hr_assistant.custom_embedding import CustomEmbeddingFunction


class SemanticChunking:
    def __init__(self, breakpoint_percentile=95, buffer_size=1):
        self.breakpoint_percentile = breakpoint_percentile
        self.buffer_size = buffer_size
        self.embedding_function = CustomEmbeddingFunction()

    def chunk_text(self, text):
        sentences = self._process_sentences(text)
        if len(sentences) <= 1:
            return [text.strip()] if text.strip() else []

        embeddings = self._embed_sentences(sentences)
        distances = self._calculate_distances(embeddings)

        threshold = self._percentile(distances, self.breakpoint_percentile)
        split_points = [
            index for index, distance in enumerate(distances) if distance > threshold
        ]

        chunks = []
        start = 0
        for point in split_points + [len(sentences) - 1]:
            chunk = " ".join(
                sentence["sentence"] for sentence in sentences[start : point + 1]
            ).strip()
            if chunk:
                chunks.append(chunk)
            start = point + 1

        return chunks

    def _process_sentences(self, text):
        raw_sentences = self._split_into_sentences(text)
        sentences = [
            {"sentence": sentence, "index": index}
            for index, sentence in enumerate(raw_sentences)
        ]

        for index, current in enumerate(sentences):
            context_range = range(
                max(0, index - self.buffer_size),
                min(len(sentences), index + self.buffer_size + 1),
            )
            current["combined_sentence"] = " ".join(
                sentences[context_index]["sentence"] for context_index in context_range
            )

        return sentences

    @staticmethod
    def _split_into_sentences(text):
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
            if sentence.strip()
        ]

        if len(sentences) == 1 and len(text) > 100:
            parts = re.split(r"([.!?\n;:])", text.strip())
            sentences = []
            for index in range(0, len(parts) - 1, 2):
                if parts[index].strip():
                    sentences.append(parts[index].strip() + parts[index + 1])

            if len(sentences) == 1:
                sentences = [
                    part.strip() + "," for part in text.split(",") if part.strip()
                ]
                if sentences:
                    sentences[-1] = sentences[-1][:-1] + "."

        return sentences or ([text.strip() + "."] if text.strip() else [])

    def _embed_sentences(self, sentences):
        return self.embedding_function(
            [sentence["combined_sentence"] for sentence in sentences]
        )

    def _calculate_distances(self, embeddings):
        return [
            1 - self._cosine_similarity(embeddings[index], embeddings[index + 1])
            for index in range(len(embeddings) - 1)
        ]

    @staticmethod
    def _cosine_similarity(first, second):
        dot_product = sum(left * right for left, right in zip(first, second))
        first_norm = sqrt(sum(value * value for value in first))
        second_norm = sqrt(sum(value * value for value in second))

        if not first_norm or not second_norm:
            return 0

        return dot_product / (first_norm * second_norm)

    @staticmethod
    def _percentile(values, percentile):
        if not values:
            return 0

        sorted_values = sorted(values)
        position = (len(sorted_values) - 1) * percentile / 100
        lower = int(position)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = position - lower

        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
