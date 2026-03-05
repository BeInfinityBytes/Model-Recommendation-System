from src.model_selection.semantic.embedding_text_builder import build_embedding_text

sample_model = {
    "model_name": "moonshotai/Kimi-K2-Thinking",
    "base_architecture_type": ["Mixture-of-Experts (MoE)"],
    "primary_focus": [
        "General purpose",
        "Assistant",
        "Research-oriented",
        "Math & reasoning",
        "Problem solving"
    ],
    "tasks": [
        "text-generation",
        "question-answering",
        "coding-focused"
    ],
    "summary": "Kimi K2 Thinking is a state-of-the-art Mixture-of-Experts model with over 1T parameters.",
    "reasoning_level_bucket": "Expert",
    "math_proficiency_bucket": "Expert",
    "code_proficiency_bucket": "Unknown",
    "general_knowledge_bucket": "Comprehensive",
    "tool_usage": "yes",
}

result = build_embedding_text(sample_model)

print("Embedding text:\n")
print(result["embedding_text"])
print("\nMetadata:\n")
print(result["metadata"])
