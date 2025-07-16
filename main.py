"""
CLI entry-point for YouTube Topic-Scout
--------------------------------------

* Searches YouTube for the given query
* Caches raw metadata/transcripts
* Indexes them in SQLite FTS5
* Prints a Rich table of summaries & talking points
* Saves the query + results to data/results/<timestamp>_<query-slug>.json
"""

import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

from rich import print
from rich.table import Table
from rich.console import Console

import database as db
from fetch import fetch_videos
from summarizer import summarise_video

# Constants
MAX_RESULTS = 10


def _slugify(text: str) -> str:
    """File-system-safe slug for query string."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()


def run(query: str, max_results: int = MAX_RESULTS, verbose: bool = False) -> None:
    """Main workflow with enhanced features."""
    if verbose:
        print(f"[dim]Searching for: {query}[/dim]")
    
    # 1) make sure DB schema exists
    db.init_db()

    # 2) fetch fresh videos (if any) and store/crawl them
    fresh = fetch_videos(query, max_results=max_results)
    if fresh:
        db.add_videos(fresh)

    # 3) keyword search the local DB
    vids = db.search(query, limit=max_results)
    if not vids:
        print("[yellow]No cached matches; showing freshly fetched results only.[/yellow]")
        vids = fresh

    # 4) build Rich table & export payload
    table = Table(
        title=f"Results for [bold cyan]{query}",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_black",
    )
    
    table.add_column("Title", style="bold", min_width=40, max_width=60)
    table.add_column("Channel", style="green", min_width=15, max_width=25)
    table.add_column("Summary & Talking Points", style="dim")

    export_items = []

    for vid in vids:
        summary, bullets = summarise_video(vid)
        bullet_lines = "\n • ".join(bullets)
        table.add_row(
            f"[link={vid['url']}]{vid['title']}[/link]", 
            vid["channel"],
            f"{summary}\n • {bullet_lines}"
        )

        export_items.append(
            {
                "title": vid["title"],
                "channel": vid["channel"],
                "url": vid["url"],
                "summary": summary,
                "talking_points": bullets,
            }
        )

    print(table)

    # 5) write query + results to JSON file
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = results_dir / f"{timestamp}_{_slugify(query)[:50]}.json"

    payload = {
        "query": query,
        "timestamp": timestamp,
        "results": export_items,
    }
    outfile.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[green]Saved results to {outfile}[/green]")


def main():
    """Enhanced CLI with argument parsing."""
    parser = argparse.ArgumentParser(description="YouTube Topic-Scout - Intelligent content discovery")
    parser.add_argument("query", help="Search query for YouTube videos")
    parser.add_argument("--max-results", type=int, default=MAX_RESULTS,
                       help=f"Maximum number of results (default: {MAX_RESULTS})")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    try:
        run(args.query, max_results=args.max_results, verbose=args.verbose)
    except KeyboardInterrupt:
        print("\n[yellow]Search cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
