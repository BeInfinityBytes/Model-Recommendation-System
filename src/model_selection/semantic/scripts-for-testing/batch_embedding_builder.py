import logging
from src.shared.core.model_data_client import ModelDataMongoClient
from src.model_selection.semantic.embedding_text_builder import build_embedding_text

logging.getLogger("pymongo").setLevel(logging.WARNING)


def main():
    print("Starting batch embedding text generation...\n")

    model_db = ModelDataMongoClient()
    models = model_db.get_all_models()

    print(f"Total models fetched from MongoDB: {len(models)}\n")

    # Build lookup dictionary
    model_lookup = {
        m.get("model_name"): m
        for m in models
    }

    embedding_payloads = []

    for idx, model in enumerate(models, start=1):

        base_model_doc = None
        base_model_id = model.get("base_model_id")

        if base_model_id:
            base_model_id = base_model_id.strip()
            base_model_doc = model_lookup.get(base_model_id)

            if base_model_doc:
                print(f"[Inheritance Applied] {model.get('model_name')} ← {base_model_id}")
            else:
                print(f"[Warning] Base model '{base_model_id}' not found for '{model.get('model_name')}'")

        result = build_embedding_text(model, base_model_doc)

        payload = {
            "model_id": str(model.get("_id")),
            "embedding_text": result["embedding_text"],
            "metadata": result["metadata"]
        }

        embedding_payloads.append(payload)

        if idx <= 8:
            print(f"\n----- Sample Model {idx} -----")
            print("Model Name:", model.get("model_name"))
            print("Base Model ID:", base_model_id)
            print("Embedding Text:\n", result["embedding_text"])
            print("-----------------------------")

    print("\nBatch embedding text generation completed.")
    print(f"Total embedding payloads prepared: {len(embedding_payloads)}")


if __name__ == "__main__":
    main()