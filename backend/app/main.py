from fastapi.responses import Response
from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from . import database as db
from . import fetch
from . import summarizer
from . import sentiment_analyzer
from . import topic_modeler
import re
from datetime import timedelta

app = FastAPI(
    title="YouTube Topic-Scout API",
    description="API for searching and summarizing YouTube videos.",
    version="1.0.0",
)

# Initialize the TopicModeler
sentiment_analyzer_instance = sentiment_analyzer.SentimentAnalyzer()
topic_modeler_instance = topic_modeler.TopicModeler()

class TopicRequest(BaseModel):
    transcripts: List[str]

@app.on_event("startup")
async def startup_event():
    """Initialize the database on application startup."""
    db.init_db()

@app.get("/api/search")
async def search_videos(query: str, max_results: Optional[int] = 10):
    """
    Search for YouTube videos, store them, and return summarized results.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")

    try:
        # 1. Fetch fresh videos from YouTube
        fresh_videos = fetch.fetch_videos(query, max_results=max_results)
        if fresh_videos:
            db.add_videos(fresh_videos)

        # 2. Search the local database
        videos = db.search(query, limit=max_results)
        if not videos:
            # If no cached matches, use the freshly fetched ones
            videos = fresh_videos

        # 3. Summarize the results
        results = []
        for vid in videos:
            summary, bullets = summarizer.summarise_video(vid)
            results.append(
                {
                    "title": vid["title"],
                    "channel": vid["channel"],
                    "url": vid["url"],
                    "summary": summary,
                    "talking_points": bullets,
                }
            )

        # 4. Save search to history
        db.add_search_to_history(query, results)

        return {"query": query, "results": results}

    except fetch.YouTubeAPIError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/api/history")
async def get_search_history():
    """
    Retrieve the list of all past searches.
    """
    try:
        history = db.get_search_history()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/api/export/{search_id}")
async def export_search_result(search_id: int):
    """
    Export the results of a specific search in a user-friendly format.
    """
    try:
        result = db.get_search_result(search_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Search ID not found.")

        # Format as a simple text file for now
        output = f"Search Result for ID: {search_id}\n\n"
        for item in result:
            output += f"Title: {item['title']}\n"
            output += f"Channel: {item['channel']}\n"
            output += f"URL: {item['url']}\n"
            output += f"Summary: {item['summary']}\n"
            output += "--------------------------------------------------\n"

        return Response(content=output, media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/api/sentiment/{video_id}")
async def get_sentiment(video_id: str):
    """
    Analyze the sentiment of comments for a given video.
    """
    if not video_id:
        raise HTTPException(status_code=400, detail="Video ID cannot be empty.")

    try:
        # 1. Fetch comments for the video
        comments = fetch._fetch_comments(video_id)
        if not comments:
            return {"video_id": video_id, "sentiment": {"positive": 0.0, "negative": 0.0, "neutral": 100.0}, "comment_count": 0}

        # 2. Analyze sentiment
        sentiment = sentiment_analyzer_instance.analyze_sentiment(comments)

        return {"video_id": video_id, "sentiment": sentiment, "comment_count": len(comments)}

    except fetch.YouTubeAPIError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
@app.get("/api/trends/{topic}")
async def get_trends(topic: str):
    """
    Get trend analysis data for a given topic.
    """
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    try:
        trend_data = db.get_trend_data(topic)
        return {"topic": topic, "trend_data": trend_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

def _parse_duration(duration_str: str) -> timedelta:
    """Parses ISO 8601 duration format."""
    if not duration_str or duration_str.startswith('P0D'):
        return timedelta()
    
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return timedelta()
    
    hours, minutes, seconds = match.groups(default='0')
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))

@app.get("/api/channel/{channel_id}")
async def analyze_channel(channel_id: str):
    """
    Analyze a YouTube channel's content.
    """
    if not channel_id:
        raise HTTPException(status_code=400, detail="Channel ID cannot be empty.")

    try:
        # 1. Fetch all videos from the channel
        videos = fetch.fetch_channel_videos(channel_id)
        if not videos:
            return {"channel_id": channel_id, "analysis": "No videos found for this channel."}

        # 2. Perform analysis
        # Most common topics
        transcripts = [vid["transcript"] for vid in videos if vid["transcript"]]
        topics = topic_modeler_instance.extract_topics(transcripts) if transcripts else []

        # Average video length
        total_duration = sum(_parse_duration(vid["duration"]).total_seconds() for vid in videos)
        average_length_seconds = total_duration / len(videos) if videos else 0

        # Most-viewed videos
        most_viewed = sorted(videos, key=lambda x: x.get('view_count', 0), reverse=True)[:5]

        analysis = {
            "total_videos": len(videos),
            "most_common_topics": topics,
            "average_video_length_seconds": average_length_seconds,
            "most_viewed_videos": [
                {
                    "title": v["title"],
                    "url": v["url"],
                    "view_count": v.get("view_count", 0)
                }
                for v in most_viewed
            ]
        }

        return {"channel_id": channel_id, "analysis": analysis}

    except fetch.YouTubeAPIError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
 
@app.get("/")
def read_root():
    return {"message": "Welcome to the YouTube Topic-Scout API"}