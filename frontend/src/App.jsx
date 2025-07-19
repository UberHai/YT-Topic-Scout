import { useState } from 'react';
import './App.css';
import VideoResult from './components/VideoResult';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search topic.');
      return;
    }
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/search?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>YouTube Topic Scout</h1>
        <div className="search-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a topic to search..."
            className="search-input"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} disabled={loading} className="search-button">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </header>
      <main>
        {loading && <div className="loading-indicator">Loading...</div>}
        {error && <div className="error-message">Error: {error}</div>}
        <div className="results-container">
          {results.map((video, index) => (
            <VideoResult key={index} video={video} />
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;
