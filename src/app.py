
# Display the figure

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Load your data ---

# The `st.cache_data` decorator is recommended for data loading
@st.cache_data

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

inet_df = load_data()

# --- Page Configuration ---
st.set_page_config(
    page_title="Internet Usage Dashboard",
    layout="wide",
)
# --- Create the Choropleth Map ---
fig = px.choropleth(
    inet_df,
    locations="Code",
    color="Usage",
    hover_name="Entity",
    animation_frame="Year",
    color_continuous_scale=px.colors.sequential.Plasma,
    title='Internet Usage (% of population) by Country Over Time',
    labels={'Usage': 'Internet Usage (%)'},
    projection="natural earth",
    width=1000,
    height=700
)

# --- Display the figure in Streamlit ---
st.plotly_chart(fig, use_container_width=True)