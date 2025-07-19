import React, { useState } from 'react';
import VideoResult from './VideoResult';
import TrendChart from './TrendChart';
import ChannelAnalysis from './ChannelAnalysis';
import SearchHistory from './SearchHistory';
import '../App.css';

const Dashboard = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [trendTopic, setTrendTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [channelId, setChannelId] = useState('');
  const [submittedChannelId, setSubmittedChannelId] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search topic.');
      return;
    }
    setLoading(true);
    setError(null);
    setResults([]);
    setTrendTopic(query);

    try {
      const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
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

  const handleChannelSearch = () => {
    setSubmittedChannelId(channelId);
  };

  return (
    <div className="dashboard">
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
        <div className="search-container">
          <input
            type="text"
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            placeholder="Enter a channel ID for analysis..."
            className="search-input"
            onKeyDown={(e) => e.key === 'Enter' && handleChannelSearch()}
          />
          <button onClick={handleChannelSearch} className="search-button">
            Analyze Channel
          </button>
        </div>
      </header>
      <main className="dashboard-main">
        <div className="dashboard-left">
          {submittedChannelId && <ChannelAnalysis channelId={submittedChannelId} />}
          {trendTopic && (
            <div className="trend-chart-container">
              <h2>Trends for "{trendTopic}"</h2>
              <TrendChart topic={trendTopic} />
            </div>
          )}
          <div className="results-container">
            {loading && <div className="loading-indicator">Loading...</div>}
            {error && <div className="error-message">Error: {error}</div>}
            {results.map((video, index) => (
              <VideoResult key={index} video={video} onChannelClick={setSubmittedChannelId} />
            ))}
          </div>
        </div>
        <div className="dashboard-right">
          <SearchHistory onSearchAgain={(q) => {
            setQuery(q);
            handleSearch();
          }}/>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;