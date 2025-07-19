from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from . import database as db
from . import fetch
from . import summarizer
from . import topic_modeler

app = FastAPI(
    title="YouTube Topic-Scout API",
    description="API for searching and summarizing YouTube videos.",
    version="1.0.0",
)

# Initialize the TopicModeler
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

        return {"query": query, "results": results}

    except fetch.YouTubeAPIError as e:
        raise HTTPException(status_code=500, detail=f"YouTube API error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post("/api/topics")
async def get_topics(request: TopicRequest):
    """
    Extract topics from a list of video transcripts.
    """
    if not request.transcripts:
        raise HTTPException(status_code=400, detail="Transcripts list cannot be empty.")

    try:
        topics = topic_modeler_instance.extract_topics(request.transcripts)
        return {"topics": topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to the YouTube Topic-Scout API"}