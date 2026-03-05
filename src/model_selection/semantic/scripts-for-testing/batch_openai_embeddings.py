# C:\Users\Admin\Desktop\Internship\modeliq-backend\model-iq-tech-backend\src\model_selection\semantic\scripts-for-testing\batch_openai_embeddings.py

import json
import os
from datetime import datetime

from src.shared.core.model_data_client import ModelDataMongoClient
from src.model_selection.semantic.embedding_text_builder import build_embedding_text
from src.model_selection.semantic.openai_embedding_client import generate_embedding

OUTPUT_DIR = "tmp/embeddings"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_batch_embedding_generation(limit: int | None = None):
    mongo_client = ModelDataMongoClient()
    models = mongo_client.get_all_models()

    if limit:
        models = models[:limit]

    print(f"Generating embeddings for {len(models)} models...")

    # ---------------------------------------------------------
    # Create lookup dictionary for base model resolution
    # ---------------------------------------------------------
    model_lookup = {
        model.get("model_name"): model
        for model in models
        if model.get("model_name")
    }

    embedding_payloads = []

    # ---------------------------------------------------------
    # Process each model
    # ---------------------------------------------------------
    for idx, model_doc in enumerate(models, start=1):

        base_model_doc = None
        base_model_id = model_doc.get("base_model_id")

        if base_model_id:
            base_model_doc = model_lookup.get(base_model_id)

            if base_model_doc:
                print(
                    f"[Inheritance Applied] "
                    f"{model_doc.get('model_name')} ← {base_model_id}"
                )
            else:
                print(
                    f"[Warning] Base model '{base_model_id}' not found "
                    f"for '{model_doc.get('model_name')}'"
                )

        # ✅ FIXED HERE (correct argument name)
        result = build_embedding_text(
            model_doc,
            base_model_doc=base_model_doc
        )

        embedding_text = result["embedding_text"]
        metadata = result["metadata"]

        # Generate OpenAI embedding
        embedding_vector = generate_embedding(embedding_text)

        payload = {
            "id": str(model_doc["_id"]),
            "embedding": embedding_vector,
            "metadata": metadata,
            "text_preview": embedding_text[:300],
        }

        embedding_payloads.append(payload)

        model_name = metadata.get("model_name", "unknown-model")
        print(f"[{idx}/{len(models)}] Embedded: {model_name}")

    # ---------------------------------------------------------
    # Save embeddings to file
    # ---------------------------------------------------------
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"{OUTPUT_DIR}/model_embeddings_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(embedding_payloads, f, indent=2)

    print("\nBatch embedding generation completed.")
    print(f"Saved to: {output_file}")
    print(f"Total vectors: {len(embedding_payloads)}")


if __name__ == "__main__":
    run_batch_embedding_generation()