import ee
import os
import json
import pandas as pd
from google.oauth2 import service_account

KEY_PATH = 'nifa-webgis-4e708187c46c.json'
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
class FeatureExtractor:
    def __init__(self, geojson_path):
        self.initialize_gee()
        logger.info("Initialized GEE")
        
        self.doy_list = [f"{x:03d}" for x in range(58, 299, 16)]
        logger.info(f"DOY list created: {self.doy_list}")
        
        # Load geometry
        with open(geojson_path) as f:
            self.geojson = json.load(f)
        self.area_of_interest = ee.FeatureCollection(self.geojson)
        logger.info(f"Loaded geometry from {geojson_path}")

    def initialize_gee(self):
        """Initialize Earth Engine"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(script_dir, KEY_PATH)
        
        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=['https://www.googleapis.com/auth/earthengine'])
        ee.Initialize(credentials)

    def get_soil_properties(self):
        """Get static soil properties"""
        soil_data = {}
        soil_properties = {
            'awc': ee.Image("projects/nifa-webgis/assets/awc").select('b1'),  # Add .select('b1')
            'cec': ee.Image("projects/nifa-webgis/assets/cec").select('b1'),
            'som': ee.Image("projects/nifa-webgis/assets/som").select('b1')
        }
        
        logger.info("Starting soil property extraction")
        for soil_type, image in soil_properties.items():
            try:
                logger.info(f"Processing {soil_type}")
                reduced = image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.area_of_interest.geometry(),
                    scale=250,
                    maxPixels=1e9
                ).get('b1')  # Get 'b1' band value
                
                value = reduced.getInfo()
                logger.info(f"Extracted {soil_type}: {value}")
                soil_data[soil_type] = value
                
            except Exception as e:
                logger.error(f"Error extracting {soil_type}: {str(e)}")
                raise Exception(f"Failed to extract {soil_type}: {str(e)}")
            
        return soil_data

    def get_modis_vis(self, year):
        """Get vegetation indices for specific dates"""
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        
        vi_data = {doy: {} for doy in self.doy_list}
        
        logger.info(f"Starting MODIS VI extraction for year {year}")
        
        try:
            collection = ee.ImageCollection('MODIS/061/MOD09A1') \
                .filterDate(start_date, end_date) \
                .filterBounds(self.area_of_interest)
            
            logger.info(f"Initial collection size: {collection.size().getInfo()}")
                
            def calculate_indices(image):
                # Get date info
                date = ee.Date(image.get('system:time_start'))
                doy = date.getRelative('day', 'year')
                
                evi = image.expression(
                    '2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 1)',
                    {
                        'nir': image.select('sur_refl_b02'),
                        'red': image.select('sur_refl_b01'),
                        'blue': image.select('sur_refl_b03')
                    }).rename('EVI')
                
                ndvi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b01']).rename('NDVI')
                
                gci = image.expression(
                    '(nir / green) - 1',
                    {
                        'nir': image.select('sur_refl_b02'),
                        'green': image.select('sur_refl_b04')
                    }).rename('GCI')
                
                ndwi = image.normalizedDifference(['sur_refl_b02', 'sur_refl_b06']).rename('NDWI')
                
                return ee.Image.cat([evi, ndvi, gci, ndwi]).set('doy', doy)
            
            indices = collection.map(calculate_indices)
            
            for doy in self.doy_list:
                doy_number = int(doy)
                # Find closest date within ±8 days
                filtered = indices.filterMetadata('doy', 'greater_than', doy_number - 8) \
                                .filterMetadata('doy', 'less_than', doy_number + 8)
                
                count = filtered.size().getInfo()
                logger.info(f"Found {count} images for DOY {doy}")
                
                if count > 0:
                    reduced = filtered.mean().reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=self.area_of_interest.geometry(),
                        scale=250,
                        maxPixels=1e9
                    )
                    values = reduced.getInfo()
                    logger.info(f"DOY {doy} values: {values}")
                    
                    vi_data[doy] = {
                        'EVI': values['EVI'],
                        'NDVI': values['NDVI'],
                        'GCI': values['GCI'],
                        'NDWI': values['NDWI']
                    }
                else:
                    logger.warning(f"No data found for DOY {doy}, using nearest available date")
                    # Get nearest available date
                    nearest = indices.sort('doy').first()
                    reduced = nearest.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=self.area_of_interest.geometry(),
                        scale=250,
                        maxPixels=1e9
                    )
                    values = reduced.getInfo()
                    vi_data[doy] = {
                        'EVI': values['EVI'],
                        'NDVI': values['NDVI'],
                        'GCI': values['GCI'],
                        'NDWI': values['NDWI']
                    }
                    
        except Exception as e:
            logger.error(f"Error in MODIS VI extraction: {str(e)}")
            raise
            
        return vi_data

    def get_lst_data(self, year):
        """Get LST data for specific dates"""
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        
        lst_data = {doy: {} for doy in self.doy_list}
        
        collection = ee.ImageCollection('MODIS/061/MOD11A1') \
            .filterDate(start_date, end_date) \
            .filterBounds(self.area_of_interest)
        
        for doy in self.doy_list:
            doy_number = int(doy)
            filtered = collection.filter(ee.Filter.calendarRange(doy_number, doy_number, 'day_of_year'))
            
            if filtered.size().getInfo() > 0:
                day_lst = filtered.select('LST_Day_1km').mean() \
                    .multiply(0.02).subtract(273.15)
                night_lst = filtered.select('LST_Night_1km').mean() \
                    .multiply(0.02).subtract(273.15)
                
                reduced_day = day_lst.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.area_of_interest.geometry(),
                    scale=1000,
                    maxPixels=1e9
                )
                reduced_night = night_lst.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.area_of_interest.geometry(),
                    scale=1000,
                    maxPixels=1e9
                )
                
                lst_data[doy] = {
                    'LSTday': reduced_day.getInfo()['LST_Day_1km'],
                    'LSTnight': reduced_night.getInfo()['LST_Night_1km']
                }
                
        return lst_data

    def get_weather_data(self, year):
        """Get PRISM weather data for specific dates"""
        try:
            start_date = f'{year}-01-01'
            end_date = f'{year}-12-31'
            
            weather_data = {doy: {} for doy in self.doy_list}
            
            logger.info(f"Starting PRISM weather data extraction for year {year}")
            
            collection = ee.ImageCollection('OREGONSTATE/PRISM/AN81d') \
                .filterDate(start_date, end_date) \
                .filterBounds(self.area_of_interest)
                
            # Check collection size
            size = collection.size().getInfo()
            logger.info(f"PRISM collection size: {size}")
            
            # All required variables
            variables = ['ppt', 'tmax', 'tmean', 'tmin', 'tdmean', 'vpdmax', 'vpdmean', 'vpdmin']
            
            for doy in self.doy_list:
                logger.info(f"Processing DOY {doy}")
                doy_number = int(doy)
                
                # Get date for this DOY
                date = ee.Date.fromYMD(year, 1, 1).advance(doy_number-1, 'day')
                date_range = ee.DateRange(date.advance(-3, 'day'), date.advance(3, 'day'))
                
                # Filter collection by date range
                filtered = collection.filterDate(date_range)
                filtered_size = filtered.size().getInfo()
                logger.info(f"Found {filtered_size} images for DOY {doy}")
                
                if filtered_size > 0:
                    try:
                        mean_image = filtered.mean()
                        reduced = mean_image.reduceRegion(
                            reducer=ee.Reducer.mean(),
                            geometry=self.area_of_interest.geometry(),
                            scale=4000,
                            maxPixels=1e9
                        )
                        values = reduced.getInfo()
                        logger.info(f"Reduced values for DOY {doy}: {values}")
                        
                        # Store each variable
                        for var in variables:
                            weather_data[doy][var] = values.get(var, 0)  # Default to 0 if missing
                    except Exception as e:
                        logger.error(f"Error reducing data for DOY {doy}: {str(e)}")
                        # Fill with zeros if reduction fails
                        for var in variables:
                            weather_data[doy][var] = 0
                else:
                    logger.warning(f"No data found for DOY {doy}, filling with zeros")
                    for var in variables:
                        weather_data[doy][var] = 0
                        
            logger.info(f"Weather data extraction complete. First DOY data: {weather_data[self.doy_list[0]]}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error in weather data extraction: {str(e)}")
            raise

    def get_gldas_data(self, year):
        """Get GLDAS data for specific dates"""
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        
        gldas_data = {doy: {} for doy in self.doy_list}
        
        collection = ee.ImageCollection('NASA/GLDAS/V021/NOAH/G025/T3H') \
            .filterDate(start_date, end_date) \
            .filterBounds(self.area_of_interest)
        
        variables = {
            'Evap': 'Evap_tavg',
            'PotEvap': 'PotEvap_tavg',
            'RootMoist': 'RootMoist_inst'
        }
        
        for doy in self.doy_list:
            doy_number = int(doy)
            filtered = collection.filter(ee.Filter.calendarRange(doy_number, doy_number, 'day_of_year'))
            
            if filtered.size().getInfo() > 0:
                reduced = filtered.mean().reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=self.area_of_interest.geometry(),
                    scale=25000,
                    maxPixels=1e9
                )
                values = reduced.getInfo()
                
                gldas_data[doy] = {
                    'Evap': values['Evap_tavg'],
                    'PotEvap': values['PotEvap_tavg'],
                    'RootMoist': values['RootMoist_inst']
                }
                # Calculate GLDASws
                if values['PotEvap_tavg'] != 0:
                    gldas_data[doy]['GLDASws'] = values['Evap_tavg'] / (values['PotEvap_tavg'] * 0.408 * 1e-6)
                else:
                    gldas_data[doy]['GLDASws'] = 0
                
        return gldas_data

    def create_feature_vector(self, year=2023):
        """Create complete feature vector"""
        try:
            # Get all data
            logger.info("Getting soil properties...")
            soil_data = self.get_soil_properties()
            logger.info("Soil properties obtained")

            logger.info("Getting vegetation indices...")
            vi_data = self.get_modis_vis(year)
            logger.info("Vegetation indices obtained")

            logger.info("Getting LST data...")
            lst_data = self.get_lst_data(year)
            logger.info("LST data obtained")

            logger.info("Getting weather data...")
            weather_data = self.get_weather_data(year)
            logger.info("Weather data obtained")

            logger.info("Getting GLDAS data...")
            gldas_data = self.get_gldas_data(year)
            logger.info("GLDAS data obtained")
            
            # Create feature dictionary
            features = {}
            
            # Add soil properties
            features.update(soil_data)
            
            # Add time series features
            for doy in self.doy_list:
                # Log progress for each DOY
                logger.info(f"Processing DOY {doy}")
                
                try:
                    # Add vegetation indices
                    for vi in ['EVI', 'NDVI', 'GCI', 'NDWI']:
                        features[f'{vi}_{doy}'] = vi_data[doy].get(vi, 0)
                    
                    # Add LST
                    for lst in ['LSTday', 'LSTnight']:
                        features[f'{lst}_{doy}'] = lst_data[doy].get(lst, 0)
                    
                    # Add weather variables
                    for var in ['ppt', 'tmax', 'tmean', 'tmin', 'tdmean', 'vpdmax', 'vpdmean', 'vpdmin']:
                        features[f'{var}_{doy}'] = weather_data[doy].get(var, 0)
                    
                    # Add GLDAS variables
                    for var in ['Evap', 'PotEvap', 'RootMoist', 'GLDASws']:
                        features[f'{var}_{doy}'] = gldas_data[doy].get(var, 0)
                
                except Exception as e:
                    logger.error(f"Error processing DOY {doy}: {str(e)}")
                    # Fill missing values with zeros
                    logger.warning(f"Filling missing values with zeros for DOY {doy}")
                    for feature_type in ['EVI', 'NDVI', 'GCI', 'NDWI', 'LSTday', 'LSTnight',
                                    'ppt', 'tmax', 'tmean', 'tmin', 'tdmean', 'vpdmax', 'vpdmean', 'vpdmin',
                                    'Evap', 'PotEvap', 'RootMoist', 'GLDASws']:
                        features[f'{feature_type}_{doy}'] = 0
            
            # Convert to DataFrame
            df = pd.DataFrame([features])
            
            # Log feature names and counts
            logger.info(f"Total features created: {df.shape[1]}")
            logger.info(f"Feature names: {list(df.columns)}")
            
            # Verify feature count
            assert df.shape[1] == 291, f"Wrong number of features: {df.shape[1]}"
            
            return df
            
        except Exception as e:
            logger.error(f"Error in create_feature_vector: {str(e)}")
            raise

def get_features(geojson_path):
    """Main function to get feature vector"""
    try:
        extractor = FeatureExtractor(geojson_path)
        return extractor.create_feature_vector()
    except Exception as e:
        print(f"Error extracting features: {str(e)}")
        return None

if __name__ == "__main__":
    geojson_path = "request_id1.json"
    features = get_features(geojson_path)
    if features is not None:
        print(f"Successfully extracted features: {features}")