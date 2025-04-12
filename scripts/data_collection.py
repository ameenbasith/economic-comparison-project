import pandas as pd
import requests
import os
from datetime import datetime

# Create directories if they don't exist
os.makedirs('../data/raw', exist_ok=True)

print("Starting data collection process...")

# Download housing price data directly without API key
print("Downloading median home price data...")
home_price_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MSPUS"
median_home_price = pd.read_csv(home_price_url)
median_home_price.columns = ['date', 'median_home_price']
median_home_price['date'] = pd.to_datetime(median_home_price['date'])
median_home_price.to_csv('../data/raw/median_home_price.csv', index=False)
print("Home price data downloaded successfully.")

# Download median household income data
print("Downloading median household income data...")
income_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MEHOINUSA646N"
median_income = pd.read_csv(income_url)
median_income.columns = ['date', 'median_household_income']
median_income['date'] = pd.to_datetime(median_income['date'])
median_income.to_csv('../data/raw/median_household_income.csv', index=False)
print("Income data downloaded successfully.")

# Download CPI data
print("Downloading consumer price index data...")
cpi_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
cpi = pd.read_csv(cpi_url)
cpi.columns = ['date', 'consumer_price_index']
cpi['date'] = pd.to_datetime(cpi['date'])
cpi.to_csv('../data/raw/consumer_price_index.csv', index=False)
print("CPI data downloaded successfully.")

# Create minimum wage data (manually compiled)
print("Creating minimum wage data...")
min_wage_data = {
    'year': [1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023],
    'federal_min_wage': [1.60, 2.10, 3.10, 3.35, 3.80, 4.25, 5.15, 5.15, 7.25, 7.25, 7.25, 7.25]
}
min_wage_df = pd.DataFrame(min_wage_data)
min_wage_df['date'] = pd.to_datetime(min_wage_df['year'], format='%Y')
min_wage_df.to_csv('../data/raw/minimum_wage.csv', index=False)
print("Minimum wage data created successfully.")

# Create college tuition data (manually compiled)
print("Creating college tuition data...")
tuition_data = {
    'year': [1970, 1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023],
    'avg_public_tuition': [500, 640, 800, 1300, 2100, 2800, 3500, 5800, 7600, 9400, 10500, 11600],
    'avg_private_tuition': [1900, 2500, 3500, 6100, 9300, 12200, 16000, 22000, 27000, 32000, 36000, 39400]
}
tuition_df = pd.DataFrame(tuition_data)
tuition_df['date'] = pd.to_datetime(tuition_df['year'], format='%Y')
tuition_df.to_csv('../data/raw/college_tuition.csv', index=False)
print("College tuition data created successfully.")

print("All data collection complete! Files saved to data/raw directory.")