from app.services.deduplication import DeduplicationService


def test_url_canonicalization_and_cleaning():
    """Test 9 & 11: Deduplication URL normalization."""
    # 1. URL with tracking params and trailing slash
    raw_url = "HTTPS://WWW.TheHindu.com/news/national/article-101/?utm_source=twitter&utm_medium=social&utm_campaign=breaking#comments"
    normalized = DeduplicationService.normalize_url(raw_url)
    assert normalized == "https://thehindu.com/news/national/article-101"

    # 2. Re-ordered query parameters
    url_a = "https://news.example.com/item?b=2&a=1"
    url_b = "https://news.example.com/item?a=1&b=2"
    assert DeduplicationService.normalize_url(url_a) == DeduplicationService.normalize_url(url_b)


def test_content_and_file_hashing():
    """Test deterministic SHA256 hashing."""
    text_1 = "Government inspection conducted on Tuesday."
    text_2 = "   Government   inspection   conducted   on   Tuesday.   \n"
    
    hash_1 = DeduplicationService.compute_content_hash(text_1)
    hash_2 = DeduplicationService.compute_content_hash(text_2)
    assert hash_1 == hash_2
    assert len(hash_1) == 64  # SHA256 hex length

    file_bytes_1 = b"PDF_SAMPLE_DATA_12345"
    file_bytes_2 = b"PDF_SAMPLE_DATA_12345"
    assert DeduplicationService.compute_file_hash(file_bytes_1) == DeduplicationService.compute_file_hash(file_bytes_2)
