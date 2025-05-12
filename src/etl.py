# src/etl.py
import pandas as pd
import psycopg2
import os
# from .config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT # Import from config.py later

# TEMPORARY: Hardcode for now, will move to config.py
DB_HOST = os.getenv("DB_HOST_LOCAL", "localhost") # 'localhost' for direct connection to exposed port, or 'db' if running ETL in compose linking to 'db' service
DB_NAME = os.getenv("DB_NAME_LOCAL", "gamedb_local")
DB_USER = os.getenv("DB_USER_LOCAL", "localuser")
DB_PASSWORD = os.getenv("DB_PASSWORD_LOCAL", "localpass")
DB_PORT = os.getenv("DB_PORT_LOCAL", "5432")

CSV_FILE_PATH = '/app/data/game_sales_data.csv'

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
    return conn

def create_tables(conn):
    cur = conn.cursor()
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
    cur.close()
    print("Tables checked/created successfully.")

def process_etl():
    conn = get_db_connection()
    create_tables(conn) # Ensure tables exist
    cur = conn.cursor()

    try:
        df = pd.read_csv(CSV_FILE_PATH)
        print(f"Loaded {len(df)} rows from {CSV_FILE_PATH}")

        for index, row in df.iterrows():
            # Game handling
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

            # Insert sales record
            cur.execute(
                """
                INSERT INTO sales_records (game_id, sale_date, units_sold, revenue, platform, region)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (game_id, row['sale_date'], row['units_sold'], row['revenue'], row['platform'], row['region'])
            )
        conn.commit()
        print(f"Successfully processed and loaded data for {len(df)} sales records.")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("Starting ETL process...")
    process_etl()
