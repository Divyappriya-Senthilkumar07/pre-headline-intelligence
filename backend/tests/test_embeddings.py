import pytest
from app.services.embedding_service import MultilingualEmbeddingService


def test_multilingual_embedding_generation_and_dimension():
    """Test 9 & 10: Multilingual vector generation with 384D normalization."""
    embedder = MultilingualEmbeddingService()

    # English text
    vec_en = embedder.embed_text("State Pollution Control Board conducts scheduled plant inspection.")
    assert len(vec_en) == 384
    assert any(x != 0.0 for x in vec_en)

    # Tamil text
    vec_ta = embedder.embed_text("தொழிற்சாலையில் மாசுக்கட்டுப்பாட்டு வாரிய அதிகாரிகள் திடீர் ஆய்வு.")
    assert len(vec_ta) == 384

    # Hindi text
    vec_hi = embedder.embed_text("प्रदूषण नियंत्रण बोर्ड के अधिकारियों ने संयंत्र का निरीक्षण किया।")
    assert len(vec_hi) == 384


def test_vector_similarity_search():
    """Test 11: Cosine similarity search across cross-lingual semantic pairs."""
    embedder = MultilingualEmbeddingService()

    # Semantically related: Tamil & English inspection texts
    text_en_inspection = "Officials conduct environmental inspection at manufacturing plant."
    text_ta_inspection = "தொழிற்சாலை வளாகத்தில் அதிகாரிகள் ஆய்வு மேற்கொண்டனர்."

    # Unrelated: sports / entertainment text
    text_unrelated = "Local cricket tournament concludes with weekend final match."

    vec_en = embedder.embed_text(text_en_inspection)
    vec_ta = embedder.embed_text(text_ta_inspection)
    vec_unrel = embedder.embed_text(text_unrelated)

    sim_related = MultilingualEmbeddingService.cosine_similarity(vec_en, vec_ta)
    sim_unrelated = MultilingualEmbeddingService.cosine_similarity(vec_en, vec_unrel)

    # Related cross-lingual articles must have significantly higher similarity than unrelated topics
    assert sim_related > sim_unrelated
