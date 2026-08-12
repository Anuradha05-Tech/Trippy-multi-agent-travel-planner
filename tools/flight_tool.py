from dotenv import load_dotenv
import os
import requests

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

def search_flights(query):
    """Search for flights using AviationStack API. 
    Accepts query parameters or filters if applicable.
    """
    url = "http://api.aviationstack.com/v1/flights"

    params = {
        "access_key": API_KEY,
        "limit": 5
    }

    # If query is provided, we can attempt to filter by departure or arrival airport codes (IATA)
    # as a simple heuristic for user queries containing airport codes.
    if query:
        words = [w.strip().upper() for w in query.replace(",", " ").split() if len(w.strip()) == 3]
        if len(words) >= 1:
            params["dep_iata"] = words[0]
        if len(words) >= 2:
            params["arr_iata"] = words[1]

    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        return f"Error querying flight API: {str(e)}"

    flights = []

    if "data" in data and isinstance(data["data"], list):
        for flight in data["data"][:5]:
            airline = flight.get("airline", {}).get("name", "Unknown airline")
            departure = flight.get("departure", {}).get("airport", "unknown")
            arrival = flight.get("arrival", {}).get("airport", "unknown")
            status = flight.get("flight_status", "unknown")

            flights.append(f"""
            Airline : {airline},
            Departure: {departure},
            Arrival: {arrival},
            Status: {status}
            """)
    else:
        # If API returned an error message
        if "error" in data:
            error_info = data["error"].get("message", "Unknown API error")
            return f"API Error: {error_info}"
        return "No flight data found or invalid API response."

    return "\n".join(flights) if flights else "No flights found matching the criteria."
