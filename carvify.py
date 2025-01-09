import os
import re
import json
import subprocess
import pytsk3
import logging
from tqdm import tqdm
from pyfiglet import Figlet


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def display_ascii_art():
    program_name = "Carvify"
    ascii_art = Figlet(font='slant').renderText(program_name)
    print(ascii_art)

    # Display credits
    credits = "\nCreated by: pnasis\nVersion: v1.0\n"
    print(credits)

# Load file signatures
def load_signatures(file="signatures.json"):
    if not os.path.exists(file):
        raise FileNotFoundError(f"Signature file {file} not found.")
    with open(file, "r") as f:
        return json.load(f)

# List available disks/partitions
def list_partitions():
    print("Available disks and partitions:")
    result = subprocess.run(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"], capture_output=True, text=True)
    print(result.stdout)

# Read disk image using pytsk3
def read_disk_image(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Disk image {file_path} not found.")
    try:
        img = pytsk3.Img_Info(file_path)
        fs = pytsk3.FS_Info(img)
        return fs
    except Exception as e:
        raise RuntimeError(f"Error reading disk image: {e}")

# Scan for files in the disk image
def scan_for_files(fs, signatures):
    files_found = []

    def callback(file):
        for filetype, info in signatures.items():
            if file.info.meta and file.info.meta.size > 0:
                try:
                    data = file.read_random(0, file.info.meta.size)
                    if data.startswith(bytes.fromhex(info["header"])):
                        files_found.append((file.info.name.name.decode("utf-8"), file.info.meta.addr, filetype))
                except Exception:
                    pass

    for dirpath in fs.open_dir("/"):
        for entry in dirpath:
            if entry.info.name.name.decode("utf-8") not in [".", ".."]:
                callback(entry)

    return files_found

# Extract specific file by address
def extract_file(fs, meta_addr, output_dir, filename):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_obj = fs.open_meta(meta_addr=meta_addr)
    data = file_obj.read_random(0, file_obj.info.meta.size)
    output_path = os.path.join(output_dir, filename)
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"File extracted to {output_path}")

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
    display_ascii_art()
    while True:
        print("1. List Available Disks/Partitions")
        print("2. Create Disk Image")
        print("3. Scan Disk Image for Files")
        print("4. Extract Specific File")
        print("5. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            list_partitions()
        elif choice == "2":
            source = input("Enter the source disk or partition (e.g., /dev/sda): ")
            output_file = input("Enter the output file name (e.g., disk_image.dd): ")
            create_disk_image(source, output_file)
        elif choice == "3":
            disk_image_path = input("Enter the path to the disk image: ")
            signatures = load_signatures()
            fs = read_disk_image(disk_image_path)
            files_found = scan_for_files(fs, signatures)
            print("Files Found:")
            for i, (name, meta_addr, filetype) in enumerate(files_found, 1):
                print(f"{i}. {name} (Type: {filetype}, Meta Address: {meta_addr})")
        elif choice == "4":
            disk_image_path = input("Enter the path to the disk image: ")
            fs = read_disk_image(disk_image_path)
            meta_addr = int(input("Enter the meta address of the file to extract: "))
            filename = input("Enter the filename for the extracted file: ")
            output_dir = input("Enter the output directory: ")
            extract_file(fs, meta_addr, output_dir, filename)
        elif choice == "5":
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
