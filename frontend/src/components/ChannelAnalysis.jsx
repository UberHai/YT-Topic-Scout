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
                const response = await fetch(`/api/channel/${encodeURIComponent(channelId)}`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const data = await response.json();
                setAnalysis(data?.analysis || null);
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
                    {Array.isArray(analysis.most_common_topics) && analysis.most_common_topics.length > 0 ? (
                        analysis.most_common_topics.map((topic, index) => <li key={index}>{topic}</li>)
                    ) : (
                        <li>No topics found.</li>
                    )}
                </ul>
            </section>

            <section>
                <h3>Average Video Length</h3>
                <p>{typeof analysis.average_video_length_seconds === 'number' ? formatDuration(analysis.average_video_length_seconds) : 'N/A'}</p>
            </section>

            <section>
                <h3>Most Viewed Videos</h3>
                <ul>
                    {Array.isArray(analysis.most_viewed_videos) && analysis.most_viewed_videos.length > 0 ? (
                        analysis.most_viewed_videos.map((video, idx) => (
                            <li key={idx}>
                                <a href={video.url} target="_blank" rel="noopener noreferrer">
                                    {video.title}
                                </a>
                                <span> - {Number(video.view_count || 0).toLocaleString()} views</span>
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