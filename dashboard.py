import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from matplotlib.colors import is_color_like, to_hex, to_rgba
import re
import numpy as np


# ----------------- Load Canada Provinces Data -----------------
# Sample Data: Population and Coordinates for Canadian Provinces
data = {
    "Province": ["Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", 
                 "Saskatchewan", "Nova Scotia", "New Brunswick", "Newfoundland and Labrador", 
                 "Prince Edward Island"],
    "Population": [14734014, 8574571, 5241058, 4666101, 1386335, 
                   1178681, 969383, 794300, 510550, 167680],
    "Latitude": [50.0, 52.0, 53.7267, 53.9333, 49.8951, 
                 52.9399, 44.6819, 46.5653, 53.1355, 46.5107],
    "Longitude": [-85.0, -71.0, -127.6476, -116.5765, -97.1384, 
                  -106.4509, -63.7443, -66.4619, -57.6604, -63.4168]
}

df = pd.DataFrame(data)

# ----------------- Load Canada Map Shape (GeoJSON) -----------------
@st.cache_data
def load_canada_map():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/canada.geojson"
    return gpd.read_file(url)

canada_map = load_canada_map()

# ----------------- Define Colorblind-Friendly Palettes -----------------
colorblind_palettes = {
    "Normal Vision (Categorical)": px.colors.sequential.Turbo,  # Bright distinct colors for normal vision users
    "Color Universal Design (CUD): For General Colorblindness": px.colors.sequential.Inferno,  # High contrast, good for general colorblind accessibility
    "Deuteranopia & Protanopia: For Red-Green Colorblindness": px.colors.sequential.Cividis,  # Blue → Green → Yellow (Best for red-green blindness)
    "Tritanopia: For Blue-Yellow Colorblindness": px.colors.sequential.Magma,  # Black → Dark Red → Yellow (Good for tritanopia)
    "Soft Contrast: For Accessibility": px.colors.sequential.Plasma,  # Purple → Orange → Yellow (High contrast, readable for all)
}



# ----------------- Streamlit UI -----------------
st.title("Population by Provinces")
st.sidebar.header("Settings")

# Select visualization type
vis_type = st.sidebar.selectbox("Choose a visualization type:", ["Map", "Bar Chart", "Table"])

# Select colorblind-friendly palette
palette_choice = st.sidebar.selectbox("Choose a colorblind-friendly palette for the map:", list(colorblind_palettes.keys()))
palette = colorblind_palettes[palette_choice]

# Function to ensure colors are properly converted to hex
def convert_to_hex(color_list):
    hex_colors = []
    rgb_pattern = re.compile(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)")

    for c in color_list:
        if isinstance(c, tuple):  # RGB tuple (255, 0, 0)
            hex_colors.append(to_hex([v / 255 for v in c]))
        elif isinstance(c, str):
            if c.startswith("#"):  # Already a hex string
                hex_colors.append(c)
            elif rgb_pattern.match(c):  # CSS "rgb(255, 0, 0)" format
                r, g, b = map(int, rgb_pattern.match(c).groups())
                hex_colors.append(to_hex([r / 255, g / 255, b / 255]))
            elif is_color_like(c):  # Convert named colors (e.g., "red", "blue")
                hex_colors.append(to_hex(to_rgba(c)))
            else:
                raise ValueError(f"Unexpected color format: {c}")
        else:
            raise ValueError(f"Unexpected color format: {c}")

    return hex_colors

# Convert the selected color palette to hex
palette_hex = convert_to_hex(palette)

# ----------------- Visualization Logic -----------------
if vis_type == "Bar Chart":
    fig = px.bar(df, x="Province", y="Population", 
             title="Population by Province", 
             color_discrete_sequence=["#4c72b0"])  # blue shade
    st.plotly_chart(fig)



elif vis_type == "Map":
    # Create a Folium map
    m = folium.Map(location=[56.1304, -106.3468], zoom_start=4)

    # Merge data for coloring the provinces
    canada_map = canada_map.rename(columns={"name": "Province"}).merge(df, on="Province", how="left")

    # Create a color mapping based on population
    min_pop, max_pop = df["Population"].min(), df["Population"].max()
    colormap = folium.LinearColormap(colors=palette_hex, vmin=min_pop, vmax=max_pop)

    for _, row in canada_map.iterrows():
        pop = row["Population"] if pd.notna(row["Population"]) else None
        folium.GeoJson(
            row.geometry,
            style_function=lambda feature, pop=pop: {
                "fillColor": colormap(pop) if pop else "gray",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.9
            },
            tooltip=f"{row['Province']}: {row['Population']:,}" if pop else "No Data",
        ).add_to(m)

    # Add legend with colorblind-friendly palette label
    colormap.caption = f"Population Density ({palette_choice})"
    m.add_child(colormap)

    # Display the map
    folium_static(m)


elif vis_type == "Table":
    # Hide index and unnecessary columns
    table_df = df.drop(columns=["Latitude", "Longitude"])
    st.write(table_df.set_index("Province"))

