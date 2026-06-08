class VectorService:
    def __init__(self):
        pass

    def get_embedding(self, text: str) -> list:
        """Converts raw text descriptions into normalized token weights."""
        if not text:
            return []
        return text.lower().split()

    def calculate_similarity(self, words1: list, words2: list) -> float:
        """Calculates keyword match intersection over union."""
        if not words1 or not words2:
            return 0.0
            
        set1 = set(words1)
        set2 = set(words2)
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return float(len(intersection) / len(union))