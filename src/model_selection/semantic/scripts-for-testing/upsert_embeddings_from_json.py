#C:\Users\Admin\Desktop\Internship\modeliq-backend\model-iq-tech-backend\src\model_selection\semantic\scripts-for-testing\upsert_embeddings_from_json.py
import os
import json
from pathlib import Path
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# ENVIRONMENT
# -------------------------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

EMBEDDINGS_DIR = Path("tmp/embeddings")
BATCH_SIZE = 100


def get_latest_embedding_file() -> Path:
    files = sorted(
        EMBEDDINGS_DIR.glob("model_embeddings_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not files:
        raise FileNotFoundError("No embedding files found in tmp/embeddings")

    return files[0]


def load_embeddings(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def batch_upsert(index, vectors):
    for i in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[i : i + BATCH_SIZE]
        index.upsert(vectors=batch)
        print(f"Upserted vectors {i + 1} → {i + len(batch)}")


def main():
    print("🔹 Starting Pinecone JSON upsert...\n")

    latest_file = get_latest_embedding_file()
    print(f"Using embedding file: {latest_file.name}")

    embeddings = load_embeddings(latest_file)
    print(f"Total vectors: {len(embeddings)}")

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)

    vectors = []

    for item in embeddings:
        metadata = item.get("metadata", {}).copy()

        # -------------------------------------------------
        #  ADD EMBEDDING TEXT FOR RERANKING (SAFE)
        # -------------------------------------------------
        embedding_text = item.get("embedding_text") or item.get("text_preview")

        if embedding_text:
            metadata["text"] = embedding_text

        vectors.append(
            {
                "id": item["id"],
                "values": item["embedding"],
                "metadata": metadata,
            }
        )

    batch_upsert(index, vectors)

    print("\nPinecone upsert completed successfully")


if __name__ == "__main__":
    main()
