# Carvify

## Description
The **Carvify** tool is a Linux utility designed for forensic purposes. It helps recover files from disk images using file signature analysis. The tool supports creating raw disk images, listing available disks/partitions, scanning for files, and extracting specific files by their metadata address. The program is written in Python and utilizes `pytsk3` for enhanced disk image handling.

## Features
- List available disks and partitions.
- Create raw disk images from source disks or partitions.
- Scan disk images for files based on predefined signatures.
- List discovered files and allow selective file extraction.

## Requirements
- Python 3.6+
- Required Python libraries:
  - pytsk3
  - tqdm
  - logging

Refer to the `requirements.txt` file for detailed dependencies.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/pnasis/Carvify.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Carvify
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the tool:
   ```bash
   python carvify.py
   ```
2. Follow the menu options to:
   - List available disks/partitions.
   - Create a raw disk image.
   - Scan a disk image for files.
   - Extract specific files.

## File Signatures
The tool relies on a `signatures.json` file to identify file types. Ensure this file exists and is populated with the necessary file signatures in the following format:
```json
{
    "JPEG": {"header": "FFD8FF", "footer": "FFD9"},
    "PNG": {"header": "89504E47", "footer": "49454E44AE426082"}
    ...
}
```

## Example
1. List available disks/partitions:
   ```
   1. List Available Disks/Partitions
   ```
2. Create a disk image:
   ```
   Enter the source disk or partition (e.g., /dev/sda): /dev/sda
   Enter the output file name (e.g., disk_image): disk_image
   Enter the format (raw, qcow2, vmdk): raw
   ```
3. Scan the disk image for files:
   ```
   Enter the path to the disk image: disk_image.dd
   Files Found:
   1. example.jpg (Type: JPEG, Meta Address: 128)
   ```
4. Extract a specific file:
   ```
   Enter the meta address of the file to extract: 128
   Enter the filename for the extracted file: recovered.jpg
   Enter the output directory: ./recovered_files
   ```

## License
This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
