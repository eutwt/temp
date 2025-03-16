import duckdb
import pandas as pd
from datetime import date, timedelta
import random
import string

# Connect to an in-memory DuckDB database
con = duckdb.connect(database=':memory:')

# Generate the data directly in DuckDB using SQL
# This is more efficient than generating in Python first

# Set the number of rows
num_rows = 3000000

# Create a query that generates random data
query = f"""
CREATE TABLE random_data AS
SELECT 
    (DATE '2020-01-01' + INTERVAL (RANDOM() * 1095) DAY)::DATE AS date_col,
    chr(65 + RANDOM() * 26)::VARCHAR || 
    chr(65 + RANDOM() * 26)::VARCHAR || 
    chr(65 + RANDOM() * 26)::VARCHAR || 
    chr(65 + RANDOM() * 26)::VARCHAR || 
    chr(65 + RANDOM() * 26)::VARCHAR AS char_col,
    (RANDOM() * 1000)::DECIMAL(10,2) AS numeric_col
FROM range(1, {num_rows + 1});
"""

# Execute the query to create the table
con.execute(query)

# Verify the table was created with the correct number of rows
row_count = con.execute("SELECT COUNT(*) FROM random_data").fetchone()[0]
print(f"Generated {row_count} rows")

# Save the table as a parquet file
con.execute("COPY random_data TO 'random_data.parquet' (FORMAT PARQUET)")

print("Data saved to random_data.parquet")

# Optional: Show a sample of the data
print("\nSample data:")
print(con.execute("SELECT * FROM random_data LIMIT 5").fetchdf())

# Close the connection
con.close()
