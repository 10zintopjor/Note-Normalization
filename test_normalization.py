import re

from pathlib import Path
from normalize_note import get_normalized_text


def test_normalized_text():
    collated_text = Path('./test.txt').read_text(encoding='utf-8')
    normalized_text = get_normalized_text(collated_text)
    expected_normalized_text = Path('./expected_output.txt').read_text(encoding='utf-8')
    assert normalized_text == expected_normalized_text