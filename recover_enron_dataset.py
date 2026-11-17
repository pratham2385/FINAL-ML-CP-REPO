"""
recover_enron_dataset.py
Recovers the verified, correct Enron Spam dataset from the upstream repository release,
validates the schema and message uniqueness, and updates data/raw/enron_spam_data.csv.
"""

import os
import io
import zipfile
import requests
import pandas as pd

UPSTREAM_ZIP_URL = "https://raw.githubusercontent.com/MWiechmann/enron_spam_data/master/enron_spam_data.zip"
TARGET_CSV_PATH = "data/raw/enron_spam_data.csv"
BACKUP_CSV_PATH = "data/raw/enron_spam_data_corrupted_backup.csv"

def recover():
    # 1. Ensure backup exists
    if not os.path.exists(BACKUP_CSV_PATH):
        raise RuntimeError(f"Backup file {BACKUP_CSV_PATH} not found! Cannot proceed without safety backup.")

    print(f"Verified safety backup exists at: {BACKUP_CSV_PATH}")

    # 2. Download zip from upstream GitHub repository
    print(f"Downloading corrected Enron dataset from: {UPSTREAM_ZIP_URL}...")
    resp = requests.get(UPSTREAM_ZIP_URL, timeout=60)
    resp.raise_for_status()
    print(f"Download complete ({len(resp.content)} bytes received).")

    # 3. Read and inspect CSV from memory
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        csv_filename = z.namelist()[0]
        print(f"Extracting {csv_filename} from zip archive...")
        with z.open(csv_filename) as f:
            df = pd.read_csv(f)

    # 4. Rigorous validation checks
    print("\nValidating recovered dataset:")
    print(f"  Shape: {df.shape}")
    assert df.shape[0] == 33716, f"Expected 33,716 rows, got {df.shape[0]}"

    spam_count = (df['Spam/Ham'] == 'spam').sum()
    ham_count = (df['Spam/Ham'] == 'ham').sum()
    print(f"  Spam rows: {spam_count}")
    print(f"  Ham rows:  {ham_count}")
    assert spam_count == 17171, f"Expected 17,171 spam rows, got {spam_count}"
    assert ham_count == 16545, f"Expected 16,545 ham rows, got {ham_count}"

    spam_df = df[df['Spam/Ham'] == 'spam']
    unique_spam_subj = spam_df['Subject'].nunique()
    unique_spam_msg = spam_df['Message'].nunique()
    print(f"  Unique spam subjects: {unique_spam_subj}")
    print(f"  Unique spam messages: {unique_spam_msg}")
    assert unique_spam_subj > 10000, f"Expected >10,000 unique spam subjects, got {unique_spam_subj}"
    assert unique_spam_msg > 10000, f"Expected >10,000 unique spam messages, got {unique_spam_msg}"

    # 5. Write to target destination
    print(f"\nWriting verified dataset to {TARGET_CSV_PATH}...")
    df.to_csv(TARGET_CSV_PATH, index=False)
    print("Write complete!")

    # Verify file on disk
    file_size = os.path.getsize(TARGET_CSV_PATH)
    print(f"Target file size on disk: {file_size} bytes")
    print("SUCCESS: Enron Spam Dataset successfully restored and verified!")

if __name__ == '__main__':
    recover()
