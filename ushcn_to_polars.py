import tarfile
import os
import polars as pl
import glob

# Configuration
RAW_DATA_DIR = 'source-data/raw/20250419'  # Directory containing .tar.gz files
DATASET_TYPES = ['raw', 'tob', 'FLs.52j']  
ELEMENTS = ['tmax', 'tmin', 'tavg', 'prcp'] 

# Function to extract tar.gz files
def extract_tar_gz(file_path, extract_path='.'):
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(path=extract_path, filter="data")  # Use "data" for safe extraction

# Function to parse the station file
def parse_stations(file_path):
    # Define schema for stations based on readme.txt
    schema = {
        'country_code': pl.Utf8,
        'network_code': pl.Utf8,
        'coop_id': pl.Utf8,
        'latitude': pl.Float64,
        'longitude': pl.Float64,
        'elevation': pl.Float64,
        'state': pl.Utf8,
        'name': pl.Utf8,
        'component_1': pl.Utf8,
        'component_2': pl.Utf8,
        'component_3': pl.Utf8,
        'utc_offset': pl.Int32
    }
    
    # Read fixed-width file
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            record = {
                'country_code': line[0:2].strip(),
                'network_code': line[2:3].strip(),
                'coop_id': line[5:11].strip(),
                'latitude': float(line[12:20].strip()) if line[12:20].strip() else None,
                'longitude': float(line[21:30].strip()) if line[21:30].strip() else None,
                'elevation': float(line[32:37].strip()) if line[32:37].strip() != '-999.9' else None,
                'state': line[38:40].strip(),
                'name': line[41:71].strip(),
                'component_1': line[72:78].strip() if line[72:78].strip() != '------' else None,
                'component_2': line[79:85].strip() if line[79:85].strip() != '------' else None,
                'component_3': line[86:92].strip() if line[86:92].strip() != '------' else None,
                'utc_offset': int(line[93:95].strip()) if line[93:95].strip() else None
            }
            data.append(record)
    
    return pl.DataFrame(data, schema=schema)

# Function to parse data file
def parse_element_data(file_path, element, dataset_type):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            record = {
                'country_code': line[0:2].strip(),
                'network_code': line[2:3].strip(),
                'coop_id': line[5:11].strip(),
                'year': int(line[12:16].strip())
            }
            for month in range(1, 13):
                start = 16 + (month - 1) * 9
                value = int(line[start:start+6].strip())
                monthly_record = {
                    'coop_id': record['coop_id'],
                    'year': record['year'],
                    'month': month,
                    'element': element,
                    'dataset_type': dataset_type,
                    'value': value if value != -9999 else None,
                    'dmflag': line[start+6:start+7].strip() or None,
                    'qcflag': line[start+7:start+8].strip() or None,
                    'dsflag': line[start+8:start+9].strip() or None
                }
                data.append(monthly_record)
    
    # Define schema for monthly data
    schema = {
        'coop_id': pl.Utf8,
        'year': pl.UInt16,
        'month': pl.UInt8,
        'element': pl.Utf8,
        'dataset_type': pl.Utf8,
        'value': pl.Float64,
        'dmflag': pl.Utf8,
        'qcflag': pl.Utf8,
        'dsflag': pl.Utf8
    }
    
    df = pl.DataFrame(data, schema=schema)
    
    # Convert values: temperature (hundredths of °C to °C), precipitation (tenths of mm to mm)
    if element in ['tmax', 'tmin', 'tavg']:
        df = df.with_columns(pl.col('value') / 100.0)
    else:  # prcp
        df = df.with_columns(pl.col('value') / 10.0)
    
    return df

# Process station data
def process_stations():
    # Parse stations
    data_dir = 'source-data/raw/20250419'
    station_file = os.path.join(data_dir, 'ushcn-v2.5-stations.txt')
    if os.path.exists(station_file):
        print('Processing stations...')
        stations_df = parse_stations(station_file)
        stations_df.write_parquet('ushcn_stations.parquet')
        print('Saved stations to ushcn_stations.parquet')
    else:
        print(f'Station file {station_file} not found.')
        return
    
# Process element data
def process_elements():
    # Extract all .tar.gz files
    raw_data_dir = 'source-data/raw/20250419'
    for file in glob.glob(f'{raw_data_dir}/ushcn.*.latest.*.tar.gz'):
        print(f'Extracting {file}...')
        extract_tar_gz(file, raw_data_dir)
    
    # Find the extracted directory
    extracted_dirs = glob.glob(f'{raw_data_dir}/ushcn.v2.5.5*')
    if not extracted_dirs:
        print('No extracted directories found.')
        return
    extracted_data_dir = extracted_dirs[0]
    

    # Parse and combine data for each element
    data_dfs = []
    for element in ELEMENTS:
        for dataset_type in DATASET_TYPES:
            # Find all files for this element and dataset type
            data_files = glob.glob(os.path.join(extracted_data_dir, f'*.{dataset_type}.{element}'))
            if data_files:
                print(f'Processing {element}:{dataset_type} data ({len(data_files)} files)...')
                for data_file in data_files:
                    data_df = parse_element_data(data_file, element, dataset_type)
                    data_dfs.append(data_df)
            else:
                print(f'No data files found for {element} with dataset type {dataset_type}.')
    
    if data_dfs:
        # Combine all data into a single DataFrame
        combined_df = pl.concat(data_dfs)
        combined_df.write_parquet('ushcn_monthly_data.parquet')
        print('Saved monthly data to ushcn_monthly_data.parquet')
    else:
        print('No data files processed.')

def main():
    # process_stations()
    process_elements()

if __name__ == '__main__':
    main()
