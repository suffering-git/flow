import asyncio
import json
from query.query_utils import QueryUtils
from database.db_manager import DatabaseManager
from dotenv import load_dotenv

async def print_video_data(video_indices: list[int]):
    load_dotenv()
    db_manager = DatabaseManager("data/youtube_data.db") # Direct access for this script
    
    try:
        # 1. Get all video IDs
        all_videos_rows = db_manager.fetchall("SELECT video_id, video_title FROM Videos ORDER BY published_date DESC")
        all_video_ids = [row['video_id'] for row in all_videos_rows]
        
        print(f"Total videos in database: {len(all_video_ids)}\n")

        for index in video_indices:
            if 0 < index <= len(all_video_ids):
                video_id_to_fetch = all_video_ids[index - 1] # -1 because indices are 1-based
                video_title_to_fetch = all_videos_rows[index - 1]['video_title']

                print(f"--- Data for Video Index: {index} (ID: {video_id_to_fetch}, Title: {video_title_to_fetch}) ---")

                # 2. Fetch raw transcript
                transcript_row = db_manager.fetchone(
                    "SELECT transcript_text, original_language FROM RawTranscripts WHERE video_id = ?",
                    (video_id_to_fetch,)
                )
                if transcript_row:
                    print(f"\nRaw Transcript (Language: {transcript_row['original_language']}):")
                    print(transcript_row['transcript_text'])
                else:
                    print("\nRaw Transcript: Not found.")

                # 3. Fetch raw comments
                comments_rows = db_manager.fetchall(
                    "SELECT comment_text, original_language, author_name FROM RawComments WHERE video_id = ?",
                    (video_id_to_fetch,)
                )
                if comments_rows:
                    print("\nRaw Comments:")
                    for i, comment in enumerate(comments_rows):
                        print(f"  Comment {i+1} by {comment['author_name']} (Language: {comment['original_language']}):")
                        print(f"    {comment['comment_text']}")
                else:
                    print("\nRaw Comments: Not found.")
                print("\n" + "="*80 + "\n")

            else:
                print(f"Video index {index} is out of range. Total videos: {len(all_video_ids)}\n")

    finally:
        db_manager.close()

if __name__ == "__main__":
    # Example usage:
    # To see data for the 45th, 34th, 1st, 56th, and 111th video
    # You can change these indices as needed
    target_indices = [1, 10, 200] 
    asyncio.run(print_video_data(target_indices))
