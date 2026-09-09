import json

from workflows.raindrop_motamem_sync import motamem_urls, write_urls


def test_motamem_urls_filters_and_deduplicates():
    items = [
        {"link": "https://motamem.org/a"},
        {"link": "https://example.com/no"},
        {"link": "https://motamem.org/a"},
        {"link": "http://motamem.org/not-prefix"},
    ]
    assert motamem_urls(items) == ["https://motamem.org/a"]


def test_write_urls_creates_json_array(tmp_path):
    output = tmp_path / "data" / "motamem_urls.json"
    write_urls(["https://motamem.org/درس"], output)
    assert json.loads(output.read_text(encoding="utf-8")) == ["https://motamem.org/درس"]
