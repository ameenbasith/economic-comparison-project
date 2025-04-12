import sqlite3
import pandas as pd
import os

print("Starting database creation process...")

# Create directory if it doesn't exist
os.makedirs('../data/database', exist_ok=True)

# Connect to SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect('../data/database/economic_data.db')
print("Connected to SQLite database.")

# Load the CSV files
print("Loading CSV files...")
median_home_price = pd.read_csv('../data/raw/median_home_price.csv')
median_income = pd.read_csv('../data/raw/median_household_income.csv')
cpi = pd.read_csv('../data/raw/consumer_price_index.csv')
min_wage = pd.read_csv('../data/raw/minimum_wage.csv')
tuition = pd.read_csv('../data/raw/college_tuition.csv')
print("CSV files loaded successfully.")

# Convert date columns to datetime
print("Processing data...")
median_home_price['date'] = pd.to_datetime(median_home_price['date'])
median_income['date'] = pd.to_datetime(median_income['date'])
cpi['date'] = pd.to_datetime(cpi['date'])
min_wage['date'] = pd.to_datetime(min_wage['date'])
tuition['date'] = pd.to_datetime(tuition['date'])

# Extract year as a new column
median_home_price['year'] = median_home_price['date'].dt.year
median_income['year'] = median_income['date'].dt.year
cpi['year'] = cpi['date'].dt.year

# Create tables and insert data
print("Creating database tables...")
median_home_price.to_sql('median_home_price', conn, if_exists='replace', index=False)
median_income.to_sql('median_household_income', conn, if_exists='replace', index=False)
cpi.to_sql('consumer_price_index', conn, if_exists='replace', index=False)
min_wage.to_sql('minimum_wage', conn, if_exists='replace', index=False)
tuition.to_sql('college_tuition', conn, if_exists='replace', index=False)
print("Basic tables created successfully.")

# Create a view that combines annual data
print("Creating combined economic indicators view...")
conn.execute('DROP VIEW IF EXISTS annual_economic_indicators;')

conn.execute('''
CREATE VIEW annual_economic_indicators AS
WITH home_price_annual AS (
    SELECT 
        year,
        AVG(median_home_price) as median_home_price
    FROM 
        median_home_price
    GROUP BY 
        year
),
income_annual AS (
    SELECT 
        year,
        AVG(median_household_income) as median_household_income
    FROM 
        median_household_income
    GROUP BY 
        year
),
cpi_annual AS (
    SELECT 
        year,
        AVG(consumer_price_index) as consumer_price_index
    FROM 
        consumer_price_index
    GROUP BY 
        year
)
SELECT 
    hp.year,
    hp.median_home_price,
    i.median_household_income,
    c.consumer_price_index
FROM 
    home_price_annual hp
LEFT JOIN 
    income_annual i ON hp.year = i.year
LEFT JOIN 
    cpi_annual c ON hp.year = c.year
WHERE
    hp.median_home_price IS NOT NULL AND
    i.median_household_income IS NOT NULL AND
    c.consumer_price_index IS NOT NULL
ORDER BY 
    hp.year;
''')
print("Annual economic indicators view created successfully.")

# Create a calculated table with adjusted values
print("Creating economic comparison table with calculations...")
conn.execute('DROP TABLE IF EXISTS economic_comparison;')

conn.execute('''
CREATE TABLE economic_comparison AS
WITH base_year AS (
    SELECT 
        consumer_price_index
    FROM 
        annual_economic_indicators
    WHERE 
        year = 2020
)
SELECT 
    a.year,
    a.median_home_price,
    a.median_household_income,
    a.consumer_price_index,
    (a.median_home_price / a.median_household_income) as home_price_to_income_ratio,
    (a.median_home_price * (SELECT consumer_price_index FROM base_year) / a.consumer_price_index) as inflation_adjusted_home_price,
    (a.median_household_income * (SELECT consumer_price_index FROM base_year) / a.consumer_price_index) as inflation_adjusted_income
FROM 
    annual_economic_indicators a
ORDER BY
    a.year;
''')
print("Economic comparison table created successfully.")

# Create "what would need to happen" table
print("Creating affordability comparison table...")
conn.execute('DROP TABLE IF EXISTS affordability_comparison;')

conn.execute('''
CREATE TABLE affordability_comparison AS
WITH current_data AS (
    SELECT 
        home_price_to_income_ratio
    FROM 
        economic_comparison
    WHERE 
        year = (SELECT MAX(year) FROM economic_comparison)
)
SELECT 
    e.year as comparison_year,
    (SELECT home_price_to_income_ratio FROM current_data) as current_ratio,
    e.home_price_to_income_ratio as historical_ratio,
    (1 - (e.home_price_to_income_ratio / (SELECT home_price_to_income_ratio FROM current_data))) * 100 as home_price_decrease_needed,
    ((SELECT home_price_to_income_ratio FROM current_data) / e.home_price_to_income_ratio - 1) * 100 as income_increase_needed
FROM 
    economic_comparison e
WHERE 
    e.year IN (1970, 1980, 1990, 2000, 2010);
''')
print("Affordability comparison table created successfully.")

# Create decade summary table
print("Creating decade summary table...")
conn.execute('DROP TABLE IF EXISTS decade_summary;')

conn.execute('''
CREATE TABLE decade_summary AS
SELECT 
    CAST(year/10 * 10 AS INTEGER) as decade,
    AVG(median_home_price) as avg_home_price,
    AVG(median_household_income) as avg_income,
    AVG(home_price_to_income_ratio) as avg_price_to_income_ratio,
    AVG(inflation_adjusted_home_price) as avg_adj_home_price,
    AVG(inflation_adjusted_income) as avg_adj_income
FROM 
    economic_comparison
GROUP BY 
    CAST(year/10 * 10 AS INTEGER)
ORDER BY 
    decade;
''')
print("Decade summary table created successfully.")

# Create a verification query
print("\nVerifying data in tables:")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM median_home_price")
print(f"Median home price records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM economic_comparison")
print(f"Economic comparison records: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM decade_summary")
print(f"Decade summary records: {cursor.fetchone()[0]}")

conn.close()
print("\nDatabase created successfully with all tables and views!")
print("Location: data/database/economic_data.db")