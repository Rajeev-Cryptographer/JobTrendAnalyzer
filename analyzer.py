import logging
import json
from flask import jsonify
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from wordcloud import WordCloud
import io
import base64
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from collections import Counter

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# City coordinates in India for heatmap
INDIA_CITY_COORDS = {
    'Mumbai': [19.0760, 72.8777],
    'Delhi': [28.7041, 77.1025],
    'Bangalore': [12.9716, 77.5946],
    'Hyderabad': [17.3850, 78.4867],
    'Chennai': [13.0827, 80.2707],
    'Kolkata': [22.5726, 88.3639],
    'Pune': [18.5204, 73.8567],
    'Ahmedabad': [23.0225, 72.5714],
    'Jaipur': [26.9124, 75.7873],
    'Lucknow': [26.8467, 80.9462],
    'Noida': [28.5355, 77.3910],
    'Gurgaon': [28.4595, 77.0266],
    'Chandigarh': [30.7333, 76.7794],
    'Coimbatore': [11.0168, 76.9558],
    'Indore': [22.7196, 75.8577],
    'Kochi': [9.9312, 76.2673],
    'Nagpur': [21.1458, 79.0882],
    'Bhopal': [23.2599, 77.4126],
    'Visakhapatnam': [17.6868, 83.2185],
    'Bhubaneswar': [20.2961, 85.8245],
    'Guwahati': [26.1445, 91.7362],
    'Patna': [25.5941, 85.1376],
    'Surat': [21.1702, 72.8311],
    'Vadodara': [22.3072, 73.1812],
    'Dehradun': [30.3165, 78.0322],
    'Thiruvananthapuram': [8.5241, 76.9366],
    'Remote': [20.5937, 78.9629],  # Center of India for remote jobs
}

def process_data(internshala_df=None, remotive_df=None):
    """
    Process and merge job data from different sources
    
    Args:
        internshala_df: DataFrame of Internshala jobs
        remotive_df: DataFrame of Remotive jobs
        
    Returns:
        Combined and processed DataFrame
    """
    try:
        dfs = []
        
        if internshala_df is not None and not internshala_df.empty:
            logger.info(f"Processing {len(internshala_df)} Internshala jobs")
            dfs.append(internshala_df)
            
        if remotive_df is not None and not remotive_df.empty:
            logger.info(f"Processing {len(remotive_df)} Remotive jobs")
            dfs.append(remotive_df)
            
        if not dfs:
            logger.warning("No data to process")
            return pd.DataFrame()
            
        # Combine dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Clean the data
        combined_df = combined_df.fillna('')
        
        # Extract numeric salary values where possible
        combined_df['salary_numeric'] = combined_df['salary'].apply(extract_numeric_salary)
        
        logger.info(f"Successfully processed {len(combined_df)} total jobs")
        return combined_df
        
    except Exception as e:
        logger.error(f"Error processing job data: {str(e)}")
        raise

def extract_numeric_salary(salary_str):
    """Extract numeric salary value from string."""
    if not isinstance(salary_str, str) or not salary_str:
        return np.nan
        
    try:
        # Extract numbers from the string
        import re
        numbers = re.findall(r'[\d,]+', salary_str)
        if not numbers:
            return np.nan
            
        # Clean and convert the highest number found
        highest_num = max([int(n.replace(',', '')) for n in numbers])
        
        # Adjust for monthly/yearly if needed
        if 'month' in salary_str.lower() or 'monthly' in salary_str.lower():
            return highest_num
        elif 'year' in salary_str.lower() or 'annually' in salary_str.lower():
            return highest_num / 12
            
        return highest_num
    except:
        return np.nan

# def generate_wordcloud(df):
#     """
#     Generate word cloud of skills from job listings
    
#     Args:
#         df: DataFrame with job data
        
#     Returns:
#         Base64 encoded image data of the word cloud
#     """
#     try:
#         if 'skills' not in df.columns or df.empty:
#             logger.warning("No skills column in data or empty dataframe")
#             return None
            
#         # Collect all skills but filter out 'nan' values and empty strings
#         skills_text = ' '.join([
#             str(skills) for skills in df['skills'] 
#             if skills and str(skills).lower() != 'nan' and pd.notna(skills)
#         ])
        
#         # Further filter out any 'nan' that might be in the combined string
#         skills_text = skills_text.replace('nan', '').replace('NaN', '').replace('Nan', '')
        
#         if not skills_text:
#             logger.warning("No skills data found")
#             return None
            
#         # Generate word cloud
#         wordcloud = WordCloud(
#             width=800, 
#             height=400, 
#             background_color='white',
#             colormap='viridis',
#             max_words=100,
#             contour_width=1,
#             contour_color='steelblue'
#         ).generate(skills_text)
        
#         # Convert to image
#         plt.figure(figsize=(10, 5))
#         plt.imshow(wordcloud, interpolation='bilinear')
#         plt.axis("off")
        
#         # Save to bytes buffer
#         img_buf = io.BytesIO()
#         plt.savefig(img_buf, format='png', bbox_inches='tight')
#         img_buf.seek(0)
        
#         # Convert to base64 for embedding in HTML
#         img_data = base64.b64encode(img_buf.getvalue()).decode('utf-8')
#         plt.close()
        
#         # Create top skills list for extra context
#         skills_list = []
#         for skills in df['skills'].dropna():
#             if isinstance(skills, str) and skills.lower() != 'nan':
#                 # Split by comma and process each skill
#                 for skill in skills.split(','):
#                     skill = skill.strip()
#                     # Only add non-empty, non-nan skills
#                     if skill and skill.lower() != 'nan':
#                         skills_list.append(skill)
        
#         # Filter out any remaining 'nan' values
#         filtered_skills = [skill for skill in skills_list if skill.lower() != 'nan']
        
#         skill_counts = Counter(filtered_skills).most_common(20)
#         # Format top skills as an array of objects with 'skill' and 'count' properties
#         top_skills = [{'skill': skill, 'count': count} for skill, count in skill_counts 
#                      if skill.lower() != 'nan']
        
#         logger.info(f"Processed {len(filtered_skills)} skills, found {len(top_skills)} unique top skills")
        
#         logger.info(f"Generated wordcloud with {len(top_skills)} top skills")
        
#         return jsonify({'image': img_data, 'top_skills': top_skills})
        
#     except Exception as e:
#         logger.error(f"Error generating word cloud: {str(e)}")
#         return None
def generate_india_heatmap(df):
    """
    Generate heatmap of job locations in India
    
    Args:
        df: DataFrame with job data
        
    Returns:
        Folium map as HTML
    """
    try:
        if 'location' not in df.columns or df.empty:
            logger.warning("No location column in data or empty dataframe")
            return None
            
        # Extract India locations
        india_df = df[df['source'] == 'Internshala']
        if india_df.empty:
            logger.warning("No India job data found")
            return None
            
        # Count jobs by location
        location_counts = {}
        for location in india_df['location']:
            if not isinstance(location, str) or not location:
                continue
                
            # Extract city from location
            cities = [city.strip() for city in location.split(',')]
            for city in cities:
                if city in location_counts:
                    location_counts[city] += 1
                else:
                    location_counts[city] = 1
                    
        if not location_counts:
            logger.warning("No valid locations found")
            return None
            
        # Create heatmap data using predefined coordinates
        heatmap_data = []
        mapped_cities = []
        
        for city, count in location_counts.items():
            # Check if we have coordinates for this city
            for known_city, coords in INDIA_CITY_COORDS.items():
                if known_city.lower() in city.lower() or city.lower() in known_city.lower():
                    weight = count  # Job count as weight
                    heatmap_data.append([coords[0], coords[1], weight])
                    mapped_cities.append(city)
                    break
                    
        # Try to geocode unmapped cities
        unmapped_cities = set(location_counts.keys()) - set(mapped_cities)
        if unmapped_cities:
            geolocator = Nominatim(user_agent="job_trends_analyzer")
            for city in unmapped_cities:
                try:
                    # Add India to help with geocoding
                    search_term = f"{city}, India"
                    location = geolocator.geocode(search_term, timeout=10)
                    if location:
                        weight = location_counts[city]
                        heatmap_data.append([location.latitude, location.longitude, weight])
                    time.sleep(1)  # Be nice to the geocoding service
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    logger.warning(f"Geocoding error for {city}: {str(e)}")
                    continue
                    
        if not heatmap_data:
            logger.warning("No locations could be mapped for heatmap")
            return None
            
        # Create the map centered on India
        m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles='CartoDB positron')
        
        # Add the heatmap layer
        HeatMap(heatmap_data).add_to(m)
        
        # Add markers for top cities
        top_cities = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for city, count in top_cities:
            for known_city, coords in INDIA_CITY_COORDS.items():
                if known_city.lower() in city.lower() or city.lower() in known_city.lower():
                    folium.Marker(
                        location=coords,
                        popup=f"{city}: {count} jobs",
                        icon=folium.Icon(color='blue')
                    ).add_to(m)
                    break
                    
        # Save map to HTML
        map_html = m._repr_html_()
        return map_html
        
    except Exception as e:
        logger.error(f"Error generating India heatmap: {str(e)}")
        return None

def generate_world_heatmap(df):
    """
    Generate world heatmap for remote jobs
    
    Args:
        df: DataFrame with job data
        
    Returns:
        Folium map as HTML
    """
    try:
        if 'location' not in df.columns or df.empty:
            logger.warning("No location column in data or empty dataframe")
            return None
            
        # Use Remotive jobs for world map
        remotive_df = df[df['source'] == 'Remotive']
        if remotive_df.empty:
            logger.warning("No Remotive job data found")
            return None
            
        # Count jobs by location
        location_counts = {}
        for location in remotive_df['location']:
            if not isinstance(location, str) or not location:
                continue
                
            # Parse location
            locations = [loc.strip() for loc in location.split(',')]
            for loc in locations:
                # Handle "anywhere", "remote", "worldwide" etc.
                if any(term in loc.lower() for term in ['anywhere', 'remote', 'worldwide', 'global']):
                    loc = 'Worldwide'
                    
                if loc in location_counts:
                    location_counts[loc] += 1
                else:
                    location_counts[loc] = 1
                    
        if not location_counts:
            logger.warning("No valid locations found for world map")
            return None
            
        # World regions for heatmap
        world_regions = {
            'Worldwide': [0, 0],  # Will be distributed
            'USA': [37.0902, -95.7129],
            'US': [37.0902, -95.7129],
            'United States': [37.0902, -95.7129],
            'North America': [37.0902, -95.7129],
            'Europe': [48.8566, 2.3522],
            'EU': [48.8566, 2.3522],
            'UK': [51.5074, -0.1278],
            'United Kingdom': [51.5074, -0.1278],
            'Canada': [56.1304, -106.3468],
            'Australia': [-25.2744, 133.7751],
            'Asia': [34.0479, 100.6197],
            'South America': [-23.5505, -46.6333],
            'Africa': [9.0820, 8.6753],
            'Germany': [51.1657, 10.4515],
            'France': [46.2276, 2.2137],
            'Spain': [40.4168, -3.7038],
            'Italy': [41.8719, 12.5674],
            'Netherlands': [52.1326, 5.2913],
            'Brazil': [-14.2350, -51.9253],
            'Japan': [36.2048, 138.2529],
            'India': [20.5937, 78.9629],
            'Russia': [61.5240, 105.3188],
            'China': [35.8617, 104.1954]
        }
            
        # Create heatmap data
        heatmap_data = []
        
        # Process known regions
        for location, count in location_counts.items():
            found = False
            for region, coords in world_regions.items():
                if region.lower() in location.lower() or location.lower() in region.lower():
                    weight = count
                    heatmap_data.append([coords[0], coords[1], weight])
                    found = True
                    break
                    
            # If location is not in known regions, try geocoding
            if not found and location != 'Worldwide':
                try:
                    geolocator = Nominatim(user_agent="job_trends_analyzer")
                    geocode_result = geolocator.geocode(location, timeout=10)
                    if geocode_result:
                        weight = count
                        heatmap_data.append([geocode_result.latitude, geocode_result.longitude, weight])
                    time.sleep(1)  # Be nice to the geocoding service
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    logger.warning(f"Geocoding error for {location}: {str(e)}")
                    # If geocoding fails, add to worldwide
                    if 'Worldwide' in location_counts:
                        location_counts['Worldwide'] += count
                    else:
                        location_counts['Worldwide'] = count
                        
        # Distribute worldwide jobs across major tech hubs
        if 'Worldwide' in location_counts:
            worldwide_count = location_counts['Worldwide']
            tech_hubs = [
                [37.7749, -122.4194],  # San Francisco
                [40.7128, -74.0060],   # New York
                [51.5074, -0.1278],    # London
                [48.8566, 2.3522],     # Paris
                [52.5200, 13.4050],    # Berlin
                [35.6762, 139.6503],   # Tokyo
                [12.9716, 77.5946],    # Bangalore
                [31.2304, 121.4737],   # Shanghai
                [1.3521, 103.8198],    # Singapore
                [-33.8688, 151.2093],  # Sydney
            ]
            
            # Distribute worldwide jobs among tech hubs
            weight_per_hub = worldwide_count / len(tech_hubs)
            for hub in tech_hubs:
                heatmap_data.append([hub[0], hub[1], weight_per_hub])
                
        if not heatmap_data:
            logger.warning("No locations could be mapped for world heatmap")
            return None
            
        # Create the world map
        m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB positron')
        
        # Add the heatmap layer
        HeatMap(heatmap_data).add_to(m)
        
        # Add markers for top regions
        top_regions = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for region, count in top_regions:
            if region in world_regions:
                folium.Marker(
                    location=world_regions[region],
                    popup=f"{region}: {count} jobs",
                    icon=folium.Icon(color='green')
                ).add_to(m)
                
        # Save map to HTML
        map_html = m._repr_html_()
        return map_html
        
    except Exception as e:
        logger.error(f"Error generating world heatmap: {str(e)}")
        return None
