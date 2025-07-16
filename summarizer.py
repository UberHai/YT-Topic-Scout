"""Enhanced summarizer with improved algorithms and performance."""
from __future__ import annotations
import re
import logging
from collections import Counter, defaultdict
from typing import List, Tuple, Dict
from dataclasses import dataclass

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
from nltk.tag import pos_tag

from logger import logger

# Ensure required NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')

STOPWORDS = set(stopwords.words("english"))
STEMMER = PorterStemmer()
WORD_RE = re.compile(r"[A-Za-z']+")

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """Container for summary results."""
    summary: str
    keywords: List[str]
    key_phrases: List[str]
    word_count: int
    sentence_count: int


class TextProcessor:
    """Advanced text processing for summarization."""
    
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stopwords = STOPWORDS
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s.!?,:;\-\']', ' ', text)
        return text.strip()
    
    def extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text."""
        words = WORD_RE.findall(text.lower())
        return [w for w in words if w not in self.stopwords and len(w) > 2]
    
    def extract_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        """Extract key phrases using POS tagging."""
        try:
            sentences = sent_tokenize(text)
            phrases = []
            
            for sentence in sentences:
                tokens = word_tokenize(sentence.lower())
                tagged = pos_tag(tokens)
                
                # Extract noun phrases (NN + NNS)
                current_phrase = []
                for word, tag in tagged:
                    if tag.startswith('NN') and word not in self.stopwords:
                        current_phrase.append(word)
                    elif current_phrase:
                        if len(current_phrase) > 1:
                            phrases.append(' '.join(current_phrase))
                        current_phrase = []
                
                if current_phrase and len(current_phrase) > 1:
                    phrases.append(' '.join(current_phrase))
            
            # Count and return most common phrases
            phrase_counts = Counter(phrases)
            return [p for p, _ in phrase_counts.most_common(max_phrases)]
            
        except Exception as e:
            logger.warning(f"Error extracting phrases: {e}")
            return []


class Summarizer:
    """Enhanced extractive summarizer with multiple algorithms."""
    
    def __init__(self):
        self.processor = TextProcessor()
    
    def _calculate_sentence_scores(self, sentences: List[str], text: str) -> Dict[str, float]:
        """Calculate sentence importance scores using multiple factors."""
        if not sentences:
            return {}
        
        # Word frequency scores
        words = self.processor.extract_words(text)
        word_freq = Counter(words)
        
        # Sentence scores
        scores = {}
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_words = self.processor.extract_words(sentence)
            
            if not sentence_words:
                continue
            
            # Frequency score
            freq_score = sum(word_freq[word] for word in sentence_words) / len(sentence_words)
            
            # Position score (earlier sentences get higher scores)
            position_score = 1.0 / (sentences.index(sentence) + 1)
            
            # Length score (prefer medium-length sentences)
            word_count = len(sentence_words)
            if 10 <= word_count <= 30:
                length_score = 1.0
            else:
                length_score = 0.5
            
            # Combine scores
            total_score = (freq_score * 0.6 + position_score * 0.3 + length_score * 0.1)
            scores[sentence] = total_score
        
        return scores
    
    def summarize_text(self, text: str, max_sentences: int = 3, max_keywords: int = 5) -> SummaryResult:
        """Generate comprehensive summary of text."""
        if not text or not text.strip():
            return SummaryResult(
                summary="No content available for summarization.",
                keywords=[],
                key_phrases=[],
                word_count=0,
                sentence_count=0
            )
        
        # Clean text
        text = self.processor.clean_text(text)
        
        # Tokenize sentences
        sentences = sent_tokenize(text)
        if not sentences:
            return SummaryResult(
                summary="No sentences found in content.",
                keywords=[],
                key_phrases=[],
                word_count=0,
                sentence_count=0
            )
        
        # Calculate scores and select top sentences
        scores = self._calculate_sentence_scores(sentences, text)
        
        if not scores:
            return SummaryResult(
                summary=text[:200] + "..." if len(text) > 200 else text,
                keywords=[],
                key_phrases=[],
                word_count=len(text.split()),
                sentence_count=len(sentences)
            )
        
        # Select top sentences
        top_sentences = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: sentences.index(x[0]))  # Maintain order
        
        summary = " ".join(sentence for sentence, _ in top_sentences)
        
        # Extract keywords
        words = self.processor.extract_words(text)
        keyword_counts = Counter(words)
        keywords = [word for word, _ in keyword_counts.most_common(max_keywords)]
        
        # Extract key phrases
        key_phrases = self.processor.extract_phrases(text, max_phrases=max_keywords)
        
        return SummaryResult(
            summary=summary,
            keywords=keywords,
            key_phrases=key_phrases,
            word_count=len(words),
            sentence_count=len(sentences)
        )


# Global summarizer instance
summarizer = Summarizer()


def summarise_video(meta: dict, max_sent: int = 3, max_keywords: int = 5) -> Tuple[str, List[str]]:
    """Legacy interface for backward compatibility."""
    text = " ".join([meta.get("description", ""), meta.get("transcript", "")])
    
    result = summarizer.summarize_text(
        text, 
        max_sentences=max_sent, 
        max_keywords=max_keywords
    )
    
    # Combine keywords and key phrases for richer results
    all_keywords = result.keywords + result.key_phrases
    all_keywords = list(dict.fromkeys(all_keywords))  # Remove duplicates
    
    return result.summary, all_keywords[:max_keywords]


def get_detailed_summary(meta: dict) -> SummaryResult:
    """Get detailed summary with all metadata."""
    text = " ".join([meta.get("description", ""), meta.get("transcript", "")])
    return summarizer.summarize_text(text)


def extract_topics(text: str, num_topics: int = 5) -> List[str]:
    """Extract main topics from text."""
    if not text.strip():
        return []
    
    words = summarizer.processor.extract_words(text)
    topics = [word for word, _ in Counter(words).most_common(num_topics)]
    return topics
