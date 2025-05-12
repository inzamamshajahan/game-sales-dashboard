# src/dashboard.py
import streamlit as st
import pandas as pd
import psycopg2
import os

# --- CHANGE 1: Remove the temporary/local os.getenv calls for DB params ---
# These lines are removed as the config is now imported:
# DB_HOST = os.getenv("DB_HOST_LOCAL", "db")
# DB_NAME = os.getenv("DB_NAME_LOCAL", "gamedb_local")
# DB_USER = os.getenv("DB_USER_LOCAL", "localuser")
# DB_PASSWORD = os.getenv("DB_PASSWORD_LOCAL", "localpass")
# DB_PORT = os.getenv("DB_PORT_LOCAL", "5432")

# --- CHANGE 2: Ensure the import from config.py is present ---
# (Adjust path if config.py is located differently, e.g., from ..config if in subfolder)
from config import DATABASE_CONNECTION_PARAMS, APP_ENV # Import the centralized dictionary and APP_ENV

# --- CHANGE 3: Modify get_db_connection to use the imported params ---
def get_db_connection():
    """Establishes database connection using centralized configuration."""
    try:
        # Use the imported dictionary with the splat operator (**)
        conn = psycopg2.connect(**DATABASE_CONNECTION_PARAMS)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}") # Log error
        st.error(f"Database connection error: {e}") # Show error in Streamlit UI
        return None # Return None if connection fails

def fetch_sales_data(conn):
    """Fetches sales data joined with game details from the database."""
    # (Query remains the same)
    query = """
    SELECT
        sr.sale_id,
        sr.sale_date,
        g.game_title,
        g.genre,
        g.developer,
        sr.platform,
        sr.region,
        sr.units_sold,
        sr.revenue
    FROM sales_records sr
    JOIN games g ON sr.game_id = g.game_id
    ORDER BY sr.sale_date DESC;
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame() # Return empty dataframe on error

# --- Streamlit App ---
st.set_page_config(layout="wide")

# Use APP_ENV from config to show which environment we're viewing
st.title(f"🎮 Game Sales Dashboard ({APP_ENV.upper()} Environment)")

conn = get_db_connection() # Attempt connection

if conn: # Only proceed if connection was successful
    st.success("Database connection successful!")
    try:
        sales_df = fetch_sales_data(conn)

        if not sales_df.empty:
            st.subheader("Recent Sales Records")
            st.dataframe(sales_df)

            st.subheader("Total Revenue")
            total_revenue = sales_df['revenue'].sum()
            st.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")

            # Add more KPIs/Charts here later as needed
            # Example: Sales by Platform
            st.subheader("Revenue by Platform")
            platform_revenue = sales_df.groupby('platform')['revenue'].sum().sort_values(ascending=False)
            if not platform_revenue.empty:
                st.bar_chart(platform_revenue)
            else:
                st.write("No platform data available.")

        else:
            st.warning("No sales data found in the database.")

    except Exception as e:
        st.error(f"An error occurred during dashboard processing: {e}")
    finally:
        if conn:
            conn.close()
            print("Dashboard: Database connection closed.")
else:
    st.error("Failed to connect to the database. Please check logs or configuration.")