import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SearchHistory.css';

const SearchHistory = ({ onSearchAgain }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/history');
        setHistory(response.data.history || response.data);
      } catch (err) {
        setError('Failed to fetch search history.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleExport = async (searchId) => {
    try {
      const response = await axios.get(`/api/export/${searchId}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `search-export-${searchId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      console.error('Failed to export search results.', err);
    }
  };

  if (loading) {
    return <div className="loading-indicator">Loading history...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <div className="search-history">
      <h2>Search History</h2>
      {history.length === 0 ? (
        <p>No search history found.</p>
      ) : (
        <table className="search-history-table">
          <thead>
            <tr>
              <th>Query</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {history.map((search) => (
              <tr key={search.search_id || search.query}>
                <td>
                  <span
                    className="search-again-link"
                    onClick={() => onSearchAgain(search.query)}
                  >
                    {search.query}
                  </span>
                </td>
                <td>{new Date(search.timestamp).toLocaleDateString()}</td>
                <td>
                  <button
                    onClick={() => handleExport(search.search_id)}
                    className="export-button"
                  >
                    Export
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SearchHistory;