import logging
from datetime import datetime
import boto3
import pandas as pd

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    datefmt='%Y-%m-%d %H:%M:%S',  # Date format
    filename='app.log',  # Log file name
    filemode='w'  # Write mode ('a' for append)
)

# Log to console instead of a file (useful for quick debugging)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Set handler level
formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add console handler to the root logger
logging.getLogger().addHandler(console_handler)

def get_service_quotas(region_name):
    start_time = datetime.now()
    logging.info(f"Working on region {region_name}")
    client = boto3.client('service-quotas', region_name=region_name)
    services = []
    quotas = []

    # Get the list of services
    logging.info(f"Getting service list for region {region_name}")
    paginator = client.get_paginator('list_services')
    for page in paginator.paginate():
        for service in page['Services']:
            service_code = service['ServiceCode']
            service_name = service['ServiceName']
            services.append((service_code, service_name))


    # Get quotas for each service
    for service_code, service_name in services:
        has_quotas = False
        paginator = client.get_paginator('list_service_quotas')
        for page in paginator.paginate(ServiceCode=service_code):
            for quota in page['Quotas']:
                quotas.append({
                    'Region': region_name,
                    'Service Name': service_name,
                    'Service Code': service_code,
                    'Quota Name': quota.get('QuotaName'),
                    'Quota Code': quota.get('QuotaCode'),
                    'Value': quota.get('Value'),
                    'Adjustable': quota.get('Adjustable'),
                    'Global Quota': quota.get('GlobalQuota')
                })
                has_quotas = True
                logging.info(f'{service_name} {quota["QuotaCode"]} got.')

        # If no quotas were found, append empty quota attributes
        if not has_quotas:
            quotas.append({
                'Region': region_name,
                'Service Name': service_name,
                'Service Code': service_code,
                'Quota Name': None,
                'Quota Code': None,
                'Value': None,
                'Adjustable': None,
                'Global Quota': None
            })
            logging.info(f'{service_name} has no applied quotas, leave it empty.')
    end_time = datetime.now()
    used_time = end_time - start_time
    logging.info(f'Region {region_name} has {used_time} seconds.')
    return quotas

if __name__ == '__main__':
    logging.info('Application started')

    # Fetch service quotas
    quota_data = []
    # for region in ['cn-north-1', 'cn-northwest-1']:
    for region in ['cn-north-1']:
        region_quotas = get_service_quotas(region_name=region)
        quota_data.append(region_quotas)

    # Convert to a DataFrame
    df = pd.DataFrame(quota_data)

    # Save to an Excel file
    excel_file = "aws_service_quotas.xlsx"
    df.to_excel(excel_file, index=False)

    print(f"Service quotas saved to {excel_file}")
