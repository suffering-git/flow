import os
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

def fetch_comments_bare_minimum(youtube, video_id: str, fetch_number: int):
    """Fetch comments for a single video"""
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100
        )
        response = request.execute()
        
        comment_count = len(response.get('items', []))
        return {
            'success': True,
            'count': comment_count,
            'fetch_number': fetch_number
        }
    
    except HttpError as e:
        if 'commentsDisabled' in str(e):
            return {'success': False, 'error': 'Comments disabled', 'fetch_number': fetch_number}
        else:
            return {'success': False, 'error': str(e), 'fetch_number': fetch_number}
    except Exception as e:
        return {'success': False, 'error': str(e), 'fetch_number': fetch_number}

def profile_synchronous_fetches(video_id: str, num_fetches: int = 100):
    load_dotenv()
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    if not youtube_api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file.")
        return

    youtube = build("youtube", "v3", developerKey=youtube_api_key)
    
    print(f"Starting {num_fetches} synchronous comment fetches for video ID: {video_id}")
    print("=" * 70)
    
    results = []
    individual_times = []
    
    overall_start = time.time()
    
    for i in range(num_fetches):
        fetch_start = time.time()
        result = fetch_comments_bare_minimum(youtube, video_id, i + 1)
        fetch_end = time.time()
        
        fetch_time = fetch_end - fetch_start
        individual_times.append(fetch_time)
        results.append(result)
        
        # Print progress every 10 fetches
        if (i + 1) % 10 == 0:
            print(f"Completed {i + 1}/{num_fetches} fetches | Last fetch: {fetch_time:.3f}s")
    
    overall_end = time.time()
    total_time = overall_end - overall_start
    
    # Calculate statistics
    successful_fetches = sum(1 for r in results if r['success'])
    failed_fetches = num_fetches - successful_fetches
    avg_time = sum(individual_times) / len(individual_times)
    min_time = min(individual_times)
    max_time = max(individual_times)
    
    # Print results
    print("\n" + "=" * 70)
    print("PROFILING RESULTS")
    print("=" * 70)
    print(f"Total fetches:        {num_fetches}")
    print(f"Successful fetches:   {successful_fetches}")
    print(f"Failed fetches:       {failed_fetches}")
    print(f"\nTotal time:           {total_time:.2f} seconds")
    print(f"Average time/fetch:   {avg_time:.3f} seconds")
    print(f"Min time:             {min_time:.3f} seconds")
    print(f"Max time:             {max_time:.3f} seconds")
    print(f"Fetches per second:   {num_fetches / total_time:.2f}")
    print("=" * 70)
    
    # Show any errors
    errors = [r for r in results if not r['success']]
    if errors:
        print(f"\nErrors encountered: {len(errors)}")
        for err in errors[:5]:  # Show first 5 errors
            print(f"  Fetch #{err['fetch_number']}: {err['error']}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")

if __name__ == "__main__":
    VIDEO_ID_TO_CHECK = 'kJQP7kiw5Fk'
    profile_synchronous_fetches(VIDEO_ID_TO_CHECK, num_fetches=100)