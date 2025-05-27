import asyncio
import httpx
import aiomysql
from datetime import datetime
from difflib import SequenceMatcher

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'db': 'asssignment1'
}

async def update_db():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://eonet.gsfc.nasa.gov/api/v3/events?limit=50")
        data = response.json().get("events", [])

    pool = await aiomysql.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            insert_query = """
            INSERT IGNORE INTO eonet_events (
                event_id, title, description, link, closed,
                category_id, category_title,
                source_id, source_url,
                magnitude_value, magnitude_unit,
                geometry_date, geometry_type, longitude, latitude
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s
            )
            """

            for event in data:
                event_id = event["id"]
                title = event["title"]
                description = event.get("description")
                link = event["link"]
                closed = event.get("closed")
                closed = datetime.fromisoformat(closed.replace("Z", "")) if closed else None

                category = event["categories"][0] if event["categories"] else {}
                source = event["sources"][0] if event["sources"] else {}
                geometry = event["geometry"][0] if event["geometry"] else {}

                category_id = category.get("id")
                category_title = category.get("title")

                source_id = source.get("id")
                source_url = source.get("url")

                magnitude_value = geometry.get("magnitudeValue")
                magnitude_unit = geometry.get("magnitudeUnit")
                geometry_date = geometry.get("date")
                geometry_date = datetime.fromisoformat(geometry_date.replace("Z", "")) if geometry_date else None
                geometry_type = geometry.get("type")
                coordinates = geometry.get("coordinates", [None, None])
                longitude, latitude = coordinates if len(coordinates) == 2 else (None, None)

                values = (
                    event_id, title, description, link, closed,
                    category_id, category_title,
                    source_id, source_url,
                    magnitude_value, magnitude_unit,
                    geometry_date, geometry_type, longitude, latitude
                )

                await cursor.execute(insert_query, values)

            await conn.commit()

    pool.close()
    await pool.wait_closed()



async def get_description_by_title(input_title):
    print(f"Searching for title: {input_title}")

    pool = await aiomysql.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            query = """
                SELECT title, description 
                FROM eonet_events 
                WHERE MATCH(title) AGAINST(%s IN NATURAL LANGUAGE MODE)
                LIMIT 5
            """
            await cursor.execute(query, (input_title,))
            results = await cursor.fetchall()

            if not results:
                await cursor.execute("SELECT title, description FROM eonet_events")
                all_rows = await cursor.fetchall()

                def similarity(a, b):
                    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

                best_match = max(all_rows, key=lambda row: similarity(row['title'], input_title))
                await pool.wait_closed()
                return {
                    "matched_title": best_match['title'],
                    "description": best_match['description']
                }

            best = results[0]
            await pool.wait_closed()
            return {
                "matched_title": best["title"],
                "description": best["description"]
            }


async def main():
    await update_db()

if __name__ == "__main__":
    asyncio.run(main())
