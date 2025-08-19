
import streamlit as st
import requests
import pandas as pd
import io
import json
import numpy as np
import plotly.express as px

# --- Load your data ---

# The `st.cache_data` decorator is recommended for data loading
@st.cache_data

def load_country_centroids():
    """
    Loads the GeoJSON file, calculates the centroid for each country,
    and returns a DataFrame with country codes and their lat/lon coordinates.
    """
    centroids = []
    try:
        with open('data/raw/countries.geojson', 'r') as f:
            geojson_data = json.load(f)
    except FileNotFoundError:
        st.error("The 'countries.geojson' file was not found in the 'data/raw' directory. Please make sure it's there.")
        return pd.DataFrame(columns=['Code', 'lat', 'lon'])

    for feature in geojson_data['features']:
        code = feature['properties'].get('ISO_A3')
        if not code:
            continue

        geom = feature['geometry']
        coords = geom['coordinates']
        
        # Handle MultiPolygon and Polygon geometries to find the main polygon
        if geom['type'] == 'MultiPolygon':
            # Find the largest polygon by number of points
            main_polygon = max(coords, key=lambda p: len(p[0]))
        elif geom['type'] == 'Polygon':
            main_polygon = coords
        else:
            continue

        # Calculate centroid by averaging the coordinates of the main polygon's exterior ring
        # This is a simplification but works well for centering maps.
        points = np.array(main_polygon[0])
        lon, lat = np.mean(points, axis=0)
        
        centroids.append({'Code': code, 'lat': lat, 'lon': lon})

    return pd.DataFrame(centroids)

def load_data():
    """
    Loads and preprocesses the internet usage data.
    """
    # Make sure this CSV file is in the same directory as your app.py
    df = pd.read_csv("data/raw/share-of-individuals-using-the-internet.csv", sep=",")
    
    # Rename the column for easier plotting
    df = df.rename({'Individuals using the Internet (% of population)': 'Usage'}, axis=1)
    
    # Convert 'Year' to datetime if needed, though px.choropleth can handle it as a string/int
    df['Date'] = pd.to_datetime(df['Year'], format='%Y')
    
    return df


# Load the main and geographical data
inet_df = load_data()
centroids_df = load_country_centroids()

# Merge the two dataframes to add lat/lon to the main data
if not centroids_df.empty:
    inet_df = pd.merge(inet_df, centroids_df, on='Code', how='left')

# --- Page Configuration ---
st.set_page_config(
    page_title="Internet Usage Dashboard",
    layout="wide",
)

# --- Sidebar for filters ---
st.sidebar.header("Filter Options")

# Create a list of entities for the dropdown, starting with "All"
entity_list = ["All"] + sorted(inet_df['Entity'].unique().tolist())

# Create the dropdown in the sidebar
selected_entity = st.sidebar.selectbox("Select an Entity", entity_list)

# Filter the dataframe based on the selection
if selected_entity == "All":
    filtered_df = inet_df
else:
    filtered_df = inet_df[inet_df['Entity'] == selected_entity]

if st.checkbox("Show dataframe", key="show_data"):
    # If the checkbox is checked, display a subheader and the dataframe.
    st.subheader("Underlying Data")
    st.dataframe(filtered_df)

# The figure is created only if the checkbox is ticked.
if st.checkbox("Show Map", value=True, key="show_map"): 
        
    # Use the filtered_df for plotting
    
    # Define a dynamic title
    if selected_entity == "All":
        title_text = 'Internet Usage (% of population) by Country Over Time'
    else:
        title_text = f'Internet Usage in {selected_entity} (% of population) Over Time'

    # Define a fixed color range for consistency
    color_range = [inet_df['Usage'].min(), inet_df['Usage'].max()]
    
    # Create the Choropleth Map
    fig = px.choropleth(
        inet_df,
        locations="Code",
        color="Usage",
        hover_name="Entity",
        animation_frame="Year",
        color_continuous_scale=px.colors.sequential.Plasma,
        title=title_text,
        labels={'Usage': 'Internet Usage (%)'},
        projection="natural earth",
        width=1000,
        height=700
    )

    # If a single country is selected, update the map's view to zoom in on it.
    if selected_entity != "All" and not filtered_df.empty:
        # Check if lat/lon data is available after the merge
        if 'lat' in filtered_df.columns and 'lon' in filtered_df.columns:
            # Create a new dataframe that only contains rows with valid lat/lon data
            valid_geo_data = filtered_df.dropna(subset=['lat', 'lon'])
            
            # Only attempt to zoom if we have valid geo data for the selection.
            # This prevents the IndexError for regions.
            if not valid_geo_data.empty:
                entity_data = valid_geo_data.iloc[0]
                
                # Update the geo projection to focus on the selected country
                fig.update_geos(
                    center={"lon": entity_data['lon'], "lat": entity_data['lat']},
                    projection_scale=4 # Adjust this value for more or less zoom
                )


    # --- Display the figure in Streamlit ---
    # filter changes, ensuring a clean re-render
    st.plotly_chart(fig, use_container_width=True, key=f"map_{selected_entity}")
