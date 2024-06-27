import os
import pandas as pd

# Specify the directory path of the raw IFCB data
directory = '/Users/alisonchase/Documents/IFCB/TaraEuropa/7_IFCB/2023/'

#TSG_file = '/Users/alisonchase/Documents/IFCB/TaraEuropa/TaraEuropa_InLine_TSG_20230403_20231109_Product_v20240131.csv'
TSG_file = '/Users/alisonchase/Documents/IFCB/TaraEuropa/TaraEuropa_InLine_TSG_20230403_20231109_Product_v20240131.csv'

# Get all file names in the directory
file_names = os.listdir(directory)

# Create a DataFrame with a column of file names without extension
df = pd.DataFrame({'BinId': [os.path.splitext(file)[0] for file in file_names]})

# Extract DateTime from file names and create a new column
df['date_str'] = df['BinId'].str[1:9]
df['time_str'] = df['BinId'].str[10:16]
df['date_time_str'] = df['date_str'] + df['time_str']

df['DateTime'] = pd.to_datetime(df['date_time_str'], format='%Y%m%d%H%M%S')

df = df.sort_values(by='DateTime')

df = df.drop_duplicates(subset='BinId', keep='first')

df['Type'] = 'inline'
df['Concentration'] = 1
df['Flag'] = 1
df['Depth'] = 1.5

# Load the TSG text file

data = pd.read_csv(TSG_file)
data['dt'] = pd.to_datetime(data['dt'])
data = data.rename(columns={'dt': 'DateTime'})

data = data.sort_values(by='DateTime')



tolerance = pd.Timedelta('1 hour')

# Merge the data based on DateTime and select specific columns
merged_df = pd.merge_asof(df, data, on='DateTime', direction='nearest', tolerance=tolerance)

# Print the merged DataFrame
#print(merged_df)

# Print the DataFrame
#print(df)

columns_to_keep = ['BinId', 'DateTime', 'lat', 'lon', 'sss', 'sst', 'Type', 'Concentration', 'Flag', 'Depth']
new_df = merged_df[columns_to_keep]

new_df = new_df.rename(columns={'BinId': 'bin', 'lat': 'Latitude', 'lon': 'Longitude', 'sss': 'Salinity', 'sst': 'Temperature'})

print(new_df)

new_df.to_csv('/Users/alisonchase/Documents/IFCB/TaraEuropa/TaraEuropa-2023-metadata.csv', index=False)