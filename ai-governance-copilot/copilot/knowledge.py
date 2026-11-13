"""RAG layer: load Markdown knowledge files, chunk them, embed them, search them.

Flow:  knowledge/*.md  ->  chunks (one per "## " section)  ->  embeddings (FastEmbed)
       ->  Qdrant vector database (in memory)  ->  semantic search for the agent.
"""
from pathlib import Path

from . import config

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
COLLECTION = "governance_knowledge"


def load_chunks(folder: Path = KNOWLEDGE_DIR, max_chars: int = 1200) -> list:
    """Split every Markdown file into chunks, one per '## ' section.

    Each chunk keeps its document title and section heading, so a passage like
    'Score likelihood from 1 to 5' still carries the context 'AI risk assessment'.
    """
    chunks = []
    for path in sorted(folder.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        title = next((l[2:].strip() for l in lines if l.startswith("# ")), path.stem)
        section, body = "Introduction", []

        def flush():
            text = " ".join(" ".join(body).split())
            # Very long sections are split again so each vector stays focused.
            for start in range(0, len(text), max_chars):
                piece = text[start:start + max_chars]
                if piece:
                    chunks.append({
                        "id": len(chunks),
                        "source": path.name,
                        "section": section,
                        "text": f"{title} — {section}: {piece}",
                    })

        for line in lines:
            if line.startswith("## "):
                flush()
                section, body = line[3:].strip(), []
            elif not line.startswith("# "):
                body.append(line)
        flush()
    return chunks


class KnowledgeBase:
    """A tiny vector store: FastEmbed for embeddings, Qdrant (in memory) for search."""

    def __init__(self, chunks=None, embedding_model: str = config.EMBEDDING_MODEL):
        # Imported here so the rest of the project works without these heavy libraries.
        from fastembed import TextEmbedding
        from qdrant_client import QdrantClient, models

        self.chunks = chunks if chunks is not None else load_chunks()
        self.embedder = TextEmbedding(model_name=embedding_model)
        self.client = QdrantClient(":memory:")

        vectors = list(self.embedder.embed([c["text"] for c in self.chunks]))
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE),
        )
        self.client.upsert(
            collection_name=COLLECTION,
            points=[models.PointStruct(id=c["id"], vector=v.tolist(), payload=c)
                    for c, v in zip(self.chunks, vectors)],
        )

    def search(self, query: str, k: int = config.TOP_K) -> list:
        """Return the k most similar chunks, best first, with a similarity score."""
        query_vector = next(iter(self.embedder.query_embed(query)))
        hits = self.client.query_points(
            collection_name=COLLECTION, query=query_vector.tolist(), limit=k
        ).points
        return [{**hit.payload, "score": round(hit.score, 3)} for hit in hits]


_knowledge_base = None


def get_knowledge_base() -> KnowledgeBase:
    """Build the knowledge base once and reuse it (embedding takes a few seconds)."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
