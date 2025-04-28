import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Set page configuration
st.set_page_config(
    page_title="Housing Affordability Time Machine",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application title and introduction
st.title("Housing Affordability Time Machine")
st.markdown("""
This dashboard explores housing affordability trends since 1970, comparing current economic conditions 
with historical periods. The analysis focuses on the relationship between housing prices, income, 
and what would need to change to return to historical affordability levels.
""")

# Instructions for setup
with st.expander("📋 Setup Instructions"):
    st.markdown("""
    ### How to Run With Your Own Data

    1. Make sure you have run the data collection and database creation scripts:
    ```bash
    python scripts/data_collection.py
    python scripts/create_database.py
    ```

    2. The app will look for the database in these locations:
       - `../data/database/economic_data.db`
       - `./data/database/economic_data.db`
       - `data/database/economic_data.db`
       - `economic_data.db`

    3. If no database is found, sample data will be generated for demonstration purposes.

    4. If using sample data, a warning will be displayed in the sidebar.
    """)


# Function to load data from SQLite database
@st.cache_data
def load_data():
    """Load data from database or create sample data if database not found"""
    # Try multiple potential database paths
    potential_paths = [
        '../data/database/economic_data.db',
        './data/database/economic_data.db',
        'data/database/economic_data.db',
        'economic_data.db'
    ]

    db_found = False
    for db_path in potential_paths:
        if os.path.exists(db_path):
            try:
                # Connect to SQLite database
                conn = sqlite3.connect(db_path)

                # Load the data
                economic_comparison = pd.read_sql("SELECT * FROM economic_comparison", conn)
                affordability_comparison = pd.read_sql("SELECT * FROM affordability_comparison", conn)
                decade_summary = pd.read_sql("SELECT * FROM decade_summary", conn)
                median_home_price = pd.read_sql("SELECT * FROM median_home_price", conn)

                conn.close()
                st.success(f"Successfully loaded database from: {db_path}")
                db_found = True
                return economic_comparison, affordability_comparison, decade_summary, median_home_price
            except Exception as e:
                st.warning(f"Found database at {db_path} but encountered an error: {e}")
                continue

    if not db_found:
        st.warning("Database not found. Creating sample data for demonstration.")

        # Create sample economic comparison data
        years = list(range(1970, 2024, 1))

        # Generate synthetic data with realistic trends
        economic_comparison = pd.DataFrame({
            'year': years,
            'median_home_price': [
                23000 * (1.07 ** (i)) for i in range(len(years))
            ],
            'median_household_income': [
                9870 * (1.045 ** (i)) for i in range(len(years))
            ],
            'consumer_price_index': [
                38.8 * (1.04 ** (i)) for i in range(len(years))
            ]
        })

        # Calculate ratios and adjustments
        economic_comparison['home_price_to_income_ratio'] = economic_comparison['median_home_price'] / \
                                                            economic_comparison['median_household_income']

        # Use 2020 as base year for inflation adjustment
        base_cpi = economic_comparison.loc[economic_comparison['year'] == 2020, 'consumer_price_index'].values[
            0] if 2020 in economic_comparison['year'].values else 258.8

        economic_comparison['inflation_adjusted_home_price'] = economic_comparison['median_home_price'] * (
                    base_cpi / economic_comparison['consumer_price_index'])
        economic_comparison['inflation_adjusted_income'] = economic_comparison['median_household_income'] * (
                    base_cpi / economic_comparison['consumer_price_index'])

        # Create sample affordability comparison
        comparison_years = [1970, 1980, 1990, 2000, 2010]
        current_ratio = economic_comparison.iloc[-1]['home_price_to_income_ratio']

        affordability_comparison = pd.DataFrame({
            'comparison_year': comparison_years,
            'current_ratio': [current_ratio] * len(comparison_years)
        })

        # Get historical ratios
        historical_ratios = []
        for year in comparison_years:
            ratio = economic_comparison.loc[economic_comparison['year'] == year, 'home_price_to_income_ratio'].values[0]
            historical_ratios.append(ratio)

        affordability_comparison['historical_ratio'] = historical_ratios
        affordability_comparison['home_price_decrease_needed'] = (1 - (
                    affordability_comparison['historical_ratio'] / affordability_comparison['current_ratio'])) * 100
        affordability_comparison['income_increase_needed'] = (affordability_comparison['current_ratio'] /
                                                              affordability_comparison['historical_ratio'] - 1) * 100

        # Create sample decade summary
        decades = [1970, 1980, 1990, 2000, 2010, 2020]
        decade_summary = pd.DataFrame({'decade': decades})

        # Calculate decade averages
        for decade in decades:
            decade_data = economic_comparison[(economic_comparison['year'] >= decade) &
                                              (economic_comparison['year'] < decade + 10)]

            if not decade_data.empty:
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_home_price'] = decade_data[
                    'median_home_price'].mean()
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_income'] = decade_data[
                    'median_household_income'].mean()
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_price_to_income_ratio'] = decade_data[
                    'home_price_to_income_ratio'].mean()
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_adj_home_price'] = decade_data[
                    'inflation_adjusted_home_price'].mean()
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_adj_income'] = decade_data[
                    'inflation_adjusted_income'].mean()
            else:
                # Handle the case where there's no data for a decade (e.g., future decades)
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_home_price'] = None
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_income'] = None
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_price_to_income_ratio'] = None
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_adj_home_price'] = None
                decade_summary.loc[decade_summary['decade'] == decade, 'avg_adj_income'] = None

        # Clean up any NaN values
        decade_summary = decade_summary.dropna()

        # Sample home price data (monthly)
        dates = pd.date_range(start='1970-01-01', end='2023-12-31', freq='M')

        # Add some volatility to make it look more realistic
        np.random.seed(42)  # For reproducibility
        volatility = np.random.normal(0, 0.01, size=len(dates))
        trend = np.array([1.07 ** (i / 12) for i in range(len(dates))])

        median_home_price = pd.DataFrame({
            'date': dates,
            'median_home_price': 23000 * trend * (1 + volatility)
        })

        # Add year column
        median_home_price['year'] = median_home_price['date'].dt.year

        return economic_comparison, affordability_comparison, decade_summary, median_home_price


# Load the data
economic_comparison, affordability_comparison, decade_summary, median_home_price = load_data()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Housing Affordability Overview",
     "Affordability Gap Analysis",
     "Decade Comparison",
     "Raw Data Explorer"]
)

if economic_comparison is not None:
    # Disclaimer about sample data
    if not os.path.exists('../data/database/economic_data.db') and not os.path.exists(
            './data/database/economic_data.db'):
        st.sidebar.warning("⚠️ Using synthesized sample data for demonstration purposes")
        st.sidebar.info("The actual data would come from your database")

    # Housing Affordability Overview page
    if page == "Housing Affordability Overview":
        st.header("Housing Affordability Overview")

        # Key metrics in columns
        col1, col2, col3 = st.columns(3)

        # Get latest year's data
        latest_data = economic_comparison.iloc[-1]

        with col1:
            st.metric(
                label="Latest Home Price to Income Ratio",
                value=f"{latest_data['home_price_to_income_ratio']:.2f}x",
                delta=f"{latest_data['home_price_to_income_ratio'] - economic_comparison.iloc[0]['home_price_to_income_ratio']:.2f}x since 1970"
            )

        with col2:
            st.metric(
                label="Latest Median Home Price",
                value=f"${latest_data['median_home_price']:,.0f}",
                delta=f"{(latest_data['median_home_price'] / economic_comparison.iloc[0]['median_home_price'] - 1) * 100:.1f}% since 1970"
            )

        with col3:
            st.metric(
                label="Latest Median Household Income",
                value=f"${latest_data['median_household_income']:,.0f}",
                delta=f"{(latest_data['median_household_income'] / economic_comparison.iloc[0]['median_household_income'] - 1) * 100:.1f}% since 1970"
            )

        # Add year range slider
        selected_years = st.slider(
            "Select Year Range",
            int(economic_comparison['year'].min()),
            int(economic_comparison['year'].max()),
            (int(economic_comparison['year'].min()), int(economic_comparison['year'].max()))
        )

        # Filter data based on selected years
        filtered_data = economic_comparison[
            (economic_comparison['year'] >= selected_years[0]) &
            (economic_comparison['year'] <= selected_years[1])
            ]

        # Housing Affordability Trend Chart
        st.subheader("Housing Affordability Trend (Home Price to Income Ratio)")

        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the trend line
        sns.lineplot(
            data=filtered_data,
            x='year',
            y='home_price_to_income_ratio',
            marker='o',
            linewidth=2,
            color='#1f77b4',
            ax=ax
        )

        # Add a horizontal line for historical average
        historical_avg = economic_comparison['home_price_to_income_ratio'].mean()
        ax.axhline(
            y=historical_avg,
            color='red',
            linestyle='--',
            alpha=0.7
        )

        # Add text label for the average line
        ax.text(
            filtered_data['year'].max() - 2,
            historical_avg + 0.1,
            f'Historical Average: {historical_avg:.2f}x',
            color='red',
            fontsize=10
        )

        # Customize chart
        ax.set_title('Home Price to Income Ratio Over Time', fontsize=14)
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Home Price to Income Ratio', fontsize=12)
        ax.grid(True, alpha=0.3)

        # Show the chart
        st.pyplot(fig)

        # Explanation text
        st.markdown("""
        ### Understanding the Chart
        The **Home Price to Income Ratio** shows how many years of median household income it would 
        take to purchase a median-priced home. A higher ratio indicates decreased affordability.

        - **Key Observation**: Housing affordability has declined significantly since the 1970s
        - The red dashed line represents the historical average ratio
        - Use the year range slider to focus on specific time periods
        """)

        # Compare nominal vs inflation-adjusted values
        st.subheader("Nominal vs. Inflation-Adjusted Values")

        fig, ax = plt.subplots(figsize=(12, 8))

        # Create two y-axes
        ax2 = ax.twinx()

        # Plot median home price (nominal and adjusted)
        sns.lineplot(
            data=filtered_data,
            x='year',
            y='median_home_price',
            color='blue',
            label='Nominal Home Price',
            ax=ax,
            marker='o'
        )

        sns.lineplot(
            data=filtered_data,
            x='year',
            y='inflation_adjusted_home_price',
            color='lightblue',
            label='Inflation-Adjusted Home Price (2020 dollars)',
            ax=ax,
            marker='s'
        )

        # Plot median income (nominal and adjusted)
        sns.lineplot(
            data=filtered_data,
            x='year',
            y='median_household_income',
            color='green',
            label='Nominal Household Income',
            ax=ax2,
            marker='o'
        )

        sns.lineplot(
            data=filtered_data,
            x='year',
            y='inflation_adjusted_income',
            color='lightgreen',
            label='Inflation-Adjusted Income (2020 dollars)',
            ax=ax2,
            marker='s'
        )

        # Customize chart
        ax.set_title('Home Prices vs. Household Income Over Time', fontsize=14)
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Home Price ($)', fontsize=12)
        ax2.set_ylabel('Household Income ($)', fontsize=12)
        ax.grid(True, alpha=0.3)

        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

        # Show the chart
        st.pyplot(fig)

    # Affordability Gap Analysis page
    elif page == "Affordability Gap Analysis":
        st.header("Affordability Gap Analysis")

        st.markdown("""
        This section examines the gap between current and historical housing affordability levels.
        It shows what would need to happen (either home price decrease or income increase) to return
        to the affordability levels of previous decades.
        """)

        # Display the affordability comparison table
        st.subheader("What Would Need to Happen to Return to Historical Affordability")
        st.dataframe(
            affordability_comparison.rename(columns={
                'comparison_year': 'Year',
                'current_ratio': 'Current Price-to-Income Ratio',
                'historical_ratio': 'Historical Price-to-Income Ratio',
                'home_price_decrease_needed': 'Home Price Decrease Needed (%)',
                'income_increase_needed': 'Income Increase Needed (%)'
            }).set_index('Year').style.format({
                'Current Price-to-Income Ratio': '{:.2f}x',
                'Historical Price-to-Income Ratio': '{:.2f}x',
                'Home Price Decrease Needed (%)': '{:.1f}%',
                'Income Increase Needed (%)': '{:.1f}%'
            })
        )

        # Create chart for affordability gap visualization
        st.subheader("Affordability Gap Visualization")

        # Chart options
        metric = st.radio(
            "Select metric to display:",
            ["Home Price Decrease Needed (%)", "Income Increase Needed (%)"]
        )

        column_map = {
            "Home Price Decrease Needed (%)": "home_price_decrease_needed",
            "Income Increase Needed (%)": "income_increase_needed"
        }

        # Create chart
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the selected metric
        bars = sns.barplot(
            data=affordability_comparison,
            x='comparison_year',
            y=column_map[metric],
            palette='viridis',
            ax=ax
        )

        # Add data labels on bars
        for i, p in enumerate(bars.patches):
            ax.annotate(
                f'{p.get_height():.1f}%',
                (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center',
                va='bottom',
                fontsize=10
            )

        # Customize chart
        ax.set_title(f'{metric} to Match Historical Affordability', fontsize=14)
        ax.set_xlabel('Comparison Year', fontsize=12)
        ax.set_ylabel(metric, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')

        # Show the chart
        st.pyplot(fig)

        # Explanation and insights
        st.markdown("""
        ### Key Insights

        - **Significant Gap**: There is a substantial gap between current housing affordability and historical levels
        - **1970s vs Now**: To return to 1970s affordability levels, either home prices would need to decrease 
          dramatically or incomes would need to increase by thousands of percent
        - **Most Recent Comparison**: Even compared to 2010, there has been a notable decline in affordability

        This analysis highlights why many Americans feel that homeownership has become increasingly out of reach
        compared to previous generations.
        """)

    # Decade Comparison page
    elif page == "Decade Comparison":
        st.header("Decade Comparison")

        st.markdown("""
        This section compares economic indicators by decade, providing a broader historical context
        for understanding housing affordability trends.
        """)

        # Display the decade summary table
        st.subheader("Economic Indicators by Decade")
        st.dataframe(
            decade_summary.rename(columns={
                'decade': 'Decade',
                'avg_home_price': 'Avg Home Price ($)',
                'avg_income': 'Avg Household Income ($)',
                'avg_price_to_income_ratio': 'Avg Price-to-Income Ratio',
                'avg_adj_home_price': 'Inflation-Adjusted Home Price (2020$)',
                'avg_adj_income': 'Inflation-Adjusted Income (2020$)'
            }).set_index('Decade').style.format({
                'Avg Home Price ($)': '${:,.0f}',
                'Avg Household Income ($)': '${:,.0f}',
                'Avg Price-to-Income Ratio': '{:.2f}x',
                'Inflation-Adjusted Home Price (2020$)': '${:,.0f}',
                'Inflation-Adjusted Income (2020$)': '${:,.0f}'
            })
        )

        # Create decade comparison charts
        col1, col2 = st.columns(2)

        with col1:
            # Price-to-Income Ratio by Decade
            fig1, ax1 = plt.subplots(figsize=(8, 6))

            bars1 = sns.barplot(
                data=decade_summary,
                x='decade',
                y='avg_price_to_income_ratio',
                palette='Blues',
                ax=ax1
            )

            # Add data labels
            for i, p in enumerate(bars1.patches):
                ax1.annotate(
                    f'{p.get_height():.2f}x',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center',
                    va='bottom',
                    fontsize=10
                )

            ax1.set_title('Average Home Price-to-Income Ratio by Decade', fontsize=12)
            ax1.set_xlabel('Decade', fontsize=10)
            ax1.set_ylabel('Price-to-Income Ratio', fontsize=10)
            ax1.grid(True, alpha=0.3, axis='y')

            st.pyplot(fig1)

        with col2:
            # Inflation-Adjusted Values by Decade
            fig2, ax2 = plt.subplots(figsize=(8, 6))

            # Create separate data for plotting
            decades = decade_summary['decade'].astype(str)
            adj_home_price = decade_summary['avg_adj_home_price'] / 1000  # Convert to thousands
            adj_income = decade_summary['avg_adj_income'] / 1000  # Convert to thousands

            # Set width of bars
            bar_width = 0.35
            x = np.arange(len(decades))

            # Create bars
            bars1 = ax2.bar(x - bar_width / 2, adj_home_price, bar_width, label='Inflation-Adj Home Price')
            bars2 = ax2.bar(x + bar_width / 2, adj_income, bar_width, label='Inflation-Adj Income')

            # Add data labels
            for bar in bars1:
                height = bar.get_height()
                ax2.annotate(f'${height:.0f}K',
                             xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 3),
                             textcoords="offset points",
                             ha='center', va='bottom',
                             fontsize=8)

            for bar in bars2:
                height = bar.get_height()
                ax2.annotate(f'${height:.0f}K',
                             xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 3),
                             textcoords="offset points",
                             ha='center', va='bottom',
                             fontsize=8)

            ax2.set_title('Inflation-Adjusted Values by Decade (2020$)', fontsize=12)
            ax2.set_xlabel('Decade', fontsize=10)
            ax2.set_ylabel('Amount (Thousands of 2020$)', fontsize=10)
            ax2.set_xticks(x)
            ax2.set_xticklabels(decades)
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')

            st.pyplot(fig2)

        # Explanation and insights
        st.markdown("""
        ### Key Observations from Decade Analysis

        - **Most Affordable Decade**: The 1970s had the lowest price-to-income ratio, making it the most affordable decade for homeownership
        - **Growing Divergence**: The gap between inflation-adjusted home prices and incomes has widened over time
        - **Recent Acceleration**: The 2010s and 2020s have seen a dramatic acceleration in the price-to-income ratio
        - **Real Purchasing Power**: When adjusted for inflation, incomes have not kept pace with the rapid increase in home prices

        This decade-by-decade view demonstrates that today's housing affordability challenges represent a significant 
        departure from historical norms.
        """)

    # Raw Data Explorer page
    elif page == "Raw Data Explorer":
        st.header("Raw Data Explorer")

        st.markdown("""
        Explore the raw data used in this analysis. This section allows you to view the underlying data
        and examine specific time periods or metrics in detail.
        """)

        # Select dataset to explore
        dataset = st.selectbox(
            "Select dataset to explore:",
            ["Economic Comparison", "Affordability Comparison", "Decade Summary", "Median Home Price"]
        )

        if dataset == "Economic Comparison":
            st.subheader("Economic Comparison Data")
            st.dataframe(economic_comparison)
            st.download_button(
                label="Download Economic Comparison Data as CSV",
                data=economic_comparison.to_csv(index=False).encode('utf-8'),
                file_name='economic_comparison.csv',
                mime='text/csv',
            )

        elif dataset == "Affordability Comparison":
            st.subheader("Affordability Comparison Data")
            st.dataframe(affordability_comparison)
            st.download_button(
                label="Download Affordability Comparison Data as CSV",
                data=affordability_comparison.to_csv(index=False).encode('utf-8'),
                file_name='affordability_comparison.csv',
                mime='text/csv',
            )

        elif dataset == "Decade Summary":
            st.subheader("Decade Summary Data")
            st.dataframe(decade_summary)
            st.download_button(
                label="Download Decade Summary Data as CSV",
                data=decade_summary.to_csv(index=False).encode('utf-8'),
                file_name='decade_summary.csv',
                mime='text/csv',
            )

        elif dataset == "Median Home Price":
            st.subheader("Median Home Price Data")
            # Show count of records and date range
            st.write(f"Number of records: {len(median_home_price)}")
            st.write(f"Date range: {median_home_price['date'].min()} to {median_home_price['date'].max()}")

            # Option to show sample or all data
            show_option = st.radio("Data display option:", ["Show sample (100 rows)", "Show all data"])

            if show_option == "Show sample (100 rows)":
                st.dataframe(median_home_price.head(100))
            else:
                st.dataframe(median_home_price)

            st.download_button(
                label="Download Median Home Price Data as CSV",
                data=median_home_price.to_csv(index=False).encode('utf-8'),
                file_name='median_home_price.csv',
                mime='text/csv',
            )

        # Custom query option
        st.subheader("Custom SQL Query")
        st.markdown("""
        Advanced users can run custom SQL queries against the database for deeper analysis.
        Example: `SELECT year, median_home_price, median_household_income FROM economic_comparison WHERE year > 2000`
        """)

        custom_query = st.text_area("Enter custom SQL query:", height=100)

        if st.button("Run Query"):
            if custom_query:
                try:
                    # Connect to database
                    conn = sqlite3.connect('../data/database/economic_data.db')

                    # Execute query
                    result = pd.read_sql(custom_query, conn)
                    conn.close()

                    # Display result
                    st.dataframe(result)

                    # Download option
                    st.download_button(
                        label="Download Query Result as CSV",
                        data=result.to_csv(index=False).encode('utf-8'),
                        file_name='query_result.csv',
                        mime='text/csv',
                    )
                except Exception as e:
                    st.error(f"Error executing query: {e}")
            else:
                st.warning("Please enter a SQL query to run.")

    # Footer
    st.markdown("---")
    st.markdown("""
    **Housing Affordability Time Machine** | Created with Streamlit

    Data sources: Federal Reserve Economic Data (FRED) - Median Home Price (MSPUS), 
    Median Household Income (MEHOINUSA646N), Consumer Price Index (CPIAUCSL)
    """)
# This section is now handled in the load_data function

if __name__ == "__main__":
    # This allows the app to be run with `streamlit run app.py`
    pass