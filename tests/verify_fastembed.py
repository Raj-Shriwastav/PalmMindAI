#!/usr/bin/env python3
import sys
import time


def verify_fastembed():
    print("--------------------------------------------------")
    print("Verifying FastEmbed installation and model loading...")
    print("--------------------------------------------------")

    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("\n[ERROR] 'fastembed' is not installed in your Python environment.")
        print("Please install it by running:")
        print("  pip install fastembed")
        return False

    print("\n[SUCCESS] 'fastembed' module imported successfully!")

    # We use Snowflake/snowflake-arctic-embed-m as specified
    model_name = "Snowflake/snowflake-arctic-embed-m"
    print(f"Loading embedding model: {model_name}...")
    print(
        "Note: If this is the first time, FastEmbed will download the model weight (~400MB for Arctic) automatically."
    )

    try:
        start_time = time.time()
        # Initialize fastembed TextEmbedding
        model = TextEmbedding(model_name=model_name)
        load_duration = time.time() - start_time
        print(f"[SUCCESS] Model loaded successfully in {load_duration:.2f} seconds!")

        # Test text embedding
        sentences = [
            "FastEmbed is a lightweight and fast Python library built for generating text embeddings.",
            "It is optimized for CPU and works out-of-the-box without complex setup.",
        ]

        print("\nGenerating embeddings for sample sentences...")
        start_time = time.time()
        embeddings = list(model.embed(sentences))
        embed_duration = time.time() - start_time

        print(
            f"[SUCCESS] Successfully generated embeddings in {embed_duration:.4f} seconds!"
        )
        for idx, emb in enumerate(embeddings):
            print(f"  Sentence {idx + 1} embedding dimensions: {emb.shape}")
            # Snowflake/snowflake-arctic-embed-m produces 768 dimensional embeddings by default (dense)
            print(f"  First 5 values: {emb[:5]}")

        print("\nFastEmbed is fully functional and ready to use in the RAG pipeline.")
        return True

    except Exception as e:
        print(f"\n[ERROR] An error occurred during FastEmbed initialization/embedding:")
        print(f"Details: {str(e)}")
        print("\nIf downloading is failing, please check your network connection.")
        return False


if __name__ == "__main__":
    success = verify_fastembed()
    sys.exit(0 if success else 1)
