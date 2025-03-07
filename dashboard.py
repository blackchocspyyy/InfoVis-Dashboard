import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import folium_static

# Sample data: Country, Population, Latitude, Longitude
data = {
    "Country": ["USA", "Canada", "Germany", "France", "Japan"],
    "Population": [331_000_000, 38_000_000, 83_000_000, 67_000_000, 125_000_000],
    "Latitude": [37.0902, 56.1304, 51.1657, 46.6034, 36.2048],
    "Longitude": [-95.7129, -106.3468, 10.4515, 2.2137, 138.2529]
}

df = pd.DataFrame(data)

# Colorblind-friendly palettes
colorblind_palettes = {
    "Normal Vision": px.colors.qualitative.Set1,
    "Deuteranopia (Red-Green)": px.colors.sequential.Viridis,
    "Protanopia (Red-Green)": px.colors.sequential.Plasma,
    "Tritanopia (Blue-Yellow)": px.colors.sequential.Magma
}

# Streamlit UI
st.title("Accessible Data Visualization Dashboard")

# Select visualization type
vis_type = st.selectbox("Choose a visualization type:", ["Bar Chart", "Map", "Table"])

# Select colorblind-friendly palette
palette_choice = st.selectbox("Choose a colorblind-friendly palette:", list(colorblind_palettes.keys()))
palette = colorblind_palettes[palette_choice]

if vis_type == "Bar Chart":
    fig = px.bar(df, x="Country", y="Population", color="Country", color_discrete_sequence=palette,
                 title="Population by Country")
    st.plotly_chart(fig)

elif vis_type == "Map":
    m = folium.Map(location=[20, 0], zoom_start=2)
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row['Country']}: {row['Population']:,}",
        ).add_to(m)
    folium_static(m)

elif vis_type == "Table":
    st.write(df)

