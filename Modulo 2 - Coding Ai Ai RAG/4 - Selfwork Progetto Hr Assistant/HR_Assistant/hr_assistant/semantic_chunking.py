import re
from math import sqrt

from openai import OpenAI

from hr_assistant.config import Config


class SemanticChunking:
    def __init__(self, breakpoint_percentile=95, buffer_size=1):
        self.breakpoint_percentile = breakpoint_percentile
        self.buffer_size = buffer_size
        self.client = OpenAI(api_key=Config.require_openai_api_key())

    def chunk_text(self, text):
        sentences = self._process_sentences(text)
        if len(sentences) <= 1:
            return [text.strip()] if text.strip() else []

        embeddings = self._embed_sentences(sentences)
        distances = self._calculate_distances(embeddings)

        threshold = self._percentile(distances, self.breakpoint_percentile)
        split_points = [index for index, distance in enumerate(distances) if distance > threshold]

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
        raw_sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.?!])\s+", text)
            if sentence.strip()
        ]
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

    def _embed_sentences(self, sentences):
        response = self.client.embeddings.create(
            model=Config.EMBEDDING_MODEL,
            input=[sentence["combined_sentence"] for sentence in sentences],
        )
        return [item.embedding for item in response.data]

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
