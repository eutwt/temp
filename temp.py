import requests
import pandas as pd

# Replace these with your ServiceNow instance details
INSTANCE = 'your_instance'  # e.g., 'dev12345'
USERNAME = 'your_username'
PASSWORD = 'your_password'

# Base URL for the ServiceNow Table API
BASE_URL = f'https://{INSTANCE}.service-now.com/api/now/table/demand'

# Headers for the HTTP request
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Parameters to filter and limit the data
PARAMS = {
    'sysparm_fields': 'number,short_description,requested_by,due_date',  # Specify the fields you need
    'sysparm_limit': '1000',  # Adjust the limit as needed
    'sysparm_query': '',  # Add any query parameters if required
}

# Function to fetch data with pagination support
def fetch_demands():
    records = []
    offset = 0
    limit = 1000  # Maximum number of records per request
    while True:
        PARAMS['sysparm_offset'] = offset
        response = requests.get(
            BASE_URL,
            auth=(USERNAME, PASSWORD),
            headers=HEADERS,
            params=PARAMS
        )
        if response.status_code != 200:
            print('Error:', response.status_code, response.reason)
            break

        data = response.json()
        result = data.get('result', [])
        if not result:
            break  # No more records
        records.extend(result)
        offset += limit
    return records

# Fetch the demands data
demands_data = fetch_demands()

# Load data into a pandas DataFrame
df = pd.DataFrame(demands_data)

# Display the DataFrame
print(df.head())
