from __future__ import annotations

import re
from collections import Counter

TOKEN_RE = re.compile(r"[\w一-龥ぁ-んァ-ヴー]{2,}")


def count_tokens(texts: list[str], top_k: int = 80) -> dict[str, int]:
    joined = "\n".join(texts)
    tokens = TOKEN_RE.findall(joined)
    counts = Counter([t.lower() for t in tokens])
    return dict(counts.most_common(top_k))


# TODO(unknown_emerging): add char n-gram / subword extractor for unseen word detection.
