from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

class TopicModeler:
    def __init__(self, n_topics=5, n_words=5):
        self.n_topics = n_topics
        self.n_words = n_words
        self.vectorizer = CountVectorizer(stop_words='english')
        self.lda = LatentDirichletAllocation(n_components=self.n_topics, random_state=42)

    def extract_topics(self, transcripts):
        if not transcripts:
            return []

        try:
            # Vectorize the text data
            X = self.vectorizer.fit_transform(transcripts)

            # Fit the LDA model
            self.lda.fit(X)

            # Get the most important words for each topic
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            for topic_idx, topic in enumerate(self.lda.components_):
                top_words_idx = topic.argsort()[:-self.n_words - 1:-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topics.append(f"Topic {topic_idx + 1}: {', '.join(top_words)}")
            
            return topics
        except Exception as e:
            # Handle cases where topic modeling might fail (e.g., empty vocabulary)
            print(f"Error during topic modeling: {e}")
            return ["Could not determine topics"]