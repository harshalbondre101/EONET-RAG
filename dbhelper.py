import requests
import mysql.connector
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'asssignment1'
}

def update_db():
    # Get latest 50 events from EONET
    url = "https://eonet.gsfc.nasa.gov/api/v3/events?limit=50"
    response = requests.get(url)
    data = response.json().get("events", [])

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

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

        # Get first category, source, and geometry (you can extend to multiple if needed)
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

        cursor.execute(insert_query, values)

    conn.commit()
    cursor.close()
    conn.close()

def get_description_by_title(input_title):
    print(f"Searching for title: {input_title}")
    from difflib import SequenceMatcher

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Try full-text search first
    query = """
        SELECT title, description 
        FROM eonet_events 
        WHERE MATCH(title) AGAINST(%s IN NATURAL LANGUAGE MODE)
        LIMIT 5
    """
    cursor.execute(query, (input_title,))
    results = cursor.fetchall()

    # Fallback: do fuzzy matching on titles if no strong matches
    if not results:
        cursor.execute("SELECT title, description FROM eonet_events")
        all_rows = cursor.fetchall()

        def similarity(a, b):
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        best_match = max(all_rows, key=lambda row: similarity(row['title'], input_title))
        conn.close()
        return str({
            "matched_title": best_match['title'],
            "description": best_match['description']
        })

    # Otherwise return the best match from full-text
    best = results[0]
    conn.close()
    return str({
        "matched_title": best["title"],
        "description": best["description"]
    })

update_db()