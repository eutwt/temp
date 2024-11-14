import requests
import pandas as pd

def fetch_demands(instance, username, password, sysparm_fields=None, sysparm_query='', sysparm_limit=1000):
    """
    Fetches demand records from a ServiceNow instance and returns them as a list of dictionaries.

    Parameters:
    - instance (str): The ServiceNow instance name (e.g., 'dev12345').
    - username (str): The username for authentication.
    - password (str): The password for authentication.
    - sysparm_fields (str): Comma-separated list of fields to retrieve. If None, all fields are retrieved.
    - sysparm_query (str): The query string to filter records.
    - sysparm_limit (int): The maximum number of records per request.

    Returns:
    - records (list): A list of dictionaries containing the demand records.
    """

    # Base URL for the ServiceNow Table API
    BASE_URL = f'https://{instance}.service-now.com/api/now/table/demand'

    # Headers for the HTTP request
    HEADERS = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Parameters to filter and limit the data
    PARAMS = {
        'sysparm_limit': sysparm_limit,  # Adjust the limit as needed
    }

    if sysparm_fields:
        PARAMS['sysparm_fields'] = sysparm_fields

    if sysparm_query:
        PARAMS['sysparm_query'] = sysparm_query

    # Pagination variables
    records = []
    offset = 0
    while True:
        PARAMS['sysparm_offset'] = offset
        response = requests.get(
            BASE_URL,
            auth=(username, password),
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
        offset += sysparm_limit
    return records

# Example usage
if __name__ == "__main__":
    # Replace these with your ServiceNow instance details
    INSTANCE = 'your_instance'  # e.g., 'dev12345'
    USERNAME = 'your_username'
    PASSWORD = 'your_password'

    # Define the fields you want to retrieve
    FIELDS = 'number,short_description,requested_by,due_date'

    # Define any query parameters
    QUERY = ''  # e.g., 'state=active^priority=1'

    # Fetch the demands data
    demands_data = fetch_demands(
        instance=INSTANCE,
        username=USERNAME,
        password=PASSWORD,
        sysparm_fields=FIELDS,
        sysparm_query=QUERY,
        sysparm_limit=1000
    )

    # Load data into a pandas DataFrame
    df = pd.DataFrame(demands_data)

    # Display the DataFrame
    print(df.head())


##########

import requests
import base64

username = 'your_username'
password = 'your_password'
url = 'https://now.wf.com/api/now/table/demand'

# Create Basic Auth header
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
headers = {
    'Authorization': f'Basic {encoded_credentials}',
    'Content-Type': 'application/json'
}

response = requests.get(url, headers=headers)
