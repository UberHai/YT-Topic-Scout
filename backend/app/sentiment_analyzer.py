"""Sentiment analysis for YouTube comments."""
from transformers import pipeline
from typing import List, Dict

class SentimentAnalyzer:
    """Analyzes the sentiment of a list of comments."""

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initializes the sentiment analysis pipeline.

        Args:
            model_name (str): The name of the Hugging Face model to use.
        """
        try:
            self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
        except Exception as e:
            # Log the error and re-raise to signal a problem with initialization
            print(f"Error initializing sentiment analysis pipeline: {e}")
            raise

    def analyze_sentiment(self, comments: List[str]) -> Dict[str, float]:
        """
        Analyzes the sentiment of a list of comments and returns aggregated results.

        Args:
            comments (List[str]): A list of comments to analyze.

        Returns:
            Dict[str, float]: A dictionary with the percentage of positive,
                              negative, and neutral comments.
        """
        if not comments:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}

        try:
            # The pipeline returns a list of dictionaries like {'label': 'POSITIVE', 'score': 0.999}
            sentiments = self.sentiment_pipeline(comments)
        except Exception as e:
            print(f"Error during sentiment analysis: {e}")
            # Return a neutral score if analysis fails
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0}

        # Aggregate the results
        sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
        for sentiment in sentiments:
            label = sentiment["label"].upper()
            if label in sentiment_counts:
                sentiment_counts[label] += 1
            else:
                # Handle cases where the model might return other labels
                sentiment_counts["NEUTRAL"] += 1
        
        total_comments = len(comments)
        return {
            "positive": (sentiment_counts["POSITIVE"] / total_comments) * 100,
            "negative": (sentiment_counts["NEGATIVE"] / total_comments) * 100,
            "neutral": (sentiment_counts["NEUTRAL"] / total_comments) * 100,
        }