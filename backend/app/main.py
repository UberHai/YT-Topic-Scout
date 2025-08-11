from fastapi.responses import Response
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

from . import database as db
from . import fetch
from . import summarizer
from . import sentiment_analyzer
from . import topic_modeler
from .logger import logger
import re
from datetime import timedelta
import json
from fastapi.responses import StreamingResponse

app = FastAPI(
    title="YouTube Topic-Scout API",
    description="API for searching and summarizing YouTube videos.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Local dev frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
    This endpoint first checks the local database for cached results.
    If the cache is insufficient, it fetches fresh data from the YouTube API.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")

    try:
        # 1. Search the local database first
        videos = db.search(query, limit=max_results)

        # 2. If local results are insufficient, fetch from YouTube (progressive enrichment)
        if len(videos) < max_results:
            try:
                fresh_videos = fetch.fetch_videos(query, max_results=max_results)
                if fresh_videos:
                    # Insert immediately so subsequent local searches find them
                    db.add_videos(fresh_videos)
                    # Progressive: extend the in-memory list now to render quickly
                    existing_ids = {v['video_id'] for v in videos}
                    new_videos = [v for v in fresh_videos if v['video_id'] not in existing_ids]
                    videos.extend(new_videos)
                    videos = videos[:max_results]
            except fetch.YouTubeAPIError as e:
                # If API fails but we have some cached results, proceed with cached
                if not videos:
                    raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")

        # 3. Summarize the results
        results = []
        # Gather latest stats for enrichment
        try:
            video_ids = [dict(v).get("video_id") for v in videos]
            latest_stats = db.get_latest_stats_for_videos(video_ids)
        except Exception:
            latest_stats = {}

        for vid in videos:
            # Convert sqlite3.Row to a standard dictionary
            vid_dict = dict(vid)
            summary, bullets = summarizer.summarise_video(vid_dict)
            stats = latest_stats.get(vid_dict.get("video_id"), {})
            results.append(
                {
                    "title": vid_dict["title"],
                    "channel": vid_dict["channel"],
                    "channel_id": vid_dict.get("channel_id"),
                    "url": vid_dict["url"],
                    "published_at": vid_dict.get("published_at"),
                    "duration": vid_dict.get("duration"),
                    "view_count": stats.get("view_count"),
                    "like_count": stats.get("like_count"),
                    "summary": summary,
                    "talking_points": bullets,
                }
            )

        # 4. Save search to history
        if results:
            db.add_search_to_history(query, results)

        return {"query": query, "results": results}

    except fetch.YouTubeAPIError as e:
        logger.error(f"YouTube API error in search_videos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in search_videos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@app.get("/api/history")
async def get_search_history():
    """
    Retrieve the list of all past searches.
    """
    try:
        history = db.get_search_history()
        return history
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


@app.get("/api/search/stream")
async def search_videos_stream(query: str, max_results: Optional[int] = 10):
    """
    Stream search results as NDJSON for progressive rendering.
    Each line is a JSON object for a single video; the last line may include {"done": true}.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty.")

    async def streamer():
        try:
            # 1) Try local DB results first for instant response
            local_results = db.search(query, limit=max_results)
            for row in local_results:
                vid_dict = dict(row)
                summary, bullets = summarizer.summarise_video(vid_dict)
                payload = {
                    "title": vid_dict["title"],
                    "channel": vid_dict["channel"],
                    "channel_id": vid_dict.get("channel_id"),
                    "url": vid_dict["url"],
                    "published_at": vid_dict.get("published_at"),
                    "duration": vid_dict.get("duration"),
                    "summary": summary,
                    "talking_points": bullets,
                }
                yield json.dumps(payload) + "\n"

            # 2) If we still need more, progressively fetch from YouTube
            if len(local_results) < (max_results or 10):
                try:
                    ids = fetch._search_ids(query, max_results or 10)
                    batch_size = min(10, len(ids)) or 10
                    to_insert = []
                    sent_ids = {dict(r).get("video_id") for r in local_results}

                    for i in range(0, len(ids), batch_size):
                        batch_ids = ids[i:i+batch_size]
                        details = fetch._get_batch_details(batch_ids)
                        for item in details:
                            vid = item["id"]
                            if vid in sent_ids:
                                continue
                            data = {
                                "video_id": vid,
                                "title": item["snippet"]["title"],
                                "description": item["snippet"].get("description", ""),
                                "channel": item["snippet"]["channelTitle"],
                                "channel_id": item["snippet"].get("channelId"),
                                "url": f"https://www.youtube.com/watch?v={vid}",
                                "transcript": fetch._captions(vid),
                                "published_at": item["snippet"].get("publishedAt", ""),
                                "duration": item.get("contentDetails", {}).get("duration", ""),
                            }
                            summary, bullets = summarizer.summarise_video(data)
                            payload = {
                                "title": data["title"],
                                "channel": data["channel"],
                                "channel_id": data.get("channel_id"),
                                "url": data["url"],
                                "published_at": data.get("published_at"),
                                "duration": data.get("duration"),
                                "summary": summary,
                                "talking_points": bullets,
                            }
                            to_insert.append(data)
                            yield json.dumps(payload) + "\n"

                            if max_results and (len(sent_ids) + len(to_insert)) >= max_results:
                                break

                        if to_insert:
                            try:
                                db.add_videos(to_insert)
                            except Exception:
                                pass
                            to_insert = []
                        await asyncio.sleep(0)
                except fetch.YouTubeAPIError:
                    pass
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
        finally:
            yield json.dumps({"done": True}) + "\n"

    return StreamingResponse(streamer(), media_type="application/x-ndjson")

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