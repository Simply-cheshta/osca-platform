from sentence_transformers import SentenceTransformer
print("Connecting to HuggingFace to fetch text-matching model weights...")
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("\n Success! Model downloaded and stored locally on your machine.")
except Exception as e:
    print(f"\n Network failed with error: {e}")
    