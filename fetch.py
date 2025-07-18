"""Enhanced YouTube fetcher with caching, retries, and error handling."""
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

# Configuration constants
MAX_RESULTS = 10
CACHE_TTL = 3600  # seconds
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 1  # seconds

# Load API key from config
import json
from pathlib import Path

def load_config():
    """Load configuration from config.json."""
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

config = load_config()
YT_KEY = config.get("YOUTUBE_API_KEY")
if not YT_KEY:
    raise RuntimeError("Put your YOUTUBE_API_KEY in config.json")

try:
    yt = build("youtube", "v3", developerKey=YT_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to initialize YouTube API: {e}")

# Cache directories
RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)
CACHE = Path("data/cache")
CACHE.mkdir(parents=True, exist_ok=True)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""
    pass


def _get_cache_key(query: str, max_results: int) -> str:
    """Generate cache key for search queries."""
    content = f"{query}:{max_results}"
    return hashlib.md5(content.encode()).hexdigest()


def _is_cache_valid(cache_file: Path, ttl: int = None) -> bool:
    """Check if cache file is still valid."""
    if not cache_file.exists():
        return False
    
    ttl = ttl or CACHE_TTL
    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
    return file_age.total_seconds() < ttl


def _make_api_request(func, *args, **kwargs):
    """Make API request with retry logic and exponential backoff."""
    max_attempts = API_RETRY_ATTEMPTS
    base_delay = API_RETRY_DELAY
    
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            if e.resp.status in [403, 429]:  # Rate limit or quota exceeded
                if attempt < max_attempts - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"API rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
            raise YouTubeAPIError(f"API request failed: {e}")
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(base_delay)
                continue
            raise
    
    raise YouTubeAPIError("Max retry attempts exceeded")


def _search_ids(query: str, n: int) -> List[str]:
    """Search for video IDs with caching."""
    cache_key = _get_cache_key(f"search:{query}", n)
    cache_file = CACHE / f"search_{cache_key}.json"
    
    # Check cache first
    if _is_cache_valid(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Make API request
    print(f"Searching YouTube for: {query}")
    resp = _make_api_request(
        lambda: yt.search().list(
            q=query, 
            part="snippet", 
            type="video", 
            maxResults=n,
            order="relevance"
        ).execute()
    )
    
    video_ids = [item["id"]["videoId"] for item in resp["items"]]
    
    # Cache results
    try:
        with open(cache_file, 'w') as f:
            json.dump(video_ids, f)
    except Exception:
        pass
    
    return video_ids


def _details(ids: List[str]) -> List[Dict]:
    """Get video details with batching and caching."""
    if not ids:
        return []
    
    # Process in batches to avoid API limits
    batch_size = 50  # YouTube API limit
    all_details = []
    
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_details = _get_batch_details(batch_ids)
        all_details.extend(batch_details)
    
    return all_details


def _get_batch_details(ids: List[str]) -> List[Dict]:
    """Get details for a batch of videos."""
    cache_key = _get_cache_key("details:" + ",".join(ids), 0)
    cache_file = CACHE / f"details_{cache_key}.json"
    
    # Check cache
    if _is_cache_valid(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Make API request
    resp = _make_api_request(
        lambda: yt.videos().list(
            id=",".join(ids), 
            part="snippet,statistics,contentDetails"
        ).execute()
    )
    
    details = resp["items"]
    
    # Cache results
    try:
        with open(cache_file, 'w') as f:
            json.dump(details, f)
    except Exception:
        pass
    
    return details


def _captions(vid: str) -> str:
    """Get video captions with improved error handling."""
    try:
        segs = YouTubeTranscriptApi.get_transcript(vid)
        transcript = " ".join(s["text"] for s in segs)
        return transcript.replace('\n', ' ').strip()
    except TranscriptsDisabled:
        return ""
    except Exception:
        return ""


def fetch_videos(query: str, max_results: int = 10) -> List[Dict]:
    """Enhanced video fetching with comprehensive caching and error handling."""
    if not query.strip():
        return []
    
    try:
        # Search for video IDs
        video_ids = _search_ids(query, max_results)
        if not video_ids:
            return []
        
        # Get video details
        items = _details(video_ids)
        if not items:
            return []
        
        videos = []
        for item in items:
            vid = item["id"]
            cache_file = RAW / f"{vid}.json"
            
            # Build fresh record
            data = {
                "video_id": vid,
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "channel": item["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "transcript": _captions(vid),
                "published_at": item["snippet"].get("publishedAt", ""),
                "duration": item.get("contentDetails", {}).get("duration", ""),
                "view_count": item.get("statistics", {}).get("viewCount", ""),
                "like_count": item.get("statistics", {}).get("likeCount", ""),
                "fetched_at": datetime.now().isoformat(),
            }
            
            # Cache the data
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            
            videos.append(data)
        
        return videos
        
    except Exception as e:
        raise YouTubeAPIError(f"Failed to fetch videos: {e}")
