import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import folium
from streamlit_folium import folium_static
from matplotlib.colors import to_hex


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
    "Tritanopia (Blue-Yellow)": px.colors.sequential.Magma
}

# ----------------- Streamlit UI -----------------
st.title("Canadian Provinces Data Visualization")
st.sidebar.header("Settings")

# Select visualization type
vis_type = st.sidebar.selectbox("Choose a visualization type:", ["Bar Chart", "Map", "Table"])

# Select colorblind-friendly palette
palette_choice = st.sidebar.selectbox("Choose a colorblind-friendly palette:", list(colorblind_palettes.keys()))
palette = colorblind_palettes[palette_choice]

# Convert Plotly colors to HEX (Fix for Folium)

# Function to ensure colors are properly converted to hex
def convert_to_hex(color_list):
    hex_colors = []
    for c in color_list:
        if isinstance(c, tuple):  # If RGB tuple, convert to hex
            hex_colors.append(to_hex([v / 255 for v in c]))
        else:  # If already a hex string, use directly
            hex_colors.append(c)
    return hex_colors

# Convert selected palette to hex codes
palette_hex = convert_to_hex(palette)

# ----------------- Visualization Logic -----------------
if vis_type == "Bar Chart":
    fig = px.bar(df, x="Province", y="Population", color="Province", 
                 color_discrete_sequence=palette, title="Population by Province")
    st.plotly_chart(fig)

elif vis_type == "Map":
    # Create a Folium map
    m = folium.Map(location=[56.1304, -106.3468], zoom_start=4)

    # Merge data for coloring the provinces
    canada_map = canada_map.rename(columns={"name": "Province"}).merge(df, on="Province", how="left")

    # Sort data to ensure color mapping is ordered correctly
    sorted_df = df.sort_values(by="Population")
    sorted_population = sorted_df["Population"].tolist()

    # Ensure color scale aligns with sorted population
    from matplotlib.colors import to_hex
    palette_hex = [to_hex([v / 255 for v in px.colors.hex_to_rgb(c)]) for c in palette]
    
    # Make sure the number of colors matches the number of unique population values
    num_colors = min(len(palette_hex), len(sorted_population))
    colormap = folium.LinearColormap(
        colors=palette_hex[:num_colors], 
        vmin=min(sorted_population), 
        vmax=max(sorted_population)
    )

    for _, row in canada_map.iterrows():
        pop = row["Population"] if pd.notna(row["Population"]) else None
        folium.GeoJson(
            row.geometry,
            style_function=lambda feature, pop=pop: {
                "fillColor": colormap(pop) if pop else "gray",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.7
            },
            tooltip=f"{row['Province']}: {row['Population']:,}" if pop else "No Data",
        ).add_to(m)

    colormap.caption = "Population Density"
    m.add_child(colormap)

    folium_static(m)


elif vis_type == "Table":
    # Hide index and unnecessary columns
    table_df = df.drop(columns=["Latitude", "Longitude"])
    st.write(table_df.set_index("Province"))
