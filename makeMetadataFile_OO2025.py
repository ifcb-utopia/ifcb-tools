import sys
print(sys.executable)

import os
import pandas as pd

# Specify the directory path of the raw IFCB data
directory = '/Users/alisonchase/Library/CloudStorage/Dropbox/Ocean_Optics_Class/OOClass2025/IFCB185/raw/'

# Specify the path to the TSG file
TSG_file = '/Users/alisonchase/Library/CloudStorage/Dropbox/Ocean_Optics_Class/OOClass2025/IFCB185/tsg.csv'
GPS_file = '/Users/alisonchase/Library/CloudStorage/Dropbox/Ocean_Optics_Class/OOClass2025/IFCB185/gps.csv'

# Specific the path for the output metadata file
output_path = '/Users/alisonchase/Library/CloudStorage/Dropbox/Ocean_Optics_Class/OOClass2025/IFCB185/OO2025_IFCB_metadata.csv'

# Get all file names in the directory
file_names = os.listdir(directory)

# Create a DataFrame with a column of file names without extension
df = pd.DataFrame({'BinId': [os.path.splitext(file)[0] for file in file_names]})

# Extract DateTime from file names and create a new column
df['date_str'] = df['BinId'].str[1:9]
df['time_str'] = df['BinId'].str[10:16]
df['date_time_str'] = df['date_str'] + df['time_str']

print(df)
df['DateTime'] = pd.to_datetime(df['date_time_str'], format='%Y%m%d%H%M%S')

df = df.sort_values(by='DateTime')

df = df.drop_duplicates(subset='BinId', keep='first')

 # Add columns that are required by ifcb-tools processing codes; update values as appropriate 
df['Type'] = 'inline'
df['Concentration'] = 1
df['Flag'] = 1
df['Depth'] = 1.5

# Load the TSG text file
# Load the GPS file
gps_data = pd.read_csv(GPS_file)
gps_data['dt'] = pd.to_datetime(gps_data['dt'])
gps_data = gps_data.rename(columns={'dt': 'DateTime'})

# Merge TSG and GPS data on DateTime (nearest match within 1 minute)
tsg_data = pd.read_csv(TSG_file)
tsg_data['dt'] = pd.to_datetime(tsg_data['dt'])
tsg_data = tsg_data.rename(columns={'dt': 'DateTime'})

tsg_gps_merged = pd.merge_asof(tsg_data.sort_values('DateTime'),
                               gps_data.sort_values('DateTime'),
                               on='DateTime', direction='nearest', tolerance=pd.Timedelta('1 minute'))
data = tsg_gps_merged

# data = pd.read_csv(TSG_file)
# data['dt'] = pd.to_datetime(data['dt'])
# data = data.rename(columns={'dt': 'DateTime'})

# data = data.sort_values(by='DateTime')

tolerance = pd.Timedelta('1 hour')

# Merge the data based on DateTime and select specific columns
merged_df = pd.merge_asof(df, data, on='DateTime', direction='nearest', tolerance=tolerance)

# Print the merged DataFrame
#print(merged_df)

# Print the DataFrame
#print(df)

columns_to_keep = ['BinId', 'DateTime', 'lat', 'lon', 's', 't1', 'Type', 'Concentration', 'Flag', 'Depth']
new_df = merged_df[columns_to_keep]

# Rename the columns based on what is required by subsequent processing codes
new_df = new_df.rename(columns={'BinId': 'bin', 'lat': 'Latitude', 'lon': 'Longitude', 's': 'Salinity', 't1': 'Temperature'})

print(new_df)

# Write the metadata file as a csv
new_df.to_csv(output_path, index=False)