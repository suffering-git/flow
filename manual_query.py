import asyncio
from query.query_utils import QueryUtils
from pprint import pprint

async def main():
    # Create an instance of QueryUtils
    query_utils = QueryUtils()

    # Example 1: Full-text search
    print("--- Full-text search ---")
    results = query_utils.search_text("wheelbarrow")
    for result in results:
        pprint(result)
    print("\n")

    # Example 2: Semantic search
    print("--- Semantic search ---")
    results = await query_utils.search_semantic("carrot")
    for result in results:
        pprint(result)
    print("\n")

    # Example 3: Get insight details
    print("--- Insight details ---")
    # First, get an insight ID from a search
    results = query_utils.search_text("AI")
    if results:
        insight_id = results[0]['insight_id']
        details = query_utils.get_insight_details(insight_id)
        pprint(details)
    print("\n")


    # Close the database connection
    query_utils.close()

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())
