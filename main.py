import os
import re
import json
import subprocess
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Load file signatures
def load_signatures(file="signatures.json"):
    if not os.path.exists(file):
        raise FileNotFoundError(f"Signature file {file} not found.")
    with open(file, "r") as f:
        return json.load(f)

# Read disk image with progress tracking
def read_disk_image(file_path):
    file_size = os.path.getsize(file_path)
    chunk_size = 1024 * 1024  # 1 MB
    data = b""

    with open(file_path, "rb") as f, tqdm(total=file_size, unit="B", unit_scale=True, desc="Reading Disk Image") as pbar:
        while chunk := f.read(chunk_size):
            data += chunk
            pbar.update(len(chunk))
    return data

# Scan for signatures
def scan_for_signatures(data, header, footer):
    header_pattern = re.compile(header, re.DOTALL)
    results = []
    last_end = 0

    for match in header_pattern.finditer(data):
        start = match.start()
        if start < last_end:
            continue
        footer_match = data.find(bytes.fromhex(footer), start)
        if footer_match != -1:
            end = footer_match + len(bytes.fromhex(footer))
            results.append((start, end))
            last_end = end
        else:
            # Handle incomplete footer, default to 1MB recovery
            results.append((start, start + 1024 * 1024))
            last_end = start + 1024 * 1024
    return results

# Recover files
def recover_files(data, matches, output_dir, extension):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for i, (start, end) in enumerate(matches):
        recovered_data = data[start:end]
        filename = os.path.join(output_dir, f"file_{i + 1}{extension}")
        with open(filename, "wb") as f:
            f.write(recovered_data)
        if end - start < 1024:  # Example threshold for partial files
            logging.info(f"Recovered partial file: {filename}")

# Create disk image
def create_disk_image(source, output_file):
    """
    Create a raw disk image from the specified source.

    Args:
        source (str): The source disk or partition (e.g., /dev/sda).
        output_file (str): Path to save the created disk image.
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source device {source} not found.")

    try:
        # Use dd command to create a disk image
        with open(output_file, "wb") as dst, tqdm(unit="B", unit_scale=True, desc="Creating Disk Image") as pbar:
            result = subprocess.run(
                ["dd", f"if={source}", f"of={output_file}", "bs=1M"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Error creating disk image: {result.stderr}")
            pbar.update(os.path.getsize(output_file))
        print(f"Disk image created successfully: {output_file}")
    except Exception as e:
        print(f"Error creating disk image: {e}")

# Main function
def main():
    print("1. Create Disk Image")
    print("2. Scan and Recover Files")
    choice = input("Choose an option: ")

    if choice == "1":
        source = input("Enter the source disk or partition (e.g., /dev/sda): ")
        output_file = input("Enter the output file name (e.g., disk_image.dd): ")
        create_disk_image(source, output_file)
    elif choice == "2":
        # Existing scan and recovery process
        signatures = load_signatures()
        disk_image_path = input("Enter the path to the disk image: ")
        data = read_disk_image(disk_image_path)
        for filetype, info in signatures.items():
            print(f"Scanning for {filetype}...")
            matches = scan_for_signatures(data, bytes.fromhex(info["header"]), bytes.fromhex(info["footer"]))
            recover_files(data, matches, "output", info["extension"])
            print(f"Recovered {len(matches)} {filetype} files.")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
