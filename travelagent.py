import streamlit as st
import json
import os
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from datetime import datetime
from agno.exceptions import ModelProviderError

# Set up Streamlit UI with a travel-friendly theme
st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #ff5733;
        }
        .subtitle {
            text-align: center;
            font-size: 20px;
            color: #555;
        }
        .stSlider > div {
            background-color: #f9f9f9;
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and subtitle
st.markdown('<h1 class="title">✈️ AI-Powered Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Plan your dream trip with AI! Get personalized recommendations for flights, hotels, and activities.</p>', unsafe_allow_html=True)

# User Inputs Section
st.markdown("### 🌍 Where are you headed?")
source = st.text_input("🛫 Departure City (IATA Code):", "BOM")  # Example: BOM for Mumbai
destination = st.text_input("🛬 Destination (IATA Code):", "DEL")  # Example: DEL for Delhi

st.markdown("### 📅 Plan Your Adventure")
num_days = st.slider("🕒 Trip Duration (days):", 1, 14, 5)
travel_theme = st.selectbox(
    "🎭 Select Your Travel Theme:",
    ["💑 Couple Getaway", "👨‍👩‍👧‍👦 Family Vacation", "🏔️ Adventure Trip", "🧳 Solo Exploration"]
)

# Divider for aesthetics
st.markdown("---")

st.markdown(
    f"""
    <div style="
        text-align: center; 
        padding: 15px; 
        background-color: #6a5acd; 
        border-radius: 10px; 
        margin-top: 20px;
    ">
        <h3>🌟 Your {travel_theme} to {destination} is about to begin! 🌟</h3>
        <p>Let's find the best flights, stays, and experiences for your unforgettable journey.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")  # Example: Mar-06, 2025 | 6:20 PM
    except ValueError as e:
        # Log the error or handle specific parsing errors
        return "N/A"

activity_preferences = st.text_area(
    "🌍 What activities do you enjoy? (e.g., relaxing on the beach, exploring historical sites, nightlife, adventure)",
    "Relaxing on the beach, exploring historical sites"
)

# Date inputs with defaults and validation
from datetime import date, timedelta
default_departure = date.today() + timedelta(days=30)  # Default to 30 days from today
default_return = default_departure + timedelta(days=7)  # Default to 7 days after departure

departure_date = st.date_input("Departure Date", value=default_departure)
return_date = st.date_input("Return Date", value=default_return)

# Validate that return date is after departure date
if return_date < departure_date:
    st.error("Return date must be after departure date!")

# Sidebar Setup
st.sidebar.title("🌎 Travel Assistant")
st.sidebar.subheader("Personalize Your Trip")

# Travel Preferences
budget = st.sidebar.radio("💰 Budget Preference:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["Economy", "Business", "First Class"])
hotel_rating = st.sidebar.selectbox("🏨 Preferred Hotel Rating:", ["Any", "3⭐", "4⭐", "5⭐"])

# Packing Checklist
st.sidebar.subheader("🎒 Packing Checklist")
packing_list = {
    "👕 Clothes": True,
    "🩴 Comfortable Footwear": True,
    "🕶️ Sunglasses & Sunscreen": False,
    "📖 Travel Guidebook": False,
    "💊 Medications & First-Aid": True
}
for item, checked in packing_list.items():
    st.sidebar.checkbox(item, value=checked)

# Travel Essentials
st.sidebar.subheader("🛂 Travel Essentials")
visa_required = st.sidebar.checkbox("🛃 Check Visa Requirements")
travel_insurance = st.sidebar.checkbox("🛡️ Get Travel Insurance")
currency_converter = st.sidebar.checkbox("💱 Currency Exchange Rates")

# Replace with your actual API keys
SERPAPI_KEY = ""  # SerpAPI key
GOOGLE_API_KEY = ""  # Google API key
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Function to fetch flight data
def fetch_flights(source, destination, departure_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": source,
        "arrival_id": destination,
        "outbound_date": str(departure_date),
        "return_date": str(return_date),
        "currency": "INR",
        "hl": "en",
        "api_key": SERPAPI_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results, params  # Return params for reuse in booking links

# Function to extract top 3 cheapest flights
def extract_cheapest_flights(flight_data):
    best_flights = flight_data.get("best_flights", [])
    sorted_flights = sorted(best_flights, key=lambda x: x.get("price", float("inf")))[:3]  # Get top 3 cheapest
    return sorted_flights

# AI Agents
researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify the travel destination specified by the user.",
        "Gather detailed information on the destination, including climate, culture, and safety tips.",
        "Find popular attractions, landmarks, and must-visit places.",
        "Search for activities that match the user’s interests and travel style.",
        "Prioritize information from reliable sources and official travel guides.",
        "Provide well-structured summaries with key insights and recommendations."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
    add_datetime_to_instructions=True,
)

planner = Agent(
    name="Planner",
    instructions=[
        "Gather details about the user's travel preferences and budget.",
        "Create a detailed itinerary with scheduled activities and estimated costs.",
        "Ensure the itinerary includes transportation options and travel time estimates.",
        "Optimize the schedule for convenience and enjoyment.",
        "Present the itinerary in a structured format."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        "Identify key locations in the user's travel itinerary.",
        "Search for highly rated hotels near those locations.",
        "Search for top-rated restaurants based on cuisine preferences and proximity.",
        "Prioritize results based on user preferences, ratings, and availability.",
        "Provide direct booking links or reservation options where possible."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[SerpApiTools(api_key=SERPAPI_KEY)],
    add_datetime_to_instructions=True,
)

# Generate Travel Plan
if st.button("🚀 Generate Travel Plan"):
    try:
        with st.spinner("✈️ Fetching best flight options..."):
            flight_data, params = fetch_flights(source, destination, departure_date, return_date)
            cheapest_flights = extract_cheapest_flights(flight_data)

        # AI Processing
        research_results_content = ""
        hotel_restaurant_results_content = ""
        itinerary_content = ""
        
        with st.spinner("🔍 Researching best attractions & activities..."):
            research_prompt = (
                f"Research the best attractions and activities in {destination} for a {num_days}-day {travel_theme.lower()} trip. "
                f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. "
                f"Hotel Rating: {hotel_rating}. Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}."
            )
            try:
                research_results = researcher.run(research_prompt, stream=False)
                research_results_content = research_results.content
            except ModelProviderError as e:
                st.warning("⚠️ Google AI service is currently unavailable. Using fallback information...")
                research_results_content = f"Popular attractions in {destination} for {travel_theme.lower()} trips include various cultural and historical sites. Based on your preferences for {activity_preferences}, we recommend exploring local attractions and dining options."

        with st.spinner("🏨 Searching for hotels & restaurants..."):
            hotel_restaurant_prompt = (
                f"Find the best hotels and restaurants near popular attractions in {destination} for a {travel_theme.lower()} trip. "
                f"Budget: {budget}. Hotel Rating: {hotel_rating}. Preferred activities: {activity_preferences}."
            )
            try:
                hotel_restaurant_results = hotel_restaurant_finder.run(hotel_restaurant_prompt, stream=False)
                hotel_restaurant_results_content = hotel_restaurant_results.content
            except ModelProviderError as e:
                st.warning("⚠️ Google AI service is currently unavailable. Using fallback information...")
                hotel_restaurant_results_content = f"For {budget} budget and {hotel_rating} hotels in {destination}, we recommend checking popular booking sites like Booking.com, Hotels.com, or Airbnb. For restaurants, apps like TripAdvisor, Zomato, or Yelp can help you find dining options that match your preferences."

        with st.spinner("🗺️ Creating your personalized itinerary..."):
            planning_prompt = (
                f"Based on the following data, create a {num_days}-day itinerary for a {travel_theme.lower()} trip to {destination}. "
                f"The traveler enjoys: {activity_preferences}. Budget: {budget}. Flight Class: {flight_class}. Hotel Rating: {hotel_rating}. "
                f"Visa Requirement: {visa_required}. Travel Insurance: {travel_insurance}. Research: {research_results_content}. "
                f"Flights: {json.dumps(cheapest_flights)}. Hotels & Restaurants: {hotel_restaurant_results_content}."
            )
            try:
                itinerary = planner.run(planning_prompt, stream=False)
                itinerary_content = itinerary.content
            except ModelProviderError as e:
                st.warning("⚠️ Google AI service is currently unavailable. Using fallback information...")
                itinerary_content = f"""
                # {num_days}-Day {travel_theme} Trip to {destination}
                
                ## Day 1
                - Morning: Arrive at {destination} and check into your hotel
                - Afternoon: Explore the area around your accommodation
                - Evening: Dinner at a local restaurant
                
                ## Day 2-{num_days-1}
                - Morning: Visit popular attractions
                - Afternoon: Engage in {activity_preferences}
                - Evening: Try local cuisine
                
                ## Day {num_days}
                - Morning: Last-minute shopping for souvenirs
                - Afternoon: Prepare for departure
                - Evening: Return flight
                
                Note: This is a simplified itinerary. For a more detailed and personalized plan, please try again when the AI service is available.
                """
        
        # Display Results
        st.subheader("✈️ Cheapest Flight Options")
        if cheapest_flights:
            cols = st.columns(len(cheapest_flights))
            for idx, flight in enumerate(cheapest_flights):
                with cols[idx]:
                    airline_logo = flight.get("airline_logo", "")
                    airline_name = flight.get("airline", "Unknown Airline")
                    price = flight.get("price", "Not Available")
                    total_duration = flight.get("total_duration", "N/A")
                    
                    flights_info = flight.get("flights", [{}])
                    departure = flights_info[0].get("departure_airport", {})
                    arrival = flights_info[-1].get("arrival_airport", {})
                    airline_name = flights_info[0].get("airline", "Unknown Airline") 
                    
                    departure_time = format_datetime(departure.get("time", "N/A"))
                    arrival_time = format_datetime(arrival.get("time", "N/A"))
                    
                    departure_token = flight.get("departure_token", "")
                    booking_options = ""  # Initialize with empty string

                    if departure_token:
                        try:
                            params_with_token = {
                                **params,
                                "departure_token": departure_token  # Add the token here
                            }
                            search_with_token = GoogleSearch(params_with_token)
                            results_with_booking = search_with_token.get_dict()
                            booking_options = results_with_booking.get('best_flights', [])[idx].get('booking_token', '')
                        except Exception as e:
                            st.error(f"Error fetching booking details: {str(e)}")

                    booking_link = f"https://www.google.com/travel/flights?tfs={booking_options}" if booking_options else "#"
                    
                    # Flight card layout
                    st.markdown(
                        f"""
                        <div style="
                            border: 2px solid #ddd; 
                            border-radius: 10px; 
                            padding: 15px; 
                            text-align: center;
                            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                            background-color: #f9f9f9;
                            margin-bottom: 20px;
                        ">
                            <img src="{airline_logo}" width="100" alt="Flight Logo" />
                            <h3 style="margin: 10px 0;">{airline_name}</h3>
                            <p><strong>Departure:</strong> {departure_time}</p>
                            <p><strong>Arrival:</strong> {arrival_time}</p>
                            <p><strong>Duration:</strong> {total_duration} min</p>
                            <h2 style="color: #008000;">💰 {price}</h2>
                            <a href="{booking_link}" target="_blank" style="
                                display: inline-block;
                                padding: 10px 20px;
                                font-size: 16px;
                                font-weight: bold;
                                color: #fff;
                                background-color: #007bff;
                                text-decoration: none;
                                border-radius: 5px;
                                margin-top: 10px;
                            ">🔗 Book Now</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.warning("⚠️ No flight data available.")

        st.subheader("🏨 Hotels & Restaurants")
        st.write(hotel_restaurant_results_content)

        st.subheader("🗺️ Your Personalized Itinerary")
        st.write(itinerary_content)

        st.success("✅ Travel plan generated successfully!")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try again later or check your API keys.")

    # Display Results
    st.subheader("✈️ Cheapest Flight Options")
    if cheapest_flights:
        cols = st.columns(len(cheapest_flights))
        for idx, flight in enumerate(cheapest_flights):
            with cols[idx]:
                airline_logo = flight.get("airline_logo", "")
                airline_name = flight.get("airline", "Unknown Airline")
                price = flight.get("price", "Not Available")
                total_duration = flight.get("total_duration", "N/A")
                
                flights_info = flight.get("flights", [{}])
                departure = flights_info[0].get("departure_airport", {})
                arrival = flights_info[-1].get("arrival_airport", {})
                airline_name = flights_info[0].get("airline", "Unknown Airline") 
                
                departure_time = format_datetime(departure.get("time", "N/A"))
                arrival_time = format_datetime(arrival.get("time", "N/A"))
                
                departure_token = flight.get("departure_token", "")
                booking_options = ""  # Initialize with empty string

                if departure_token:
                    try:
                        params_with_token = {
                            **params,
                            "departure_token": departure_token  # Add the token here
                        }
                        search_with_token = GoogleSearch(params_with_token)
                        results_with_booking = search_with_token.get_dict()
                        booking_options = results_with_booking.get('best_flights', [])[idx].get('booking_token', '')
                    except Exception as e:
                        st.error(f"Error fetching booking details: {str(e)}")

                booking_link = f"https://www.google.com/travel/flights?tfs={booking_options}" if booking_options else "#"
                
                # Flight card layout
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #ddd; 
                        border-radius: 10px; 
                        padding: 15px; 
                        text-align: center;
                        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
                        background-color: #f9f9f9;
                        margin-bottom: 20px;
                    ">
                        <img src="{airline_logo}" width="100" alt="Flight Logo" />
                        <h3 style="margin: 10px 0;">{airline_name}</h3>
                        <p><strong>Departure:</strong> {departure_time}</p>
                        <p><strong>Arrival:</strong> {arrival_time}</p>
                        <p><strong>Duration:</strong> {total_duration} min</p>
                        <h2 style="color: #008000;">💰 {price}</h2>
                        <a href="{booking_link}" target="_blank" style="
                            display: inline-block;
                            padding: 10px 20px;
                            font-size: 16px;
                            font-weight: bold;
                            color: #fff;
                            background-color: #007bff;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 10px;
                        ">🔗 Book Now</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.warning("⚠️ No flight data available.")

    st.subheader("🏨 Hotels & Restaurants")
    st.write(hotel_restaurant_results.content)

    st.subheader("🗺️ Your Personalized Itinerary")
    st.write(itinerary.content)

    st.success("✅ Travel plan generated successfully!")
