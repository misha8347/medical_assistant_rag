import json
import requests
from tqdm import tqdm
import pandas as pd
import pyarrow.parquet as pq
from requests.exceptions import ConnectionError, Timeout, RequestException
import time

MAX_RETRIES = 5
TIMEOUT = 5  # seconds


def get_full_text(pmid):
    """
    Fetches the full text from the NCBI API for a given PubMed ID (PMID).
    Handles connection issues, retries on failures, and returns "no text" if unavailable.
    """
    url = f'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmid}/unicode'
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            
            # If server closed connection, wait and retry
            if response.status_code == 429:  # Too many requests
                wait_time = (2 ** attempt)  # Exponential backoff
                print(f"Rate limited. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            # Handle no results
            if 'No result can be found' in response.text or response.status_code != 200:
                return "no text"

            json_data = response.json()
            
            # Extract full text from passages
            full_text_pieces = []
            passages = json_data[0]["documents"][0]["passages"]

            for passage in passages:
                full_text_pieces.append(passage["text"])

            return " ".join(full_text_pieces)

        except (ConnectionError, Timeout) as e:
            wait_time = (2 ** attempt)  # Exponential backoff
            print(f"Connection error: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

        except RequestException as e:
            print(f"Request failed: {e}. Skipping PMID {pmid}")
            break  # Skip this PMID if an unexpected request error occurs

    return "no text"  # Return this if all retries fail


def main():
    with open('/s3/misha/data_dir/PMC_patients/PMC-Patients-V2.json', 'r') as f:
        df_patients_v2 = json.load(f)

    save_path = '/s3/misha/data_dir/PMC_patients/full_texts_PMC-Patients-V2.parquet'
    records = []
    for patient in tqdm(df_patients_v2):
        pmid = patient['PMID']
        patient_uid = patient['patient_uid']
        full_text = get_full_text(pmid)
        
        record = {
            'PMID': pmid,
            'patient_uid': patient_uid,
            'title': patient['title'],
            'full_text': full_text
        }
        records.append(record)

    df = pd.DataFrame(records)
    df.to_parquet(save_path, engine='pyarrow', compression='snappy')
    print('process finished!')

if __name__ == "__main__":
    main()