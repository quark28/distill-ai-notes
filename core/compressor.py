import re
import spacy

try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    nlp = None

_SENSITIVE_PATTERNS = [
    re.compile(r'(password|pass|пароль)\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'(token|key|ключ)\s*[:=]\s*\S+', re.IGNORECASE),
]


def _redact_sensitive(text: str) -> str:
    for pattern in _SENSITIVE_PATTERNS:
        text = pattern.sub(lambda m: f"{m.group(1)}: [REDACTED]", text)
    return text

_CODE_BLOCK_RE = re.compile(r'```.*?```', re.DOTALL)

_CRITICAL_WHITELIST = {
    "не", "ни", "нет", "без", "нельзя", "кроме", "только",
    "если", "но", "однако", "хотя", "никогда", "всегда",
}

_KEEP_PUNCT = {".", "!", "?", ","}


def _compress_plain_text(text: str) -> str:
    if not nlp or not text.strip():
        return text.strip()

    doc = nlp(text)
    parts = []

    for token in doc:
        word_lower = token.text.lower()

        is_critical = word_lower in _CRITICAL_WHITELIST
        is_kept_punct = token.text in _KEEP_PUNCT
        is_content_word = (
            not token.is_stop
            and not token.is_punct
            and token.pos_ in ("NOUN", "VERB", "ADJ", "ADV", "PROPN", "NUM")
        )

        if is_critical or is_kept_punct or is_content_word:
            parts.append(token.text + token.whitespace_)

    return "".join(parts).strip()


def custom_compressor(text: str) -> str:
    text = _redact_sensitive(text)

    segments = _CODE_BLOCK_RE.split(text)
    code_blocks = _CODE_BLOCK_RE.findall(text)

    result = [_compress_plain_text(segments[0])]
    for code, segment in zip(code_blocks, segments[1:]):
        result.append(code)
        result.append(_compress_plain_text(segment))

    return " ".join(part for part in result if part).strip()