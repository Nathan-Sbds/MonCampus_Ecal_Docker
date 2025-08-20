import sys
import os
import yaml
import asyncio
import requests
import ecal_api
from random import randint
from datetime import timedelta, datetime
from dateutil import parser
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
import sqlite3


# Get config file path from command line argument or use default
config_file = sys.argv[1] if len(sys.argv) > 1 else "/app/config.yml"

if not os.path.exists(config_file):
    print(f"Config file {config_file} not found!")
    sys.exit(1)

with open(config_file, "r") as file:
    config = yaml.safe_load(file)

print(f"Using config: {config_file} - Instance: {config.get('instance_name', 'default')}")

# --- SQLITE DB SETUP ---
DB_PATH = config.get('sqlite_db_path', '/app/events.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        name TEXT,
        location TEXT,
        calendarId TEXT,
        startDate TEXT,
        startTime TEXT,
        endDate TEXT,
        endTime TEXT,
        alert TEXT,
        details TEXT,
        draft INTEGER,
        reference TEXT
    )''')
    conn.commit()
    conn.close()

def get_all_events_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, location, calendarId, startDate, startTime, endDate, endTime, alert, details, draft, reference, id FROM events')
    rows = c.fetchall()
    conn.close()
    events = []
    for row in rows:
        events.append({
            "name": row[0],
            "location": row[1],
            "calendarId": row[2],
            "startDate": row[3],
            "startTime": row[4],
            "endDate": row[5],
            "endTime": row[6],
            "alert": row[7],
            "details": row[8],
            "draft": row[9],
            "reference": row[10],
            "id": row[11]
        })
    return events

def insert_event_to_db(event, event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO events (id, name, location, calendarId, startDate, startTime, endDate, endTime, alert, details, draft, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (event_id, event["name"], event["location"], event["calendarId"], event["startDate"], event["startTime"], event["endDate"], event["endTime"], event["alert"], event["details"], event["draft"], event.get("reference", None)))
    conn.commit()
    conn.close()

def delete_event_from_db(event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM events')
    conn.commit()
    conn.close()

init_db()

def find_similar_event_in_db(event):
    """Return (id, reference) for a DB event matching key fields, or None."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, reference FROM events WHERE name = ? AND startDate = ? AND startTime = ? AND endDate = ? AND endTime = ? AND location = ? LIMIT 1''',
              (event.get('name'), event.get('startDate'), event.get('startTime'), event.get('endDate'), event.get('endTime'), event.get('location')))
    row = c.fetchone()
    conn.close()
    return row

def remove_duplicates_from_db_and_api(event_api):
    """
    Supprime les doublons d'événements dans la base locale et l'API ecal.
    """
    try:
        events_data = get_all_events_from_db()
        seen = set()
        duplicates = []
        for event in events_data:
            event_key = (
                event["name"],
                event["startDate"],
                event["startTime"],
                event["endDate"],
                event["endTime"],
                event["location"]
            )
            if event_key in seen:
                duplicates.append(event)
            else:
                seen.add(event_key)
        for duplicate in duplicates:
            if duplicate.get("id"):
                ecal_api.EventAPI.delete_event(event_api, duplicate["id"])
                delete_event_from_db(duplicate["id"])
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))

async def get_cookies():
    """
    Récupère les cookies de session après connexion.
    """
    username = config['moncampus_username']
    password = config['moncampus_password']
    url = "https://ws-edt-igs.wigorservices.net"

    options = FirefoxOptions()

    driver = None
    cookies = None
    
    try:
        driver = webdriver.Remote(options=options, command_executor="http://selenium:4444")

        # Open the login page
        driver.get(url)
        
        # Fill in the login form
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.CLASS_NAME, 'mdc-button--raised.btn.btn-primary.btn-primary').click()
                
        # Wait for redirection and retrieve cookies
        driver.implicitly_wait(5)  # Adjust if needed

        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))
    finally:
        if driver is not None:
            driver.quit()

    return cookies

async def fetch_wigor_data(cookies):
    """
    Retrieves data from Wigor.

    This function sends a GET request to the Wigor API using the provided cookies and retrieves
    the event data.

    Args:
        cookies (dict): Dictionary of cookies.

    Returns:
        list: List of retrieved data.
    """
    try:
        start_date = config['moncampus_start_date']
        end_date = config['moncampus_end_date']
        url = f"https://ws-edt-igs.wigorservices.net/Home/Get?sort=&group=&filter=&dateDebut={start_date}T00:00:00.000Z&dateFin={end_date}T23:59:59.000Z"
        response = requests.get(url, cookies=cookies)
        data = response.json().get("Data") if response.status_code == 200 else None
        return data
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))
        return None

def format_event_data(item):
    """
    Formats event data.

    This function converts the start and end dates and times to ISO format, retrieves the Teams URL
    if present, and formats the event data into a dictionary.

    Args:
        item (dict): Dictionary containing event data.

    Returns:
        dict: Dictionary of formatted event data.
    """
    try:
        # Convert start and end dates and times to ISO format
        start = parser.isoparse(item['Start']) - timedelta(hours=datetime.fromisoformat(str(parser.isoparse(item['Start']))).utcoffset().seconds // 3600)
        end = parser.isoparse(item['End']) - timedelta(hours=datetime.fromisoformat(str(parser.isoparse(item['End']))).utcoffset().seconds // 3600)

        # Retrieve Teams URL if present
        teams_url = item['TeamsUrl'].split('"')[1] if item['TeamsUrl'] is not None else None

        result = {
            "name": item['Commentaire'],
            "location": item['Salles'],
            "calendarId": config['ecal_calendar_id'],
            "startDate": start.isoformat()[:10],
            "startTime": start.isoformat()[11:16],
            "endDate": end.isoformat()[:10],
            "endTime": end.isoformat()[11:16],
            "alert": "15M",
            "details": f"Intervenant : {item.get('NomProf', 'Aucun Intervenant')}\nNom complet du cours : {item['LibelleGroupe']}\n{'' if teams_url is None else 'Lien Teams : '+teams_url}",
            "draft": 0
        }
        return result
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))

async def check_same_number_of_events(event_api):
    """
    Checks if the number of events is the same between Wigor and the API.

    This function retrieves all events from the API and compares the number of events with the data
    retrieved from Wigor. If the numbers do not match, it calls the main function to resynchronize.

    Args:
        event_api: Instance of the Event API.
    """
    try:
        cookies = await get_cookies()

        wigor_data = await fetch_wigor_data(cookies)
        if wigor_data is None:
            return

        # Compare number using local DB to avoid heavy API calls
        events_data_db = get_all_events_from_db()
        if len(wigor_data) != len(events_data_db):
            await main()
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))


async def main():
    """
    Main function to synchronize events between Wigor, the API, and the local SQLite DB.
    """
    try:
        event_api = ecal_api.EventAPI(config['ecal_api_key'], config['ecal_api_secret'])
        # --- Synchronisation initiale DB <-> API ecal ---
        # Do NOT clear DB to avoid removing local records unexpectedly.
        clear_db()
        page_index = 1
        total_loaded = 0
        while True:
            events = ecal_api.EventAPI.get_events(event_api, params={"showPastEvents": True, "page": page_index, "limit": 100, "calendarIds": config['ecal_calendar_id']})
            if "data" in events:
                for e in events["data"]:
                    event = {
                        "name": e['name'],
                        "location": e["location"],
                        "calendarId": e["calendarId"],
                        "startDate": e["startDate"],
                        "startTime": e["startTime"],
                        "endDate": e["endDate"],
                        "endTime": e["endTime"],
                        "alert": e["alert"],
                        "details": e["details"],
                        "draft": e["draft"],
                        "reference": e.get("reference", None)
                    }
                    insert_event_to_db(event, e["id"])
                    total_loaded += 1
                page_index += 1
            else:
                break

        # --- Nettoyage des doublons via la DB locale ---
        remove_duplicates_from_db_and_api(event_api)

        # --- Synchronisation Wigor <-> DB <-> API ---
        cookies = await get_cookies()
        wigor_data = await fetch_wigor_data(cookies)
        if wigor_data is None:
            return
        events_data_moncampus = [format_event_data(item) for item in wigor_data]
        events_data_db = get_all_events_from_db()

        # Ajout des nouveaux événements
        added = 0
        for event in events_data_moncampus:
            # check DB first for an equivalent event (even with different id/reference)
            similar = find_similar_event_in_db(event)
            if similar:
                # similar is (id, reference) - ensure DB has the latest reference
                existing_id, existing_ref = similar
                if existing_ref is None and event.get('reference'):
                    insert_event_to_db(event, existing_id)
                continue

            if event not in events_data_db:
                event['reference'] = str(randint(0, 10000000))
                api_event = ecal_api.EventAPI.create_event(event_api, event)
                event_id = api_event.get("id") if api_event and "id" in api_event else str(randint(0, 10000000))
                insert_event_to_db(event, event_id)
                added += 1

        # Vérification du nombre d'événements
        await check_same_number_of_events(event_api)
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))

# Execute the main function
asyncio.get_event_loop().run_until_complete(main())
