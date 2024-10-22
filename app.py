import streamlit as st
import pydeck as pdk
import pandas as pd
import geopandas as gpd
import fused
import numpy as np

def convert_gdf_to_geojson(gdf):
    """Convert GeoDataFrame to GeoJSON format suitable for PyDeck"""
    features = []
    for idx, row in gdf.iterrows():
        # Convert hex color to RGB
        color_hex = row['color'].lstrip('#')
        color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        
        feature = {
            'type': 'Feature',
            'geometry': row.geometry.__geo_interface__,
            'properties': {
                'name': row['ADMIN'],
                'metric': float(row['metric']),
                'color': list(color_rgb) + [200]  # RGB + Alpha
            }
        }
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

def create_pydeck_layer(geojson_data):
    """Create a PyDeck GeoJsonLayer"""
    return pdk.Layer(
        'GeoJsonLayer',
        data=geojson_data,
        opacity=0.8,
        stroked=True,
        filled=True,
        extruded=True,
        wireframe=True,
        get_fill_color='properties.color',
        get_line_color=[255, 255, 255],
        get_line_width=2,
        get_elevation='properties.metric',
        elevation_scale=100,
        pickable=True,
        auto_highlight=True
    )

def main():
    st.title("FlashMaps")
   
    st.write("""
    Enter a prompt to visualize country-based metrics on the map.
    Example prompts:
    - "What are the top 10 countries by GDP per capita?"
    - "List the 5 most populous countries in the world"
    - "Which countries have the highest life expectancy?"
    """)
    

    prompt = st.text_input("Enter your prompt:", "What are the top 5 countries by population?")
    
    if st.button("Generate Map"):
        with st.spinner("Processing data..."):
            try:
                # Call the Fused function with the prompt
                result = fused.run(
                    "fsh_BQfWBx5y0OdBA2AMFOWOi",
                    input_text=prompt
                )
                
                # Ensure metric values are numeric
                result['metric'] = pd.to_numeric(result['metric'], errors='coerce')
                
                # Normalize metrics for elevation
                min_metric = result['metric'].min()
                max_metric = result['metric'].max()
                result['metric'] = (result['metric'] - min_metric) / (max_metric - min_metric) * 1000
                
                # Convert the result to GeoJSON
                geojson_data = convert_gdf_to_geojson(result)
                
                # Create PyDeck layer
                layer = create_pydeck_layer(geojson_data)
                
                # Set up the PyDeck view
                view_state = pdk.ViewState(
                    latitude=20,
                    longitude=0,
                    zoom=1,
                    pitch=45
                )
                
                # Create the deck
                deck = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    map_style='light',
                    tooltip={
                        'html': '<b>Country:</b> {name}<br/>'
                               '<b>Metric:</b> {metric}',
                        'style': {
                            'backgroundColor': 'steelblue',
                            'color': 'white'
                        }
                    }
                )
                
                # Display the map
                st.pydeck_chart(deck)
                
                # Display data table
                st.subheader("Data Table")
                display_df = pd.DataFrame({
                    'Country': [f['properties']['name'] for f in geojson_data['features']],
                    'Metric': [f['properties']['metric'] for f in geojson_data['features']]
                }).sort_values('Metric', ascending=False)
                st.dataframe(display_df)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Please try a different prompt or check the input format.")

if __name__ == "__main__":
    main()
