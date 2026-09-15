from typing import List, Optional
from apps.api.src.core.config import settings
from apps.api.src.core.logging import logger
from apps.api.src.providers.ollama import OllamaProvider


class IngestionEmbedder:
    def __init__(
        self,
        model: Optional[str] = None,
        expected_dimensions: Optional[int] = None,
        batch_size: int = 16,
    ):
        self.model = model or settings.EMBEDDING_MODEL
        self.expected_dimensions = expected_dimensions or settings.EMBEDDING_DIMENSIONS
        self.batch_size = batch_size
        self.provider = OllamaProvider()

    async def embed_chunks(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        total = len(texts)

        for i in range(0, total, self.batch_size):
            batch = texts[i : i + self.batch_size]
            try:
                embeddings = await self.provider.get_embeddings(batch, model=self.model)
            except Exception as e:
                logger.error(f"Failed to generate embeddings using model '{self.model}': {e}")
                raise RuntimeError(
                    f"Embedding generation failed for model '{self.model}'. "
                    f"Ensure Ollama is running and '{self.model}' is pulled ('ollama pull {self.model}'). Error: {e}"
                ) from e

            # Validate dimensions on first sample
            if embeddings and len(embeddings[0]) != self.expected_dimensions:
                dim = len(embeddings[0])
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.expected_dimensions}, received {dim}."
                )

            all_embeddings.extend(embeddings)

        return all_embeddings
