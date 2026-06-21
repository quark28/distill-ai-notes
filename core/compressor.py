import re
import spacy

try:
    nlp = spacy.load("ru_core_news_sm")
except OSError:
    nlp = None

def custom_compressor(text: str) -> str:
    text = re.sub(r'(password|pass|пароль)\s*[:=]\s*[^\s]+', r'\1: [REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'(token|key|ключ)\s*[:=]\s*[^\s]+', r'\1: [REDACTED]', text, flags=re.IGNORECASE)
    
    if not nlp:
        return text.strip()
    
    doc = nlp(text)
    clean_tokens = []
    for token in doc:
        if not token.is_stop and not token.is_punct and token.pos_ in ["NOUN", "VERB", "ADJ", "ADV", "PROPN", "NUM"]:
            clean_tokens.append(token.text)
    
    return " ".join(clean_tokens)