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
    "Normal Vision": px.colors.qualitative.Set1,
    "Deuteranopia (Red-Green)": px.colors.sequential.Viridis,
    "Protanopia (Red-Green)": px.colors.sequential.Plasma,
    "Tritanopia (Blue-Yellow)": px.colors.sequential.Magma,
    "Color Universal Design (CUD)": ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
    "HCL-based Safe Palette": ["#E64B35", "#4DBBD5", "#00A087", "#F39B7F", "#8491B4", "#91D1C2", "#DC0000", "#7E6148"],
    "Tol Vibrant": ["#EE7733", "#0077BB", "#33BBEE", "#009988", "#EE3377", "#CC3311", "#BBBBBB"],
    "Tol Muted": ["#332288", "#88CCEE", "#44AA99", "#117733", "#999933", "#DDCC77", "#CC6677", "#882255", "#AA4499"],
}


# ----------------- Streamlit UI -----------------
st.title("Population by Provinces")
st.sidebar.header("Settings")

# Select visualization type
vis_type = st.sidebar.selectbox("Choose a visualization type:", ["Map", "Bar Chart", "Table"])

# Select colorblind-friendly palette
palette_choice = st.sidebar.selectbox("Choose a colorblind-friendly palette:", list(colorblind_palettes.keys()))
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
    fig = px.bar(df, x="Province", y="Population", color="Province", 
                 color_discrete_sequence=palette, title="Population by Province")
    st.plotly_chart(fig)

elif vis_type == "Map":
    # Create a Folium map with layer control
    m = folium.Map(location=[56.1304, -106.3468], zoom_start=4, tiles=None)

    # Add different base layers
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("CartoDB positron", name="Light Mode").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark Mode").add_to(m)
    folium.TileLayer("Stamen Terrain", name="Terrain").add_to(m)

    # Enable layer control toggle
    folium.LayerControl().add_to(m)

    # Merge data for coloring the provinces
    canada_map = canada_map.rename(columns={"name": "Province"}).merge(df, on="Province", how="left")

    # Apply logarithmic scaling to prevent extreme brightness differences
    min_pop, max_pop = df["Population"].min(), df["Population"].max()
    colormap = folium.LinearColormap(
        colors=palette_hex,
        vmin=np.log1p(min_pop),  # Log scale to smooth differences
        vmax=np.log1p(max_pop)
    )

    # Function to style each province
    def style_function(feature):
        province_name = feature["properties"]["name"]
        pop = df[df["Province"] == province_name]["Population"].values[0] if province_name in df["Province"].values else None
        return {
            "fillColor": colormap(np.log1p(pop)) if pop else "gray",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7
        }

    # Add GeoJson for provinces with interactivity
    for _, row in canada_map.iterrows():
        pop = row["Population"] if pd.notna(row["Population"]) else None
        folium.GeoJson(
            row.geometry,
            name=row["Province"],
            style_function=style_function,
            highlight_function=lambda x: {"weight": 3, "fillOpacity": 1},  # Hover effect
            tooltip=f"{row['Province']}: {row['Population']:,}" if pop else "No Data",
            popup=folium.Popup(f"<b>{row['Province']}</b><br>Population: {row['Population']:,}", max_width=200)
        ).add_to(m)

    # Add legend with the selected colorblind palette
    colormap.caption = f"Population Density ({palette_choice})"
    m.add_child(colormap)

    # Render the map in Streamlit
    folium_static(m)

elif vis_type == "Table":
    # Hide index and unnecessary columns
    table_df = df.drop(columns=["Latitude", "Longitude"])
    st.write(table_df.set_index("Province"))

