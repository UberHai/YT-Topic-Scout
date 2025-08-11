import React, { useState, useEffect } from 'react';
import VideoResult from './VideoResult';
import TrendChart from './TrendChart';
import ChannelAnalysis from './ChannelAnalysis';
import SearchHistory from './SearchHistory';
import './Dashboard.css';

const Dashboard = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('topic');
  const [results, setResults] = useState([]);
  const [trendTopic, setTrendTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analyzedChannelId, setAnalyzedChannelId] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState({ query: '', type: '' });

  useEffect(() => {
    const performSearch = async () => {
      const { query: currentQuery, type: currentSearchType } = submittedQuery;
      if (!currentQuery.trim()) {
        return;
      }
      
      setError(null);

      if (currentSearchType === 'topic') {
        setLoading(true);
        setResults([]);
        setTrendTopic(currentQuery);
        setAnalyzedChannelId('');
        try {
          // Try streaming endpoint first for faster perceived load
          const resp = await fetch(`/api/search/stream?query=${encodeURIComponent(currentQuery)}`);
          if (resp.ok && resp.headers.get('content-type')?.includes('application/x-ndjson')) {
            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            const append = (obj) => setResults((prev) => [...prev, obj]);
            while (true) {
              const { value, done } = await reader.read();
              if (done) break;
              buffer += decoder.decode(value, { stream: true });
              let idx;
              while ((idx = buffer.indexOf('\n')) >= 0) {
                const line = buffer.slice(0, idx).trim();
                buffer = buffer.slice(idx + 1);
                if (!line) continue;
                try {
                  const obj = JSON.parse(line);
                  if (obj.done) continue;
                  if (!obj.title) continue;
                  append(obj);
                } catch {}
              }
            }
          } else {
            // Fallback to non-streaming
            const response = await fetch(`/api/search?query=${encodeURIComponent(currentQuery)}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            setResults(data.results || []);
          }
        } catch (e) {
          setError(e.message);
        } finally {
          setLoading(false);
        }
      } else if (currentSearchType === 'channel') {
        setTrendTopic('');
        setResults([]);
        setAnalyzedChannelId(currentQuery);
      }
    };

    performSearch();
  }, [submittedQuery]);

  const handleSearchClick = () => {
    setSubmittedQuery({ query, type: searchType });
  };

  const handleChannelAnalysis = (channelId) => {
    setQuery(channelId);
    setSearchType('channel');
    setSubmittedQuery({ query: channelId, type: 'channel' });
  };

  const handleSearchAgain = (q) => {
    setQuery(q);
    setSearchType('topic');
    setSubmittedQuery({ query: q, type: 'topic' });
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1 className="header-title">YouTube Topic Scout</h1>
        <div className="search-area">
          <div className="unified-search-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={searchType === 'topic' ? 'Enter a topic...' : 'Enter a channel ID...'}
              className="search-input"
              onKeyDown={(e) => e.key === 'Enter' && handleSearchClick()}
            />
            <select value={searchType} onChange={(e) => setSearchType(e.target.value)}>
              <option value="topic">Topic</option>
              <option value="channel">Channel</option>
            </select>
            <button onClick={handleSearchClick} disabled={loading} className="search-button">
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </header>
      <main className="dashboard-main">
        <div className="dashboard-content">
          {analyzedChannelId && <ChannelAnalysis channelId={analyzedChannelId} />}
          {trendTopic && (
            <div className="trend-chart-container">
              <h2>Trends for "{trendTopic}"</h2>
              <TrendChart topic={trendTopic} />
            </div>
          )}
          <div className="results-container">
            {loading && <div className="loading-indicator">Loading...</div>}
            {error && <div className="error-message">Error: {error}</div>}
            {results.map((video) => (
              <VideoResult key={video.url} video={video} onChannelClick={handleChannelAnalysis} />
            ))}
          </div>
        </div>
        <aside className="dashboard-sidebar">
          <SearchHistory
            onSearchAgain={handleSearchAgain}
          />
        </aside>
      </main>
    </div>
  );
};

export default Dashboard;