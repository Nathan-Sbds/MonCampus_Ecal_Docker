import ecal_api, requests,pyppeteer, pyppeteer.launcher, asyncio, json, os
from random import randint
from datetime import timedelta, datetime
from dateutil import parser


with open('/app/config.json') as f:
    data = json.load(f)

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
        with open(data["ERROR_FILE_PATH"], 'w') as f:
            f.write(str(e))

async def get_cookies():
    """
    Retrieves login cookies.

    This function launches a headless browser, navigates to the login page, fills in the login form,
    and retrieves the cookies after a successful login.

    Returns:
        dict: Dictionary of cookies.
    """
    try:
        username = data["MONCAMPUS_USERNAME"]
        password = data["MONCAMPUS_PASSWORD"]
        url = "https://ws-edt-igs.wigorservices.net"

        # Launch the browser and open a new page
        browser = await pyppeteer.launch(
            executablePath=data["CHROMIUM_EXECUTABLE_PATH"],
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', "--disable-gpu"]
        )
        page = await browser.newPage()
        await page.goto(url)

        # Fill in the login form
        await page.waitForSelector("#username")
        await page.type("#username", username)
        await page.type("#password", password)

        await page.click('button[type="submit"]')
        await page.waitForSelector("body")

        # Retrieve cookies after login
        cookies = {cookie['name']: cookie['value'] for cookie in await page.cookies()}
        await browser.close()

        return cookies
    except Exception as e:
        with open(data["ERROR_FILE_PATH"], 'w') as f:
            f.write(str(e))

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
        start_date = data["MONCAMPUS_START_DATE"]
        end_date = data["MONCAMPUS_END_DATE"]
        url = f"https://ws-edt-igs.wigorservices.net/Home/Get?sort=&group=&filter=&dateDebut={start_date}T00:00:00.000Z&dateFin={end_date}T23:59:59.000Z"
        response = requests.get(url, cookies=cookies)
        return response.json()["Data"] if response.status_code == 200 else None
    except Exception as e:
        with open(data["ERROR_FILE_PATH"], 'w') as f:
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
            "calendarId": data["ECAL_CALENDAR_ID"],
            "startDate": start.isoformat()[:10],
            "startTime": start.isoformat()[11:16],
            "endDate": end.isoformat()[:10],
            "endTime": end.isoformat()[11:16],
            "alert": "15M",
            "details": f"Intervenant : {item.get('NomProf', 'Aucun Intervenant')}\nNom complet du cours : {item['LibelleGroupe']}\n{'' if teams_url is None else 'Lien Teams : '+teams_url}",
            "draft": 0
        }
    except Exception as e:
        with open(data["ERROR_FILE_PATH"], 'w') as f:
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
        with open(data["ERROR_FILE_PATH"], 'w') as f:
            f.write(str(e))

async def main():
    """
    Main function to synchronize events between Wigor and the API.

    This function retrieves event data from Wigor and the API, formats the data, creates new events
    in the API if they are not present, deletes events from the API if they are not present in Wigor,
    removes duplicate events, and checks if the number of events is the same between Wigor and the API.
    """
    try:
        event_api = ecal_api.EventAPI(data["ECAL_API_KEY"], data["ECAL_API_SECRET"])

        cookies = await get_cookies()

        wigor_data = await fetch_wigor_data(cookies)

        if wigor_data is None:
            return

        events_data_ecal = []
        page_index = 1

        # Retrieve all events from the API, page by page
        while True:
            events = ecal_api.EventAPI.get_events(event_api, params={"showPastEvents": True, "page": page_index, "limit": 100})
            if "result" in events and events["status"] != "No content":
                return await main()

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
        with open(data["ERROR_FILE_PATH"], 'w') as f:
            f.write(str(e))

# Execute the main function
asyncio.get_event_loop().run_until_complete(main())