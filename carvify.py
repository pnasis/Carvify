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
    ascii_art = Figlet(font="slant").renderText(program_name)
    print(ascii_art)
    print("\nCreated by: pnasis\nVersion: v1.0\n")

def load_signatures(file="signatures.json"):
    """
    Load file signatures for identifying specific file types.
    """
    if not os.path.exists(file):
        raise FileNotFoundError(f"Signature file {file} not found.")
    with open(file, "r") as f:
        return json.load(f)

def list_partitions():
    """
    List available disks and partitions using `lsblk`.
    """
    print("Available disks and partitions:")
    result = subprocess.run(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"], capture_output=True, text=True)
    print(result.stdout)

def read_disk_image(file_path):
    """
    Open a disk image and return its file system object.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Disk image {file_path} not found.")
    try:
        img = pytsk3.Img_Info(file_path)
        fs = pytsk3.FS_Info(img)
        return fs
    except Exception as e:
        raise RuntimeError(f"Error reading disk image: {e}")

def scan_for_files(fs, signatures):
    """
    Scan a file system for files matching known signatures.
    """
    files_found = []

    def process_entry(entry):
        if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
            try:
                file_name = entry.info.name.name.decode("utf-8")
                file_data = entry.read_random(0, entry.info.meta.size)

                for filetype, signature in signatures.items():
                    header = bytes.fromhex(signature["header"])
                    if file_data.startswith(header):
                        files_found.append((file_name, entry.info.meta.addr, filetype))
            except Exception:
                pass

    def walk_directory(directory):
        for entry in directory:
            if entry.info.name.name not in [b".", b".."]:
                if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                    try:
                        subdir = fs.open_dir(inode=entry.info.meta.addr)
                        walk_directory(subdir)
                    except Exception:
                        pass
                else:
                    process_entry(entry)

    root_dir = fs.open_dir("/")
    walk_directory(root_dir)
    return files_found

def extract_file(fs, meta_addr, output_dir, filename):
    """
    Extract a file from the file system using its meta address.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    try:
        file_obj = fs.open_meta(meta_addr=meta_addr)
        data = file_obj.read_random(0, file_obj.info.meta.size)
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "wb") as f:
            f.write(data)
        print(f"File extracted to {output_path}")
    except Exception as e:
        print(f"Error extracting file: {e}")

def create_disk_image(source, output_file, format):
    """
    Create a disk image in the specified format from the source.
    """
    if not os.path.exists(source):
        raise FileNotFoundError(f"Source device {source} not found.")
    try:
        if format == "raw":
            with open(output_file, "wb") as dst:
                subprocess.run(["dd", f"if={source}", f"of={output_file}.dd", "bs=1M"], check=True)
        elif format in ["qcow2", "vmdk"]:
            subprocess.run(["qemu-img", "convert", "-f", "raw", "-O", format, source, "{output_file}.{format}], check=True)
        else:
            raise ValueError("Unsupported format. Supported formats: raw, qcow2, vmdk.")
        print(f"Disk image created successfully: {output_file}")
    except Exception as e:
        print(f"Error creating disk image: {e}")

def main():
    display_ascii_art()
    while True:
        print("\n1. List Available Disks/Partitions")
        print("2. Create Disk Image")
        print("3. Scan Disk Image for Files")
        print("4. Extract Specific File")
        print("5. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            list_partitions()
        elif choice == "2":
            source = input("Enter the source disk or partition (e.g., /dev/sda): ")
            output_file = input("Enter the output file name (e.g., disk_image): ")
            format = input("Enter the format (raw, qcow2, vmdk): ")
            create_disk_image(source, f"{output_file}", format)
        elif choice == "3":
            disk_image_path = input("Enter the path to the disk image: ")
            signatures = load_signatures()
            fs = read_disk_image(disk_image_path)
            files_found = scan_for_files(fs, signatures)
            print("\nFiles Found:")
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
