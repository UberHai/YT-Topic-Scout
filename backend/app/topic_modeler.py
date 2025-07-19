from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

class TopicModeler:
    """
    A class to perform topic modeling using the BERTopic library.
    """

    def __init__(self):
        """
        Initializes the TopicModeler by loading the BERTopic model.
        """
        # Using CountVectorizer to handle potential stop words if needed
        vectorizer_model = CountVectorizer(ngram_range=(1, 2), stop_words="english")
        self.model = BERTopic(vectorizer_model=vectorizer_model, verbose=True)

    def extract_topics(self, documents):
        """
        Extracts topics from a list of documents.

        Args:
            documents (list of str): A list of documents (transcripts).

        Returns:
            list: A list of identified topics.
        """
        topics, _ = self.model.fit_transform(documents)
        
        # Get the most frequent topics
        frequent_topics = self.model.get_topic_info()
        
        return frequent_topics.to_dict(orient="records")