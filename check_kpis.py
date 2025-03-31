# Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Global power plants
df = pd.read_csv('data/raw/global_power_plants.csv', low_memory=False)

# Since we see there are a lot of missing data, we'll filter by country's completeness
# Here, we are interested in the renewable mix based on generation
# Let's define the primary_fuel
sorted(df['primary_fuel'].unique())
df.loc[df['primary_fuel']=='Wave and Tidal', 'primary_fuel'] = 'Wave_Tidal'

re_fuel = ['Biomass', 'Geothermal', 'Hydro', 'Solar', 'Storage', 'Waste', 'Wave_Tidal', 'Wind']
non_re_fuel = ['Coal', 'Cogeneration', 'Gas', 'Oil', 'Petcoke']
nuclear = ['Nuclear']

conditions = [
    (df['primary_fuel'].isin(re_fuel)),
    (df['primary_fuel'].isin(non_re_fuel)),
    (df['primary_fuel']=='Nuclear'),
    (df['primary_fuel']=='Other')
]
values = ['renewable', 'non_renewable', 'nuclear', 'other']

df['fuel_type'] = np.select(conditions, values, default='unknown')
# you need default otherwise it throws a weird type error

df["fuel_type"].value_counts()
## 0R

# row-wise operation
# df["fuel_type"] = df["primary_fuel"].apply(
#     lambda x: "renewable" if x in re_fuel else (
#         "non-renewable" if x in non_re_fuel else (
#             "nuclear" if x in nuclear else 'other'
#         )
#     )
# )

# Unpivot to long format
# will keep two separate columns for actual and estimated generation
# Actual
cols_to_melt = [f"generation_gwh_{y}" for y in range(2013, 2020)]
df_long_act = df.melt(
    id_vars=["gppd_idnr", "country_long", "primary_fuel", "capacity_mw", "fuel_type", "name"],
    value_vars=cols_to_melt,
    var_name="year",
    value_name="act_generation"
)
df_long_act["year"] = df_long_act["year"].str.extract(r"(\d+)$").astype(int)
# Estimated
cols_to_melt = [f"estimated_generation_gwh_{y}" for y in range(2013, 2018)]
df_long_est = df.melt(
    id_vars=["gppd_idnr", "country_long", "primary_fuel", "capacity_mw", "fuel_type", "name"],
    value_vars=cols_to_melt,
    var_name="year",
    value_name="est_generation"
)
df_long_est["year"] = df_long_est["year"].str.extract(r"(\d+)$").astype(int)
# Combine
df_long = df_long_act.merge(df_long_est, how='outer', on=["gppd_idnr", "country_long", "primary_fuel", "capacity_mw", "fuel_type", "name", "year"])

df_long.head(10)

# Explore KPIs
# Here, we are interested in the renewable mix based on generation
# Let's remind ourselves of how the df looks like
df_long.isnull().sum()
# The cols we are most interested on are the most empty
# Also, let's check whether we have updated data
df["year_of_capacity_data"].isnull().sum() / df.shape[0]
# 57% of the data have not beem cheched at all
(df["year_of_capacity_data"].value_counts() / df.shape[0]).sort_values
# Roughly 30% has been checked in the last decade

# We'll work with what we have, ignoring the year_of_capacity
# Let's focus on the generation
# Let's make an additional col where we use actual generation when exists and estimated when it doesn't
df_long["generation"] = df_long["act_generation"].combine_first(df_long["est_generation"])

# Now, we'll filter based on generation to keep the countries that are complete
key_cols = [
    "generation",
    "primary_fuel"
]

missing_by_country = df_long.groupby("country_long")[key_cols].apply(lambda x: x.isnull().mean()).sort_values(by="country_long").reset_index()
missing_by_country.head()
missing_by_country.loc[missing_by_country['generation']<=0.4]
(missing_by_country.loc[missing_by_country['generation']<=0.4]).shape[0]
missing_by_country.sort_values(by='generation')
# From 167 we drop to 27 countries
# missing_by_country["avg_missing"] = missing_by_country.mean(axis=1)
# missing_by_country.sort_values(by='avg_missing', ascending=False)

# So, let's filter with those
complete_countries = missing_by_country.loc[missing_by_country['generation']<=0.4]['country_long'].tolist()
df_f = df_long.loc[df_long['country_long'].isin(complete_countries)]

# Let's explore some graphs
df_fuel = df_f.groupby(['country_long', 'fuel_type']).size().unstack().fillna(0) #size is a property of groupby

# Mix by country
df_fuel_pct = df_fuel.div(df_fuel.sum(axis=1), axis=0) * 100  # Convert to percentage
df_fuel_pct.plot(kind='bar', stacked=True, figsize=(14, 8), colormap='Set3')
plt.title('Primary Fuel Mix by Country (%)')
plt.xlabel('Country')
plt.ylabel('%')
plt.xticks(rotation=90)
plt.show()

df_generation = df_f.groupby('country_long').agg({
    'generation': 'sum',
    'fuel_type': lambda x: (x == 'renewable').sum()
})
df_generation = df_f.groupby(['country_long', 'fuel_type'])['generation'].sum().unstack().fillna(0).reset_index()
df_generation['total_generation'] = df_generation.sum(axis=1, numeric_only=True)
df_generation['renewable_share'] = df_generation['renewable'] / df_generation['total_generation']
df_generation['non_renewable_share'] = df_generation['non_renewable'] / df_generation['total_generation']
df_generation['nuclear_share'] = df_generation['nuclear'] / df_generation['total_generation']
df_generation['other_share'] = df_generation['other'] / df_generation['total_generation']
df_generation.head()

df_generation.loc[df_generation['country_long']=='Sweden']

# Plot pie chart for the top countries by renewable share
bottom_countries = df_generation.sort_values('renewable_share', ascending=True).head(10)

for country in bottom_countries['country_long']:
    renewable = df_generation[df_generation['country_long'] == country]['renewable_share'].values[0]*100
    non_renewable = df_generation[df_generation['country_long'] == country]['non_renewable_share'].values[0]*100
    nuclear = df_generation[df_generation['country_long'] == country]['nuclear_share'].values[0]*100
    other = df_generation[df_generation['country_long'] == country]['other_share'].values[0]*100
    
    plt.figure(figsize=(7, 7))
    plt.pie([renewable, non_renewable, nuclear, other], labels=['Renewable', 'Non-Renewable', 'Nuclear', 'Other'], autopct='%1.2f%%', startangle=140)
    plt.title(f'Renewable vs Non-Renewable Energy Generation in {country}')
    plt.show()

df_generation.head()

## Let's check what is happening with the 100% renewable countries
fully_renewable_countries = df_generation[df_generation['renewable_share'] == 1]['country_long']

for country in fully_renewable_countries[:5]:
    country_data = df_f[df_f['country_long'] == country]
    
    # Check if non-renewable plants exist
    non_renewable_plants = country_data[country_data['fuel_type'] == 'non_renewable']
    
    if not non_renewable_plants.empty:
        # Check if they have missing generation data
        missing_non_renewable = non_renewable_plants['generation'].isna().sum()
        
        if missing_non_renewable > 0:
            print(f"\n{country} appears 100% renewable, but has {missing_non_renewable} non-renewable plants with missing data.")
        else:
            print(f"\n{country} has non-renewable plants, but all have generation data.")    
    else:
        print(f"\n{country} has no non-renewable plants registered.")

# Ok, is the 100% renewables actually true or are countries lacking info on power plants?
# We'll check the total generation over the available years
df_f_filtered = df_f.groupby('country_long')['generation'].sum().reset_index()     
df_f_filtered.loc[df_f_filtered['country_long'].isin(fully_renewable_countries)]

# Now, are these results consistentfor every available year?
# First, we need to extract the relevant columns for the generation data and the 'fuel_type' for renewable vs non-renewable.
# For simplicity, assume you already have a 'generation' column (actual + estimated) and 'fuel_type' column.

# Iterate over each country and check if renewable generation remains at 100% over multiple years
for country in fully_renewable_countries[:5]:  # Adjust the number for the countries you'd like to inspect
    country_data = df_f[df_f['country_long'] == country]

    # Check if renewable generation is always 100% for every year
    renewable_data = country_data[country_data['fuel_type'] == 'renewable']
    non_renewable_data = country_data[country_data['fuel_type'] == 'non_renewable']

    # Check the total generation for each year to see if non-renewables appear
    print(f"Country: {country}")
    for year in country_data['year'].unique():
        year_data = country_data[country_data['year'] == year]
        total_generation = year_data['generation'].sum()
        non_renewable_generation = non_renewable_data[non_renewable_data['year'] == year]['generation'].sum()

        print(f" Year: {year} - Total Generation: {total_generation} - Non-Renewable Generation: {non_renewable_generation}")
        
        # Evaluate if there's generation reported from non-renewables in the year
        if non_renewable_generation == 0:
            print(f"   No non-renewable generation in {year}.")
        else:
            print(f"   Some non-renewable generation in {year}.")

# Check missing non-renewable data
# Check if missing non-renewable generation data is consistently reported across years
for country in fully_renewable_countries:  # Adjust number to inspect a subset
    country_data = df_f[df_f['country_long'] == country]

    # Check for missing non-renewable generation data by year
    missing_non_renewable_data = country_data[country_data['fuel_type'] == 'non_renewable']
    missing_data_per_year = missing_non_renewable_data.groupby('year')['generation'].apply(lambda x: x.isna().sum())

    print(f"Missing non-renewable generation data for {country}:")
    print(missing_data_per_year)

    # If any year has a missing value, print a message
    if missing_data_per_year.sum() > 0:
        print(f"  Missing data found in the following years for {country}: {missing_data_per_year[missing_data_per_year > 0].index.tolist()}")



## Compare approaches
df_all_years = df_f.groupby(['country_long', 'fuel_type'])['generation'].sum().unstack(fill_value=0)
df_all_years['renewable_share'] = df_all_years['renewable'] / df_all_years.sum(axis=1)

df_all_years.head()

# Filter for the most recent year only
recent_year = 2017
df_recent_year = df_f[df_f['year'] == recent_year].groupby(['country_long', 'fuel_type'])['generation'].sum().unstack(fill_value=0)
df_recent_year['renewable_share'] = df_recent_year['renewable'] / df_recent_year.sum(axis=1)

# Sort by renewable share in both cases
top_countries_all_years = df_all_years.sort_values('renewable_share', ascending=False).tail(10)
top_countries_recent_year = df_recent_year.sort_values('renewable_share', ascending=False).tail(10)

# Plot side-by-side comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Bar plot for all years
axes[0].bar(top_countries_all_years.index, top_countries_all_years['renewable_share'], color='green')
axes[0].set_title("Renewable Share (All Years)")
axes[0].set_ylabel("% Renewable Generation")
axes[0].set_xticklabels(top_countries_all_years.index, rotation=90)

# Bar plot for recent year
axes[1].bar(top_countries_recent_year.index, top_countries_recent_year['renewable_share'], color='blue')
axes[1].set_title(f"Renewable Share ({recent_year})")
axes[1].set_ylabel("% Renewable Generation")
axes[1].set_xticklabels(top_countries_recent_year.index, rotation=90)

plt.tight_layout()
plt.show()





## DEPR ##
# Exploring unpivoting
    # df_long = pd.wide_to_long(
    #     df,
    #     stubnames=["generation", "estimated_generation"],
    #     i=["gppd_idnr", "country_long", "primary_fuel", "capacity_mw", "fuel_type"],
    #     j="year",
    #     sep="_gwh_",
    #     suffix="\d+"
    # ).reset_index()
    # df_long[['gppd_idnr', 'country_long', 'primary_fuel', 'capacity_mw', 'year', 'name', 'generation', 'estimated_generation']].head(10)
    # # Remember that here, all columns are kept

    # gen_actual_cols = [f"generation_gwh_{y}" for y in range(2013, 2020)]
    # gen_est_cols = [f"estimated_generation_gwh_{y}" for y in range(2013, 2018)]
    # cols_to_melt = gen_actual_cols + gen_est_cols
    # df_long = df.melt(
    #     id_vars=["gppd_idnr", "country_long", "primary_fuel", "capacity_mw", "fuel_type", "name"],
    #     value_vars=cols_to_melt,
    #     var_name="original_column",
    #     value_name="generation"
    # )
    # df_long["year"] = df_long["original_column"].str.extract(r"(\d+)$").astype(int)
    # df_long["source"] = df_long["original_column"].str.extract(r"^(.*)_gwh_")

    # #df_long.loc[df_long['gppd_idnr'] == 'WRI1023788'][['gppd_idnr', 'country_long', 'primary_fuel', 'capacity_mw', 'year', 'name', 'source', 'generation']]

    # df_long.head()
    # df_long['source'].unique()











# Here, we are interested in the renewable mix based on capacity
# So, we'll filter based on those parameters
# key_cols = [
#     "capacity_mw",
#     "primary_fuel"
# ]

# missing_by_country = df.groupby("country_long")[key_cols].apply(lambda x: x.isnull().mean()).sort_values(by="capacity_mw")

# missing_by_country.info()
# missing_by_country.head()

# missing_by_country["avg_missing"] = missing_by_country.mean(axis=1)
# missing_by_country.sort_values(by='avg_missing', ascending=False)
# # So, we have full capacity information for all countries

# # Not relevant here (as all countries are complete in terms of capacity)
# missing_by_country = missing_by_country.reset_index()
# complete_countries = missing_by_country.loc[missing_by_country['avg_missing']<0.2]['country_long'].tolist()

# complete_countries = missing_by_country[missing_by_country["avg_missing"] < 0.2].index.tolist()
# df_filtered = df[df["country_long"].isin(complete_countries)]
# df_filtered.head()