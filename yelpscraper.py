import streamlit as st
from yelpapi import YelpAPI

def main():
    # Get the Yelp API key from the user input
    api_key = st.sidebar.text_input("Enter your Yelp API key", type="password")

    if api_key:
        # Initialize the YelpAPI object
        with YelpAPI(api_key) as yelp_api:
            # Create a search form
            st.title("Yelp Business Search")
            term = st.text_input("Search term (e.g., restaurants, bars)")
            location = st.text_input("Location (e.g., New York City, NY)")
            radius = st.number_input("Search radius (in meters)", min_value=0, value=5000, step=500)
            limit = st.number_input("Number of results", min_value=1, max_value=50, value=10, step=1)

            # Perform the search when the user clicks the button
            if st.button("Search"):
                search_args = {
                    'term': term,
                    'location': location,
                    'radius': radius,
                    'limit': limit
                }

                search_results = yelp_api.search_query(**search_args)

                # Display the search results
                if search_results['total'] > 0:
                    st.write(f"Found {search_results['total']} businesses:")
                    for business in search_results['businesses']:
                        st.write(f"**Name:** {business['name']}")
                        st.write(f"**Rating:** {business['rating']} ({business['review_count']} reviews)")
                        st.write(f"**Address:** {' '.join(business['location']['display_address'])}")
                        if 'url' in business:
                            st.write(f"**Website:** {business['url']}")
                        st.write("---")
                else:
                    st.write("No businesses found.")
    else:
        st.warning("Please enter your Yelp API key to proceed.")

if __name__ == "__main__":
    st.set_page_config(page_title="Yelp Business Search", page_icon=":mag:")
    main()
