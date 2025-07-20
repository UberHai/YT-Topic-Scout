import React from 'react';
import './VideoResult.css';

const VideoResult = ({ video, onChannelClick }) => {
  const handleChannelClick = () => {
    if (onChannelClick) {
      onChannelClick(video.channel_id);
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
        Channel: {video.channel}
      </p>
      <button onClick={handleChannelClick} className="analyze-channel-button">
        Analyze Channel
      </button>
      <div className="video-details">
        <h4>Summary:</h4>
        <p>{video.summary}</p>
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