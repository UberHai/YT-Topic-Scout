import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SearchHistory = ({ onSearchAgain }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get('/api/history');
        setHistory(response.data);
        setLoading(false);
      } catch {
        setError('Failed to fetch search history.');
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleExport = async (searchId) => {
    try {
      const response = await axios.get(`/api/export/${searchId}`, {
        responseType: 'blob', // Important for file downloads
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
    return <div>Loading search history...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <div className="search-history">
      <h2>Search History</h2>
      {history.length === 0 ? (
        <p>No search history found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Query</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {history.map((search) => (
              <tr key={search.id}>
                <td
                  onClick={() => onSearchAgain(search.query)}
                  style={{cursor: 'pointer', textDecoration: 'underline'}}
                >
                  {search.query}
                </td>
                <td>{new Date(search.timestamp).toLocaleDateString()}</td>
                <td>
                  <button onClick={() => handleExport(search.id)}>
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