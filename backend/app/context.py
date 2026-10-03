"""Local token budget and extractive recall, scoped to the submitted conversation."""
from functools import lru_cache
from pathlib import Path
import json
import re
import sys
import unicodedata


@lru_cache(maxsize=1)
def tokenizer():
    from tokenizers import Tokenizer
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    return Tokenizer.from_file(str(root / 'assets/qwen3-tokenizer.json'))


def tokens(text, model):
    if model == 'qwen3:8b':
        return len(tokenizer().encode(text, add_special_tokens=False).ids)
    return len(text.encode('utf-8'))


def clip(text, budget, model, tail=False):
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        value = text[-mid:] if tail else text[:mid]
        if tokens(value, model) <= budget:
            lo = mid
        else:
            hi = mid - 1
    return (text[-lo:] if tail else text[:lo]) if lo else ''


def words(text):
    normalized = unicodedata.normalize('NFKD', text.lower())
    return set(re.findall(r'[a-z0-9_]{4,}', ''.join(c for c in normalized if not unicodedata.combining(c))))


def recall(turns, question, budget, model):
    """Retrieve bounded verbatim excerpts, never invent a generated memory."""
    query = words(question) - {'para', 'como', 'qual', 'quais', 'sobre', 'voce', 'isso', 'mais', 'pode'}
    candidates = []
    for index, turn in enumerate(turns):
        for start in range(0, len(turn.content), 800):
            excerpt = turn.content[start:start + 1000]
            score = len(query & words(excerpt))
            if score:
                candidates.append((score, index, start, turn.role, excerpt))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = []
    for _, index, start, role, excerpt in candidates[:32]:
        entry = {'turno': index + 1, 'papel': role, 'trecho': excerpt}
        if tokens(json.dumps(selected + [entry], ensure_ascii=False), model) <= budget:
            selected.append(entry)
        if len(selected) == 6:
            break
    return selected
