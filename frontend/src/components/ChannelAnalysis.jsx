import React, { useState, useEffect } from 'react';
import './ChannelAnalysis.css';

const ChannelAnalysis = ({ channelId }) => {
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!channelId) {
            setAnalysis(null);
            return;
        }

        const fetchAnalysis = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await fetch(`/api/channel/${channelId}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                setAnalysis(data);
            } catch (error) {
                setError(error.message);
            } finally {
                setLoading(false);
            }
        };

        fetchAnalysis();
    }, [channelId]);

    if (loading) {
        return <div className="loading-indicator">Loading channel analysis...</div>;
    }

    if (error) {
        return <div className="error-message">Error: {error}</div>;
    }

    if (!analysis) {
        return <div>Enter a channel ID to see the analysis.</div>;
    }

    const formatDuration = (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        return `${hours}h ${minutes}m ${remainingSeconds.toFixed(0)}s`;
    };

    return (
        <div className="channel-analysis">
            <h2>Channel Analysis: <em>{channelId}</em></h2>
            
            <section>
                <h3>Most Common Topics</h3>
                <ul>
                    {analysis.topics && analysis.topics.length > 0 ? (
                        analysis.topics.map((topic, index) => <li key={index}>{topic}</li>)
                    ) : (
                        <li>No topics found.</li>
                    )}
                </ul>
            </section>

            <section>
                <h3>Average Video Length</h3>
                <p>{analysis.average_video_length ? formatDuration(analysis.average_video_length) : 'N/A'}</p>
            </section>

            <section>
                <h3>Most Viewed Videos</h3>
                <ul>
                    {analysis.most_viewed_videos && analysis.most_viewed_videos.length > 0 ? (
                        analysis.most_viewed_videos.map((video) => (
                            <li key={video.video_id}>
                                <a href={`https://www.youtube.com/watch?v=${video.video_id}`} target="_blank" rel="noopener noreferrer">
                                    {video.title}
                                </a>
                                <span> - {video.views.toLocaleString()} views</span>
                            </li>
                        ))
                    ) : (
                        <li>No videos found.</li>
                    )}
                </ul>
            </section>
        </div>
    );
};

export default ChannelAnalysis;