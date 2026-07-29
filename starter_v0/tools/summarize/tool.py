"""Summarize tool — compress text into key points."""
from __future__ import annotations


def summarize_text(text: str, max_length: int = 3) -> str:
    """Summarize long text into concise bullet points."""
    if not text or len(text) < 100:
        return text or "(empty)"

    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 10]
    if not sentences:
        return text[:500]

    # Simple extractive summary: first sentence + key sentences
    selected = [sentences[0]]
    for s in sentences[1:]:
        if any(kw in s.lower() for kw in ["quan trọng", "important", "key", "main", "chính", "however", "therefore", "result"]):
            selected.append(s)
    if len(selected) < max_length:
        selected += sentences[1:max_length]

    return " • ".join(selected[:max_length]) + "."
