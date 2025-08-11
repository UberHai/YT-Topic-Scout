import React from 'react';
import './VideoResult.css';

const VideoResult = ({ video, onChannelClick }) => {
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(video.url);
    } catch (e) {
      // no-op
    }
  };
  const handleChannelClick = () => {
    if (onChannelClick) {
      onChannelClick(video.channel_id);
    }
  };

  const handleCopySummary = async () => {
    try {
      const text = `Title: ${video.title}\nURL: ${video.url}\nSummary: ${video.summary}`;
      await navigator.clipboard.writeText(text);
    } catch (e) {
      // no-op
    }
  };

  return (
    <div className="video-card">
      <h3>
        <a href={video.url} target="_blank" rel="noopener noreferrer">
          {video.title}
        </a>
      </h3>
      <p className="channel-name">
        Channel: <a href={`https://www.youtube.com/channel/${video.channel_id}`} target="_blank" rel="noopener noreferrer">{video.channel}</a>
      </p>
      {video.published_at && (
        <p className="published-date">Published: {new Date(video.published_at).toLocaleDateString()}</p>
      )}
      <div className="video-meta">
        {typeof video.view_count === 'number' && (
          <span className="meta-item">Views: {video.view_count.toLocaleString()}</span>
        )}
        {video.duration && (
          <span className="meta-item">Duration: {video.duration}</span>
        )}
        <button onClick={handleCopy} className="copy-link-button">Copy Link</button>
      </div>
      <button onClick={handleChannelClick} className="analyze-channel-button">
        Analyze Channel
      </button>
      <div className="video-details">
        <h4>Summary:</h4>
        <p>{video.summary}</p>
        <button onClick={handleCopySummary} className="copy-summary-button">Copy Summary</button>
        <h4>Key Talking Points:</h4>
        <ul>
          {video.talking_points.map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default VideoResult;