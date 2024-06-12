import streamlit as st
from yelp_fusion import client

# User interface
st.title("Local Business Finder")

# Sidebar for API key input
st.sidebar.title("Settings")
yelp_api_key = st.sidebar.text_input("Enter your Yelp API key:", type="password")

if yelp_api_key:
    yelp_client = client.YelpFusionClient(yelp_api_key)

    location = st.text_input("Enter a location (city, zip code, or address):")
    category = st.text_input("Enter a business category (e.g., restaurants, bars, etc.):")
    search_button = st.button("Search")

    # Function to fetch business data from Yelp API
    def fetch_businesses(location, category):
        try:
            params = {
                "term": category,
                "location": location,
                "sort_by": "best_match",
                "limit": 50,
            }
            response = yelp_client.search_query(**params)
            businesses = response.businesses
            return businesses
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return []

    # Display search results
    if search_button:
        businesses = fetch_businesses(location, category)
        if businesses:
            for business in businesses:
                st.write(f"**{business.name}**")
                st.write(f"Rating: {business.rating} ({business.review_count} reviews)")
                st.write(f"Address: {business.location.display_address}")
                st.write(f"Phone: {business.display_phone}")
                st.write("---")
else:
    st.warning("Please enter your Yelp API key in the sidebar settings.")
