import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

def fetch_comments_bare_minimum(video_id: str):
    load_dotenv()
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    if not youtube_api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file.")
        return

    youtube = build("youtube", "v3", developerKey=youtube_api_key)

    all_comments = []
    next_page_token = None
    
    print(f"Attempting to fetch comments for video ID: {video_id}")

    try:
        while True:
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                all_comments.append({
                    'author_name': comment['authorDisplayName'],
                    'comment_text': comment['textDisplay'],
                    'published_at': comment['publishedAt']
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        if all_comments:
            print(f"\nSuccessfully fetched {len(all_comments)} comments:")
            for i, comment in enumerate(all_comments[:5]): # Print first 5 comments
                print(f"--- Comment {i+1} ---")
                print(f"Author: {comment['author_name']}")
                print(f"Published: {comment['published_at']}")
                print(f"Text: {comment['comment_text']}\n")
            if len(all_comments) > 5:
                print(f"... and {len(all_comments) - 5} more comments.")
        else:
            print("\nNo comments found or fetched for this video.")

    except HttpError as e:
        if 'commentsDisabled' in str(e):
            print(f"Comments are disabled for video ID {video_id}.")
        else:
            print(f"An HTTP error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    VIDEO_ID_TO_CHECK = 'ckaYjKhRV1Y'
    fetch_comments_bare_minimum(VIDEO_ID_TO_CHECK)