# First pass on the database
# https://resourcewatch.org/data/explore/Powerwatch?section=Discover&selectedCollection=&zoom=3&lat=0&lng=0&pitch=0&bearing=0&basemap=dark&labels=light&layers=%255B%257B%2522dataset%2522%253A%2522a86d906d-9862-4783-9e30-cdb68cd808b8%2522%252C%2522opacity%2522%253A1%252C%2522layer%2522%253A%25222a694289-fec9-4bfe-a6d2-56c3864ec349%2522%257D%255D&aoi=&page=1&sort=most-viewed&sortDirection=-1
import requests

response = requests.get(
    "https://api.resourcewatch.org/v1/dataset/a86d906d-9862-4783-9e30-cdb68cd808b8/layer/2a694289-fec9-4bfe-a6d2-56c3864ec349"
)

raw_global_power_data = response.json()
print(raw_global_power_data)

# We picked up the dataset_id to check the data
dataset_id = "a86d906d-9862-4783-9e30-cdb68cd808b8"
url = f"https://api.resourcewatch.org/v1/dataset/{dataset_id}"

response = requests.get(url)
data = response.json()

print(data)

# And from this above, we picked up the url
# csv first
# not a fan

import pandas as pd

url = "https://wri-rw.carto.com/api/v2/sql?q=SELECT * FROM powerwatch_data_20180102"

# Read data into a Pandas DataFrame
df = pd.read_csv(url)

# Display the first rows
df.head()

# Let's go to pandas through the json
url = "https://wri-rw.carto.com/api/v2/sql?q=SELECT * FROM powerwatch_data_20180102"
response = requests.get(url)

data = response.json()  # Convert response to JSON
print(data)

# Extract actual data (assuming the JSON structure contains "rows")
power_plants = data.get("rows", [])

# Convert to Pandas DataFrame
df = pd.DataFrame(power_plants)

# Display first few rows
# print(df[0:10].head())
print(df.iloc[:6, : 11])

# Save the data locally as a CSV file
df.to_csv("data/raw/global_power_plants.csv", index=False)