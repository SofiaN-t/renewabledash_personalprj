# Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Global power plants
df = pd.read_csv('data/raw/global_power_plants.csv', low_memory=False)
# First checks
print(df.head())
print(df.tail())
df.info()
# It appears that we have a lot of missing values for the generation and the estimated generation
df.shape
df.columns.values
# 'cartodb_id', 'the_geom', 'the_geom_webmercator', 'country',
#       'country_long', 'name', 'gppd_idnr', 'capacity_mw', 'latitude',
#       'longitude', 'primary_fuel', 'other_fuel1', 'other_fuel2',
#       'other_fuel3', 'commissioning_year', 'owner', 'source', 'url',
#       'geolocation_source', 'wepp_id', 'year_of_capacity_data' (The year when the reported or estimated capacity value (capacity_mw) was last updated or confirmed),
#       'generation_gwh_YYYY', 'estimated_generation_gwh_YYYY', 'estimated_generation_note_YYYY'

df.describe(include=[np.number]).iloc[:, :5]
df.describe(include=[object]).iloc[:, 1:4]

# Missing
df.isnull().sum()[df.isnull().sum() > 0]
# df.isnull().sum()


# Explore
sorted(df.country_long.unique())
df.country.nunique()

sorted(df.primary_fuel.unique())

df.year_of_capacity_data.unique()

df[(df['primary_fuel'] == 'Wind')].groupby(['country'])['capacity_mw'].sum()

df[(df['primary_fuel'] == 'Wind')].groupby(['country']).agg(
    total_capacity_mw=('capacity_mw', 'sum'),
    avg_capacity_mw=('capacity_mw', 'mean')
)

df['generation_gwh_2017'].hist()
plt.show()
df['capacity_mw'].hist()
plt.show()

# Filter for up-to-date capacity data
df_f = df[df["year_of_capacity_data"] >= 2018]
df_f.shape # 24582 rows removed -- so much for updated

