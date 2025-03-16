import duckdb
import pandas as pd

# Connect to an in-memory DuckDB database
con = duckdb.connect(database=':memory:')

# Set the number of rows
num_rows = 3000000

# Create a query that generates random data
# Using list_element with a predefined list of characters instead of chr function
query = f"""
CREATE TABLE random_data AS
SELECT 
    (DATE '2020-01-01' + INTERVAL (RANDOM() * 1095) DAY)::DATE AS date_col,
    list_element(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], CAST(RANDOM() * 26 AS INTEGER)) || 
    list_element(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], CAST(RANDOM() * 26 AS INTEGER)) || 
    list_element(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], CAST(RANDOM() * 26 AS INTEGER)) || 
    list_element(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], CAST(RANDOM() * 26 AS INTEGER)) || 
    list_element(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'], CAST(RANDOM() * 26 AS INTEGER)) AS char_col,
    (RANDOM() * 1000)::DECIMAL(10,2) AS numeric_col
FROM range(1, {num_rows + 1});
"""

# Execute the query to create the table
con.execute(query)

# Verify the table was created with the correct number of rows
row_count = con.execute("SELECT COUNT(*) FROM random_data").fetchone()[0]
print(f"Generated {row_count} rows")

# Save the table as a CSV file
con.execute("COPY random_data TO 'random_data.csv' (FORMAT CSV, HEADER)")

print("Data saved to random_data.csv")

# Optional: Show a sample of the data
print("\nSample data:")
print(con.execute("SELECT * FROM random_data LIMIT 5").fetchdf())

# Close the connection
con.close()
