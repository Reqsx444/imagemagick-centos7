# Image Conversion Script Description - CentOS-like only
## Introduction
This script is designed to process images in a specified directory, allowing for changes in image quality and resolution. Additionally, the script verifies the integrity of images and generates appropriate logs regarding the operations performed. The script can be used with various options and flags, allowing customization to meet specific needs.

## Features
Package Verification and Installation: Checks if ImageMagick is installed and installs it if not available. \
Log Handling: Creates directories and log files, and clears them before each run of the script. \
Image Processing: Processes images in the specified directory according to provided parameters, such as quality, resolution, file creation year, and options for overwriting or adding a suffix to processed files. \
Image Verification: Checks the validity of formats and the integrity of images before processing. \
Result Logging: Generates logs regarding processed images and any errors encountered during processing.

## Usage
### Prerequisites :
- Python 3 \
- Libraries: os, time, shlex, imghdr, argparse, subprocess, importlib.util, PIL (Python Imaging Library) \
- ImageMagick

## Available Flags
-q, --quality (int): Target image quality (e.g., 85). \
-y, --year (int): Maximum file creation year (e.g., 2020). \
-r, --min_resolution_input (str): Target resolution in the format widthxheight (e.g., 1920x1080). \
-c, --replace (int): Override the source file (1=Yes, 0=No). Default is 1. \
-s, --suffix (str): Add a suffix to the converted image (e.g., _converted). \
-p, --path (str): Path to the directory with images. \
-d, --dryrun (int): Run in test mode (1=Yes, 0=No). Default is 0.
## Example Usage
python image_conversion.py -q 85 -y 2020 -r 1920x1080 -c 1 -p /path/to/directory
