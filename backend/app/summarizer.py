"""Abstractive summarizer using a pre-trained transformer model."""
from __future__ import annotations
import re
import logging
from collections import Counter
from typing import List, Tuple
from dataclasses import dataclass

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

from .logger import logger

# Configure logging
logger = logging.getLogger(__name__)

# Simple regex for word extraction
WORD_RE = re.compile(r"[A-Za-z']+")

@dataclass
class SummaryResult:
    """Container for summary results."""
    summary: str
    keywords: List[str]

class Summarizer:
    """
    Abstractive summarizer using a pre-trained model from Hugging Face.
    This implementation uses 't5-small', a model that offers a good balance
    between performance and resource usage.
    """
    
    def __init__(self):
        """Initializes the tokenizer and model."""
        try:
            # Using t5-small for a balance of speed and quality.
            # For higher quality summaries, 'google/pegasus-xsum' could be used.
            self.model_name = "t5-small"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            logger.info(f"Successfully loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load model '{self.model_name}': {e}")
            # Fallback to a non-functional state if model loading fails
            self.tokenizer = None
            self.model = None

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """A simple keyword extraction method."""
        if not text:
            return []
        # A basic stopword list; can be expanded.
        stopwords = set(["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"])
        words = WORD_RE.findall(text.lower())
        # Filter out stopwords and short words
        meaningful_words = [w for w in words if w not in stopwords and len(w) > 2]
        return [word for word, _ in Counter(meaningful_words).most_common(max_keywords)]

    def summarize_text(self, text: str, max_length: int = 150, min_length: int = 40, max_keywords: int = 5) -> SummaryResult:
        """
        Generates an abstractive summary of the given text.
        """
        if not self.model or not self.tokenizer:
            return SummaryResult(
                summary="Summarizer model is not available.",
                keywords=[]
            )

        if not text or not text.strip():
            return SummaryResult(
                summary="No content available for summarization.",
                keywords=[]
            )

        # Prepending "summarize: " is a common practice for T5 models
        input_text = f"summarize: {text}"
        
        inputs = self.tokenizer.encode(
            input_text,
            return_tensors="pt",
            max_length=1024,
            truncation=True
        )

        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs,
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
        
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        # Extract keywords from the original text
        keywords = self._extract_keywords(text, max_keywords=max_keywords)
        
        return SummaryResult(
            summary=summary,
            keywords=keywords
        )

# Global summarizer instance
summarizer = Summarizer()

def summarise_video(meta: dict, max_sent: int = 3, max_keywords: int = 5) -> Tuple[str, List[str]]:
    """
    Legacy interface for backward compatibility.
    Summarizes video content using the abstractive model.
    Note: `max_sent` is no longer directly applicable but the interface is kept.
    """
    text = " ".join([meta.get("description", ""), meta.get("transcript", "")])
    
    # The new summarizer returns a SummaryResult object
    result = summarizer.summarize_text(text, max_keywords=max_keywords)
    
    return result.summary, result.keywords

def get_detailed_summary(meta: dict) -> SummaryResult:
    """Get detailed summary with all metadata."""
    text = " ".join([meta.get("description", ""), meta.get("transcript", "")])
    return summarizer.summarize_text(text)

def extract_topics(text: str, num_topics: int = 5) -> List[str]:
    """Extract main topics from text."""
    if not text.strip():
        return []
    
    # Re-using the internal keyword extraction for topic modeling
    return summarizer._extract_keywords(text, max_keywords=num_topics)
