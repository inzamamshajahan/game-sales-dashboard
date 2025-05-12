# src/etl.py
import pandas as pd
import psycopg2
import os

# --- CHANGE 1: Remove the temporary/local os.getenv calls for DB params ---
# These lines are removed as the config is now imported:
# DB_HOST = os.getenv("DB_HOST_LOCAL", "localhost")
# DB_NAME = os.getenv("DB_NAME_LOCAL", "gamedb_local")
# DB_USER = os.getenv("DB_USER_LOCAL", "localuser")
# DB_PASSWORD = os.getenv("DB_PASSWORD_LOCAL", "localpass")
# DB_PORT = os.getenv("DB_PORT_LOCAL", "5432")

# --- CHANGE 2: Add import from config.py ---
from config import DATABASE_CONNECTION_PARAMS # Import the centralized dictionary

# Ensure the CSV file path is correct (using absolute path inside container)
CSV_FILE_PATH = '/app/data/game_sales_data.csv'

# --- CHANGE 3: Modify get_db_connection to use the imported params ---
def get_db_connection():
    """Establishes database connection using centralized configuration."""
    conn = None # Initialize conn to None
    try:
        # Use the imported dictionary with the splat operator (**)
        conn = psycopg2.connect(**DATABASE_CONNECTION_PARAMS)
        return conn
    except Exception as e:
        print(f"ETL Error: Database connection failed: {e}")
        # Depending on desired behavior, you might want to exit or raise the exception
        raise # Re-raise the exception to stop the ETL if connection fails

# (create_tables function remains the same, it just takes the connection object)
def create_tables(conn):
    """Creates the necessary database tables if they don't exist."""
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id SERIAL PRIMARY KEY,
                game_title VARCHAR(255) UNIQUE NOT NULL,
                genre VARCHAR(100),
                developer VARCHAR(150)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sales_records (
                sale_id SERIAL PRIMARY KEY,
                game_id INTEGER NOT NULL REFERENCES games(game_id),
                sale_date DATE NOT NULL,
                units_sold INTEGER NOT NULL,
                revenue DECIMAL(10, 2) NOT NULL,
                platform VARCHAR(50),
                region VARCHAR(50)
            );
        """)
        conn.commit()
        print("Tables checked/created successfully.")
    except Exception as e:
        conn.rollback() # Rollback any partial changes if table creation fails
        print(f"ETL Error: Failed to create tables: {e}")
        raise # Stop ETL if tables can't be created
    finally:
        cur.close()


def process_etl():
    """Main ETL process: connects, creates tables, reads CSV, loads data."""
    conn = None # Initialize conn
    try:
        conn = get_db_connection() # Get connection using refactored function
        create_tables(conn) # Ensure tables exist

        cur = conn.cursor()
        try:
            df = pd.read_csv(CSV_FILE_PATH)
            print(f"Loaded {len(df)} rows from {CSV_FILE_PATH}")

            # --- Optional: Clear existing sales data for a full reload (if desired) ---
            # print("Clearing existing sales_records data...")
            # cur.execute("TRUNCATE TABLE sales_records RESTART IDENTITY;") # Be careful with TRUNCATE!
            # print("Existing sales_records data cleared.")
            # ------------------------------------------------------------------------

            inserted_count = 0
            for index, row in df.iterrows():
                # Game handling (remains the same logic)
                cur.execute("SELECT game_id FROM games WHERE game_title = %s;", (row['game_title'],))
                game = cur.fetchone()
                if game:
                    game_id = game[0]
                else:
                    cur.execute(
                        "INSERT INTO games (game_title, genre, developer) VALUES (%s, %s, %s) RETURNING game_id;",
                        (row['game_title'], row['genre'], row['developer'])
                    )
                    game_id = cur.fetchone()[0]
                    print(f"Inserted new game: {row['game_title']} with ID: {game_id}")

                # Insert sales record (remains the same logic)
                cur.execute(
                    """
                    INSERT INTO sales_records (game_id, sale_date, units_sold, revenue, platform, region)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (game_id, row['sale_date'], row['units_sold'], row['revenue'], row['platform'], row['region'])
                )
                inserted_count += 1
            conn.commit() # Commit transaction after processing all rows
            print(f"Successfully processed and committed {inserted_count} sales records.")

        except FileNotFoundError:
            print(f"ETL Error: CSV file not found at {CSV_FILE_PATH}")
            # No rollback needed if file isn't found before DB interaction
        except Exception as e:
            print(f"ETL Error during data processing: {e}")
            conn.rollback() # Rollback transaction if error occurs during processing
        finally:
            if cur:
                cur.close() # Ensure cursor is closed

    except Exception as e:
        # Catch errors from get_db_connection or create_tables
        print(f"ETL Error: Failed to complete ETL process: {e}")
        # No need to close connection here if it failed in get_db_connection
    finally:
        if conn:
            conn.close() # Ensure connection is closed if it was opened
            print("ETL: Database connection closed.")

if __name__ == '__main__':
    print("Starting ETL process...")
    process_etl()
    print("ETL process finished.") # This might not print if an exception stops the script