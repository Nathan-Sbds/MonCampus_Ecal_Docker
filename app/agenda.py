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

# Get config file path from command line argument or use default
config_file = sys.argv[1] if len(sys.argv) > 1 else "/app/config.yml"

if not os.path.exists(config_file):
    print(f"Config file {config_file} not found!")
    sys.exit(1)

with open(config_file, "r") as file:
    config = yaml.safe_load(file)

print(f"Using config: {config_file} - Instance: {config.get('instance_name', 'default')}")

async def remove_duplicates_from_api(event_api):
    """
    Removes duplicate events from the API.

    This function retrieves all events from the API, identifies duplicates based on event details,
    and deletes the duplicate events.

    Args:
        event_api: Instance of the Event API.
    """
    try:
        events_data = []
        page_index = 1

        # Retrieve all events from the API, page by page
        while True:
            events = ecal_api.EventAPI.get_events(event_api, params={"showPastEvents": True, "page": page_index})
            if "data" in events:
                # Add events to the list if they are not already present
                events_data.extend([{
                    "name": e['name'],
                    "location": e["location"],
                    "startDate": e["startDate"],
                    "startTime": e["startTime"],
                    "endDate": e["endDate"],
                    "endTime": e["endTime"],
                    "id": e["id"]
                } for e in events["data"] if {
                    "name": e['name'],
                    "location": e["location"],
                    "startDate": e["startDate"],
                    "startTime": e["startTime"],
                    "endDate": e["endDate"],
                    "endTime": e["endTime"],
                    "id": e["id"]
                } not in events_data])

                page_index += 1
            else:
                break

        seen = set()
        duplicates = []

        # Identify duplicate events
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

        # Delete duplicate events
        for duplicate in duplicates:
            ecal_api.EventAPI.delete_event(event_api, duplicate["id"])

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
        return response.json()["Data"] if response.status_code == 200 else None
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))

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

        return {
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

        events_data_ecal = []
        page_index = 1

        # Retrieve all events from the API, page by page
        while True:
            events = ecal_api.EventAPI.get_events(event_api, params={"showPastEvents": True, "page": page_index, "limit": 100})
            if "data" in events:
                # Add events to the list if they are not already present
                events_data_ecal.extend([{
                    "name": e['name'],
                    "location": e["location"],
                    "calendarId": e["calendarId"],
                    "startDate": e["startDate"],
                    "startTime": e["startTime"],
                    "endDate": e["endDate"],
                    "endTime": e["endTime"],
                    "alert": e["alert"],
                    "details": e["details"],
                    "draft": e["draft"]
                } for e in events["data"] if {
                    "name": e['name'],
                    "location": e["location"],
                    "calendarId": e["calendarId"],
                    "startDate": e["startDate"],
                    "startTime": e["startTime"],
                    "endDate": e["endDate"],
                    "endTime": e["endTime"],
                    "alert": e["alert"],
                    "details": e["details"],
                    "draft": e["draft"]
                } not in events_data_ecal])

                page_index += 1
            else:
                break

        # Compare the number of events between Wigor and the API
        if len(wigor_data) != len(events_data_ecal):
            await main()
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))

async def main():
    """
    Main function to synchronize events between Wigor and the API.

    This function retrieves event data from Wigor and the API, formats the data, creates new events
    in the API if they are not present, deletes events from the API if they are not present in Wigor,
    removes duplicate events, and checks if the number of events is the same between Wigor and the API.
    """
    try:
        
        event_api = ecal_api.EventAPI(config['ecal_api_key'], config['ecal_api_secret'])

        cookies = await get_cookies()

        wigor_data = await fetch_wigor_data(cookies)

        with open(config['error_file_path'], 'w') as f:
            f.write(f"{wigor_data}")
        if wigor_data is None:
            return

        events_data_ecal = []
        page_index = 1

        # Retrieve all events from the API, page by page
        while True:
            events = ecal_api.EventAPI.get_events(event_api, params={"showPastEvents": True, "page": page_index, "limit": 100})
            if "result" in events and events["status"] != "No content":
                with open(config['error_file_path'], 'w') as f:
                    f.write("Error: " + str(events))
                return await main()

            with open(config['error_file_path'], 'w') as f:
                f.write("No error: " + str(events))

            if "data" in events:
                # Add events to the list if they are not already present
                events_data_ecal.extend([{
                    "name": e['name'],
                    "location": e["location"],
                    "calendarId": e["calendarId"],
                    "startDate": e["startDate"],
                    "startTime": e["startTime"],
                    "endDate": e["endDate"],
                    "endTime": e["endTime"],
                    "alert": e["alert"],
                    "details": e["details"],
                    "draft": e["draft"]
                } for e in events["data"] if {
                    "name": e['name'],
                    "location": e["location"],
                    "calendarId": e["calendarId"],
                    "startDate": e["startDate"],
                    "startTime": e["startTime"],
                    "endDate": e["endDate"],
                    "endTime": e["endTime"],
                    "alert": e["alert"],
                    "details": e["details"],
                    "draft": e["draft"]
                } not in events_data_ecal])

                page_index += 1

            else:
                break

        if len(events_data_ecal) == 0:
            return await main()

        # Format Wigor event data
        events_data_moncampus = [format_event_data(item) for item in wigor_data]

        # Create events that are not present in the API
        for event in events_data_moncampus:
            if event not in events_data_ecal:
                event['reference'] = str(randint(0, 10000000))
                ecal_api.EventAPI.create_event(event_api, event)

        # Delete events from the API that are not present in Wigor
        for event_ecal in events_data_ecal:
            if event_ecal not in events_data_moncampus:
                similar_events = ecal_api.EventAPI.get_events(event_api, params={"startDate": event_ecal["startDate"], "showPastEvents": True})
                if "data" in similar_events:
                    for event in similar_events["data"]:
                        if all([
                            event["name"] == event_ecal["name"],
                            event["startDate"] == event_ecal["startDate"],
                            event["startTime"] == event_ecal["startTime"],
                            event["endDate"] == event_ecal["endDate"],
                            event["endTime"] == event_ecal["endTime"],
                            event["location"] == event_ecal["location"],
                            event["calendarId"] == event_ecal["calendarId"]
                        ]):
                            ecal_api.EventAPI.delete_event(event_api, event_id=event["id"])
                            break

        # Remove duplicate events from the API
        await remove_duplicates_from_api(event_api)
        # Check if the number of events is the same between Wigor and the API
        await check_same_number_of_events(event_api)
    except Exception as e:
        with open(config['error_file_path'], 'w') as f:
            f.write(str(e))

# Execute the main function
asyncio.get_event_loop().run_until_complete(main())
