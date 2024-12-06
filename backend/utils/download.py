import ee
import os
import time
import json
from google.oauth2 import service_account
from google.cloud import storage

KEY_PATH = 'nifa-webgis-4e708187c46c.json'


def initialize_gcp_services():
    """Initialize Earth Engine and Google Cloud Storage with service account"""

    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to the key file
    full_key_path = os.path.join(script_dir, KEY_PATH)

    credentials = service_account.Credentials.from_service_account_file(
        full_key_path,
        scopes=[
            'https://www.googleapis.com/auth/earthengine',
            'https://www.googleapis.com/auth/devstorage.read_write'
        ])
    ee.Initialize(credentials)
    storage_client = storage.Client.from_service_account_json(full_key_path)
    
    return storage_client


def download_gee_data(geojson_path, output_path):
    # Initialize Earth Engine
    # ee.Initialize(project='nifa-webgis')

    print('----------FUNCTION ENTRY----------')

    # Load GeoJSON
    with open(geojson_path) as f:
        geojson = json.load(f)

    area_of_interest = ee.FeatureCollection(geojson)

    print('----------GEE ENTRY----------')

    def add_doy(img):
        doy = img.get('DOY')
        names = img.bandNames().map(
            lambda name: ee.String(name).cat('_').cat(doy))
        return img.select(ee.List.sequence(0, None, 1, names.length()), names)

    def daily_func(date):
        return ee.Feature(
            None, {
                'DATE': ee.Date(date).format('YYYY-MM-dd'),
                'DOY': ee.Date(date).getRelative('day', 'year').add(1),
                'system:time_start': ee.Number(date),
                'system:time_end': ee.Number(date).add(24 * 60 * 60 * 1000)
            })

    def set_date_func(obj):
        date = ee.Date(obj.get('system:time_start'))
        return obj.set({
            'DATE': date.format('YYYY-MM-dd'),
            'DOY': date.getRelative('day', 'year').add(1)
        })

    def gldas_daily_func(ft):
        gcoll = ee.ImageCollection.fromImages(ft.get('gldas_images'))
        return gcoll.mean().set({'DATE': ft.get('DATE'), 'DOY': ft.get('DOY')})

    def append_band(current, previous):
        accum = ee.Algorithms.If(
            ee.Algorithms.IsEqual(previous, None), current,
            ee.Image(previous).addBands(ee.Image(current)))
        return accum

    start = '-03-01'
    end = '-12-1'

    tasks = []
    for year in range(2023, 2024):  # Adjusted to match original loop
        year_str = str(year)
        p_year = str(year - 1)

        start_date = ee.Date(year_str + start)
        end_date = ee.Date(year_str + end)

        if year > 2006:
            start_day = f"{year_str}-01-01"
            end_day = f"{year_str}-12-31"

            dataset = ee.ImageCollection('USDA/NASS/CDL') \
                .filter(ee.Filter.date(start_day, end_day)) \
                .first()
            crop_mask = dataset.select('cropland').eq(1)
        else:
            mcd_band = f'MODIS/061/MCD12Q1/{p_year}_01_01'
            crop_mask = ee.Image(mcd_band).select('LC_Type1').clip(
                area_of_interest).eq(12)

        gldas = ee.ImageCollection('NASA/GLDAS/V021/NOAH/G025/T3H') \
            .filterDate(year_str + start, year_str + end) \
            .filterBounds(area_of_interest) \
            .select(['Evap_tavg', 'PotEvap_tavg', 'RootMoist_inst']) \
            .map(set_date_func) \
            .map(add_doy)

        daily_coll = ee.List.sequence(start_date.millis(), end_date.millis(),
                                      24 * 60 * 60 * 1000)
        daily_coll = daily_coll.map(daily_func)

        daily_filter = ee.Filter.equals(leftField="DATE", rightField="DATE")
        gldas_daily = ee.ImageCollection(
            ee.Join.saveAll(matchesKey='gldas_images').apply(
                daily_coll, gldas, daily_filter))

        gldas_daily_mean = gldas_daily.map(gldas_daily_func) \
            .iterate(append_band)

        gldas_table = ee.Image(gldas_daily_mean).reduceRegions(
            collection=area_of_interest,
            reducer=ee.Reducer.mean(),
            scale=1000,
            tileScale=16)

        # Ensure the output directory exists
        os.makedirs(output_path, exist_ok=True)

        # Export the table to Google Cloud Storage
        task = ee.batch.Export.table.toCloudStorage(
            collection=gldas_table,
            description=f'GLDAS_mean_{year_str}',
            bucket='nifa-webgis-bucket',
            fileNamePrefix=f'input2/GLDAS_mean_{year_str}',
            fileFormat='CSV')
        tasks.append(
            submit_and_download_task(task, output_path,
                                     f'GLDAS_mean_{year_str}'))

    wait_for_tasks(tasks)


def download_modis_lst(geojson_path, output_path):
    # Initialize Earth Engine
    # ee.Initialize(project='nifa-webgis')

    print('----------FUNCTION ENTRY----------')

    # Load GeoJSON
    with open(geojson_path) as f:
        geojson = json.load(f)

    area_of_interest = ee.FeatureCollection(geojson)

    print('----------GEE ENTRY----------')

    def add_bandname(img):
        datestring = ee.String(img.get('system:index'))
        format = 'YYYY_MM_dd'
        eedate = ee.Date.parse(format, datestring)
        doy = eedate.getRelative('day', 'year').add(1)
        year = eedate.get('year')
        bandname = ee.String(year).cat('_').cat(doy)
        return img.set('bandname', bandname)

    def stack_collection(collection):
        first = ee.Image(collection.first()).select([])

        def iterate_func(img, previous):
            return ee.Image(previous).addBands(img)

        return ee.Image(collection.iterate(iterate_func, first))

    def stack_lst(start, end, region, mask, mode):
        band = f'LST_{mode}_1km'
        qcband = f'QC_{mode}'
        coll = 'MODIS/061/MOD11A1' if start[:4] in ['2001', '2002'
                                                    ] else 'MODIS/061/MYD11A1'

        lst = ee.ImageCollection(coll) \
            .filterDate(start, end) \
            .filterBounds(region) \
            .map(lambda img: img.updateMask(img.select(qcband).eq(0))) \
            .map(lambda img: img.select(band).float().multiply(0.02).updateMask(mask)) \
            .map(add_bandname) \
            .sort('DOY', True)

        lst_stack = stack_collection(lst)
        return lst_stack

    start = '-03-01'
    end = '-11-30'

    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)

    tasks = []
    for year in range(2023, 2024):  # Adjusted to match original loop
        year_str = str(year)
        p_year = str(year - 1)

        if year > 2006:
            start_day = f"{year_str}-01-01"
            end_day = f"{year_str}-12-31"

            dataset = ee.ImageCollection('USDA/NASS/CDL') \
                .filter(ee.Filter.date(start_day, end_day)) \
                .first()
            crop_mask = dataset.select('cropland').eq(1)
        else:
            mcd_band = f'MODIS/061/MCD12Q1/{p_year}_01_01'
            crop_mask = ee.Image(mcd_band).select('LC_Type1').clip(
                area_of_interest).eq(12)

        # Get LST day stack
        lst_day_stack = stack_lst(year_str + start, year_str + end,
                                  area_of_interest, crop_mask, 'Day')
        mean_lst_day = lst_day_stack.reduceRegions(collection=area_of_interest,
                                                   reducer=ee.Reducer.mean(),
                                                   scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_lst_day.select([".*"], None, False),
                    description=f'LSTday_daily_mean_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/LSTday_daily_mean_{year_str}',
                    fileFormat='CSV'), output_path,
                f'LSTday_daily_mean_{year_str}'))

        # Get LST night stack
        lst_night_stack = stack_lst(year_str + start, year_str + end,
                                    area_of_interest, crop_mask, 'Night')
        mean_lst_night = lst_night_stack.reduceRegions(
            collection=area_of_interest, reducer=ee.Reducer.mean(), scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_lst_night.select([".*"], None, False),
                    description=f'LSTnight_daily_mean_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/LSTnight_daily_mean_{year_str}',
                    fileFormat='CSV'), output_path,
                f'LSTnight_daily_mean_{year_str}'))

    wait_for_tasks(tasks)


def download_prism_data(geojson_path, output_path):
    # Initialize Earth Engine
    # ee.Initialize(project='nifa-webgis')

    print('----------FUNCTION ENTRY----------')

    # Load GeoJSON
    with open(geojson_path) as f:
        geojson = json.load(f)

    area_of_interest = ee.FeatureCollection(geojson)

    print('----------GEE ENTRY----------')

    def add_doy(img):
        datestring = ee.String(img.get('system:index')).slice(0, 8)
        format = 'YYYYMMdd'
        eedate = ee.Date.parse(format, datestring)
        doy = eedate.getRelative('day', 'year').add(1)

        names = img.bandNames().map(
            lambda name: ee.String(name).cat('_').cat(doy))

        return img.select(ee.List.sequence(0, None, 1, names.length()),
                          names).set('DOY', doy)

    def append_band(current, previous):
        accum = ee.Algorithms.If(
            ee.Algorithms.IsEqual(previous, None), current,
            ee.Image(previous).addBands(ee.Image(current)))
        return accum

    def stack_prism(start, end, region, mask, feature_type):
        prism = ee.ImageCollection('OREGONSTATE/PRISM/AN81d') \
            .filterDate(start, end) \
            .filterBounds(region) \
            .select(feature_type) \
            .map(add_doy) \
            .map(lambda img: img.updateMask(mask)) \
            .iterate(append_band)
        return ee.Image(prism)

    start = '-03-01'
    end = '-11-30'

    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)

    tasks = []
    for year in range(2023, 2024):  # Adjusted to match original loop
        year_str = str(year)
        p_year = str(year - 1)

        if year > 2006:
            start_day = f"{year_str}-01-01"
            end_day = f"{year_str}-12-31"

            dataset = ee.ImageCollection('USDA/NASS/CDL') \
                .filter(ee.Filter.date(start_day, end_day)) \
                .first()
            crop_mask = dataset.select('cropland').eq(1)
        elif year != 2001:
            mcd_band = f'MODIS/061/MCD12Q1/{p_year}_01_01'
            crop_mask = ee.Image(mcd_band).select('LC_Type1').clip(
                area_of_interest).eq(12)
        else:
            mcd_band = 'MODIS/061/MCD12Q1/2001_01_01'
            crop_mask = ee.Image(mcd_band).select('LC_Type1').clip(
                area_of_interest).eq(12)
        # Get PRISM precipitation
        ppt = ['ppt']
        prism_ppt = stack_prism(year_str + start, year_str + end,
                                area_of_interest, crop_mask, ppt)
        mean_ppt = prism_ppt.reduceRegions(collection=area_of_interest,
                                           reducer=ee.Reducer.mean(),
                                           scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_ppt.select([".*"], None, False),
                    description=f'PRISM_mean_ppt_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/PRISM_mean_ppt_{year_str}',
                    fileFormat='CSV'), output_path,
                f'PRISM_mean_ppt_{year_str}'))

        # Get PRISM temperature
        temp = ['tmin', 'tmean', 'tmax']
        prism_temp = stack_prism(year_str + start, year_str + end,
                                 area_of_interest, crop_mask, temp)
        mean_temp = prism_temp.reduceRegions(collection=area_of_interest,
                                             reducer=ee.Reducer.mean(),
                                             scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_temp.select([".*"], None, False),
                    description=f'PRISM_mean_temp_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/PRISM_mean_temp_{year_str}',
                    fileFormat='CSV'), output_path,
                f'PRISM_mean_temp_{year_str}'))

        # Get PRISM vapor pressure deficit
        vpd = ['tdmean', 'vpdmin', 'vpdmax', 'tmin', 'tmean', 'tmax', 'ppt']
        prism_vpd = stack_prism(year_str + start, year_str + end,
                                area_of_interest, crop_mask, vpd)
        mean_vpd = prism_vpd.reduceRegions(collection=area_of_interest,
                                           reducer=ee.Reducer.mean(),
                                           scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_vpd.select([".*"], None, False),
                    description=f'PRISM_mean_vpd_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/PRISM_mean_vpd_{year_str}',
                    fileFormat='CSV'), output_path,
                f'PRISM_mean_vpd_{year_str}'))

    wait_for_tasks(tasks)


def download_modis_vi(geojson_path, output_path):
    # Initialize Earth Engine
    # ee.Initialize(project='nifa-webgis')

    print('----------FUNCTION ENTRY----------')

    # Load GeoJSON
    with open(geojson_path) as f:
        geojson = json.load(f)

    area_of_interest = ee.FeatureCollection(geojson)

    print('----------GEE ENTRY----------')

    def get_evi(image):
        evi = image.expression(
            '2.5 * (nir - red) / (nir + 6 * red - 7.5 * blue + 10000)', {
                'red': image.select([0]).float(),
                'nir': image.select([1]).float(),
                'blue': image.select([2]).float()
            })
        return evi.updateMask(evi.gt(0)).updateMask(evi.lt(1))

    def get_gci(image):
        gci = image.expression('nir / green - 1', {
            'nir': image.select([1]).float(),
            'green': image.select([3]).float()
        })
        return gci.updateMask(gci.gt(0))

    def get_ndwi(image):
        ndwi = image.expression('(nir - swir) / (nir + swir)', {
            'nir': image.select([1]).float(),
            'swir': image.select([4]).float()
        })
        return ndwi.updateMask(ndwi.gt(-1)).updateMask(ndwi.lt(1))

    def get_ndvi(image):
        ndvi = image.expression('(nir - red) / (nir + red)', {
            'nir': image.select([1]).float(),
            'red': image.select([0]).float()
        })
        return ndvi.updateMask(ndvi.gt(-1)).updateMask(ndvi.lt(1))

    def add_bandname(img):
        datestring = ee.String(img.get('system:index'))
        format = 'YYYY_MM_dd'
        eedate = ee.Date.parse(format, datestring)
        doy = eedate.getRelative('day', 'year').add(1)
        year = eedate.get('year')
        bandname = ee.String(year).cat('_').cat(doy)
        return img.set('bandname', bandname)

    def stack_collection(collection):
        first = ee.Image(collection.first()).select([])

        def iterate_func(img, previous):
            return ee.Image(previous).addBands(img)

        return ee.Image(collection.iterate(iterate_func, first))

    def stack_vi(start, end, region, mask, func):
        mod_vi = ee.ImageCollection('MODIS/061/MCD43A4') \
            .filterDate(start, end) \
            .filterBounds(region) \
            .map(lambda img: img.updateMask(mask)) \
            .map(func) \
            .map(add_bandname)
        mod_vi_stack = stack_collection(mod_vi)
        return mod_vi_stack

    years = list(range(2023, 2024))
    start = '-03-01'
    end = '-11-30'

    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)

    tasks = []
    for i, year in enumerate(years):
        year_str = str(year)

        if i > 0:
            start_day = f"{year_str}-01-01"
            end_day = f"{year_str}-12-31"

            dataset = ee.ImageCollection('USDA/NASS/CDL') \
                .filter(ee.Filter.date(start_day, end_day)) \
                .first()
            crop_mask = dataset.select('cropland').eq(1)
        else:
            mcd_band = f'MODIS/061/MCD12Q1/{year_str}_01_01'
            crop_mask = ee.Image(mcd_band).select('LC_Type1').clip(
                area_of_interest).eq(12)

        # EVI
        mod_evi_stack = stack_vi(year_str + start, year_str + end,
                                 area_of_interest, crop_mask, get_evi)
        mean_evi = mod_evi_stack.reduceRegions(collection=area_of_interest,
                                               reducer=ee.Reducer.mean(),
                                               scale=500,
                                               tileScale=16)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_evi.select([".*"], None, False),
                    description=f'EVI_mean_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/EVI_mean_{year_str}',
                    fileFormat='CSV'), output_path, f'EVI_mean_{year_str}'))

        # GCI
        mod_gci_stack = stack_vi(year_str + start, year_str + end,
                                 area_of_interest, crop_mask, get_gci)
        mean_gci = mod_gci_stack.reduceRegions(collection=area_of_interest,
                                               reducer=ee.Reducer.mean(),
                                               scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_gci.select([".*"], None, False),
                    description=f'GCI_mean_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/GCI_mean_{year_str}',
                    fileFormat='CSV'), output_path, f'GCI_mean_{year_str}'))

        # NDWI
        mod_ndwi_stack = stack_vi(year_str + start, year_str + end,
                                  area_of_interest, crop_mask, get_ndwi)
        mean_ndwi = mod_ndwi_stack.reduceRegions(collection=area_of_interest,
                                                 reducer=ee.Reducer.mean(),
                                                 scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_ndwi.select([".*"], None, False),
                    description=f'NDWI_mean_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/NDWI_mean_{year_str}',
                    fileFormat='CSV'), output_path, f'NDWI_mean_{year_str}'))

        # NDVI
        mod_ndvi_stack = stack_vi(year_str + start, year_str + end,
                                  area_of_interest, crop_mask, get_ndvi)
        mean_ndvi = mod_ndvi_stack.reduceRegions(collection=area_of_interest,
                                                 reducer=ee.Reducer.mean(),
                                                 scale=500)
        tasks.append(
            submit_and_download_task(
                ee.batch.Export.table.toCloudStorage(
                    collection=mean_ndvi.select([".*"], None, False),
                    description=f'NDVI_mean_{year_str}',
                    bucket='nifa-webgis-bucket',
                    fileNamePrefix=f'input2/NDVI_mean_{year_str}',
                    fileFormat='CSV'), output_path, f'NDVI_mean_{year_str}'))

    wait_for_tasks(tasks)


def process_soil_properties(geojson_path, output_folder, storage_client):
    # Initialize Earth Engine
    # ee.Initialize(project='nifa-webgis')

    # Set up GCS client
    # storage_client = storage.Client()
    bucket = storage_client.bucket(
        'nifa-webgis-bucket')  # Hardcoded bucket name

    # Read the GeoJSON file
    with open(geojson_path) as f:
        geojson = json.load(f)

    # Create an ee.Geometry from the GeoJSON
    aoi = ee.FeatureCollection(geojson)

    # Define soil properties using Earth Engine assets
    soil_properties = {
        'awc': ee.Image("projects/nifa-webgis/assets/awc"),
        'cec': ee.Image("projects/nifa-webgis/assets/cec"),
        'som': ee.Image("projects/nifa-webgis/assets/som")
    }

    def wait_for_task(task):
        while task.status()['state'] in ['READY', 'RUNNING']:
            print(
                f"Task {task.status()['description']} is {task.status()['state']}"
            )
            time.sleep(10)

        if task.status()['state'] == 'COMPLETED':
            print(
                f"Task {task.status()['description']} completed successfully")
            return True
        else:
            print(
                f"Task {task.status()['description']} failed with error: {task.status()['error_message']}"
            )
            return False

    def download_from_gcs(blob_name, destination_file_name):
        blob = bucket.blob(blob_name)
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded {blob_name} to {destination_file_name}")

    def process_soil_type(soil_type, soil_image):
        for year in range(2023, 2024):
            # Get crop mask
            if year > 2007:
                start_date = f'{year}-01-01'
                end_date = f'{year}-12-31'
                dataset = ee.ImageCollection('USDA/NASS/CDL') \
                    .filter(ee.Filter.date(start_date, end_date)) \
                    .first()
                crop_mask = dataset.select('cropland').eq(5)  # 5 for soybeans
            else:
                mcd_band = f'MODIS/061/MCD12Q1/{year}_01_01'
                crop_mask = ee.Image(mcd_band).select('LC_Type1').clip(aoi).eq(
                    12)

            # Process soil data
            county_data = soil_image.updateMask(crop_mask) \
                .reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=250,
                maxPixels=1e13
            )

            # Prepare data for export
            feature = ee.Feature(None, county_data)
            feature = feature.set('year', year)

            # Export data
            task_name = f'{soil_type}_mean_{year}'
            file_name = f'input2/{task_name}'  # Using 'input2/' prefix as in the original code
            task = ee.batch.Export.table.toCloudStorage(
                collection=ee.FeatureCollection([feature]),
                description=task_name,
                bucket='nifa-webgis-bucket',
                fileNamePrefix=file_name,
                fileFormat='CSV')
            task.start()

            if wait_for_task(task):
                print(f"Task {task_name} completed. File exported to GCS.")
                local_file_path = os.path.join(output_folder,
                                               f'{task_name}.csv')
                download_from_gcs(f'{file_name}.csv', local_file_path)
            else:
                print(
                    f"Task {task_name} failed. Please check the Earth Engine task manager for more details."
                )

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Process each soil property
    for soil_type, soil_image in soil_properties.items():
        process_soil_type(soil_type, soil_image)

    print(
        "All soil property tasks have been completed and files have been downloaded to the specified local folder."
    )


def submit_and_download_task(task, output_path, file_prefix):
    task.start()
    return {
        'task': task,
        'output_path': output_path,
        'file_prefix': file_prefix
    }


def wait_for_tasks(tasks):
    while tasks:
        for task_info in tasks[:]:
            if task_info['task'].status()['state'] in [
                    'COMPLETED', 'FAILED', 'CANCELLED'
            ]:
                if task_info['task'].status()['state'] == 'COMPLETED':
                    download_from_gcs(task_info['output_path'],
                                      task_info['file_prefix'])
                tasks.remove(task_info)
        if tasks:
            print(f"Waiting for {len(tasks)} tasks to complete...")
            time.sleep(30)


def download_from_gcs(output_path, file_prefix):
    storage_client = storage.Client()
    bucket = storage_client.bucket('nifa-webgis-bucket')
    blob = bucket.blob(f'input2/{file_prefix}.csv')
    local_file_path = os.path.join(output_path, f'{file_prefix}.csv')
    blob.download_to_filename(local_file_path)
    print(f'File downloaded to {local_file_path}')


def copy_and_rename_2001_data(output_path):
    import shutil
    # List of prefixes for the files we need to copy
    prefixes = [
        'EVI_mean_', 'GCI_mean_', 'NDWI_mean_', 'NDVI_mean_', 'GLDAS_mean_',
        'LSTday_daily_mean_', 'LSTnight_daily_mean_', 'PRISM_mean_ppt_',
        'PRISM_mean_temp_', 'PRISM_mean_vpd_', 'awc_mean_', 'cec_mean_',
        'som_mean_'
    ]

    for prefix in prefixes:
        source_file = os.path.join(output_path, f'{prefix}2002.csv')
        destination_file = os.path.join(output_path, f'{prefix}2001.csv')

        if os.path.exists(
                source_file) and not os.path.exists(destination_file):
            shutil.copy2(source_file, destination_file)
            print(f"Copied {source_file} to {destination_file}")

        source_file = os.path.join(output_path, f'{prefix}2022.csv')
        destination_file = os.path.join(output_path, f'{prefix}2023.csv')

        if os.path.exists(
                source_file) and not os.path.exists(destination_file):
            shutil.copy2(source_file, destination_file)
            print(f"Copied {source_file} to {destination_file}")


def download_all(geojson_path, output_path, storage_client):
    download_gee_data(geojson_path, output_path)
    download_modis_vi(geojson_path, output_path)
    download_prism_data(geojson_path, output_path)
    download_modis_lst(geojson_path, output_path)
    process_soil_properties(geojson_path, output_path, storage_client)


def download(requestID):
    os.environ["GCLOUD_PROJECT"] = "nifa-webgis"

    # Initialize GCP services once
    storage_client = initialize_gcp_services()

    # create output path
    output_path = f"csv_{requestID}"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    geojson_path = f"request_{requestID}.json"
    download_all(geojson_path, output_path, storage_client)


if __name__ == "__main__":
    download("id1")
