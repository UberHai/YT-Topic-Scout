"""Database optimization and maintenance utilities."""
import argparse
import sys
from pathlib import Path

import database as db

def optimize_database():
    """Run database optimization routines."""
    print("Database Optimization")
    print("=" * 30)
    
    # Get current stats
    initial_count = db.get_video_count()
    print(f"Current videos: {initial_count}")
    
    # Vacuum database
    print("Optimizing database size...")
    db.vacuum_db()
    
    # Final stats
    final_count = db.get_video_count()
    print(f"\nOptimization complete!")
    print(f"Final video count: {final_count}")


def show_stats():
    """Display database statistics."""
    print("Database Statistics")
    print("=" * 30)
    
    stats = {
        "Total Videos": db.get_video_count(),
        "Database File": "data/videos.db",
        "Raw Data Dir": "data/raw/",
        "Cache Dir": "data/cache/",
    }
    
    for key, value in stats.items():
        print(f"{key}: {value}")


def main():
    """CLI for optimization utilities."""
    parser = argparse.ArgumentParser(description="Database optimization tools")
    parser.add_argument("command", choices=["optimize", "stats"], 
                       help="Command to run")
    
    args = parser.parse_args()
    
    try:
        if args.command == "optimize":
            optimize_database()
        elif args.command == "stats":
            show_stats()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
