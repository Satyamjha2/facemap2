# Returns duplicates based on SSIM comparison. Working to improve detection with shutterstock watermark, very hit or miss.

import os
import cv2
import csv
import shutil
import time
from skimage.metrics import structural_similarity as ssim

# Constants for the folder path and settings
BASE_FOLDER_PATH = '/Volumes/OWC4/segment_images'
DEDUPE_FOLDER = 'dedupe_folder'
CLUSTER_FOLDER = os.path.join(BASE_FOLDER_PATH, DEDUPE_FOLDER)
FOLDER_LIST = [f for f in os.listdir(CLUSTER_FOLDER) if not f.startswith('.') and not f.endswith('.csv')]
print(FOLDER_LIST)
  # Base folder path change to your path

THRESHOLD = 0.9  # Similarity threshold to use for SSIM comparison
TARGET_SIZE = (128, 128)  # Size to temporarily resize images for comparison

def calculate_ssim(image1, image2):
    """Calculate the SSIM between two images."""
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)  # Convert photo 1 to grayscale
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)  # Convert photo 2 to grayscale
    score, _ = ssim(gray1, gray2, full=True)
    return score  # Return the SSIM score

def find_duplicates_with_ssim(folder_path, duplicate_output, csv_output, threshold=THRESHOLD, target_size=TARGET_SIZE):
    """Find duplicate images using SSIM and copy them for review."""
    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('jpg')]
    duplicates = []
    processed_images = {}  # Dict for processed images 

    os.makedirs(duplicate_output, exist_ok=True)  # Create folder for duplicates

    print(f"Processing {len(image_files)} images...")  # Show number of total images to process

    for i, image_path in enumerate(image_files):
        try:
            img1 = processed_images.get(image_path)  # Get image1 processed to grayscale
            if img1 is None:
                img1 = cv2.imread(image_path)
                img1 = cv2.resize(img1, target_size)  # Resize temp for comparison
                processed_images[image_path] = img1  # Store resized image

            for j in range(i + 1, len(image_files)):
                img2_path = image_files[j]
                img2 = processed_images.get(img2_path)  # Get image2 (possible dupe) processed to grayscale

                if img2 is None:
                    img2 = cv2.imread(img2_path)
                    img2 = cv2.resize(img2, target_size)  # Resize temp for comparison
                    processed_images[img2_path] = img2  # Store resized duplicate

                similarity = calculate_ssim(img1, img2)

                if similarity > threshold:
                    duplicate_copy_path = os.path.join(duplicate_output, f"duplicate_{os.path.basename(img2_path)}")
                    shutil.copy(img2_path, duplicate_copy_path)  # Copy duplicate for review
                    duplicates.append((image_path, img2_path, similarity))
                    print(f"Found duplicate: {img2_path} (SSIM: {similarity:.2f})")  # SSIM score for testing

            print(f"Images left to process: {len(image_files) - i - 1}")  # Display remaining images

        except Exception as e:
            print(f"Error processing {image_path}: {e}")

    print(f"Total duplicates found: {len(duplicates)}")  # Print number of duplicates found

    # Write duplicates to a CSV file
    with open(csv_output, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Original Image', 'Duplicate Image', 'SSIM Score'])  # Write header
        writer.writerows(duplicates)  # Write duplicate full paths in CSV

    return duplicates

def organize_duplicates_from_csv(csv_output, folder_path):
    """Organize duplicates based on a CSV file by moving them into folders under their original."""
    if not os.path.exists(folder_path):
        print(f"Folder path does not exist: {folder_path}")
        return

    # Read the CSV file
    with open(csv_output, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            original_image = row['Original Image']
            duplicates = row['Duplicate Image'].split(', ')  # Split duplicates into a list
            
            # Create a subfolder for the original image
            original_name = os.path.splitext(os.path.basename(original_image))[0]
            subfolder_path = os.path.join(folder_path, f"{original_name}_duplicates")
            os.makedirs(subfolder_path, exist_ok=True)

            for duplicate in duplicates:
                duplicate = duplicate.strip()  # Remove surrounding whitespace
                if os.path.isfile(duplicate):  # Ensure the duplicate exists
                    duplicate_move_path = os.path.join(subfolder_path, os.path.basename(duplicate))
                    shutil.move(duplicate, duplicate_move_path)  # Move duplicate to the subfolder
                    print(f"Moved {duplicate} to {subfolder_path}")
                else:
                    print(f"Duplicate not found: {duplicate}")

for FOLDER in FOLDER_LIST:
    
    FOLDER_PATH = os.path.join(BASE_FOLDER_PATH, CLUSTER_FOLDER, FOLDER)  # Folder with original images change to your cluster folder
    base_name = os.path.basename(FOLDER_PATH)  # Get the base name of the folder

    # Create paths for duplicates and CSV output without timestamp
    DUPLICATE_OUTPUT = os.path.join(BASE_FOLDER_PATH, 'dupes', f"{base_name}_dupes")
    CSV_OUTPUT = os.path.join(BASE_FOLDER_PATH, 'csv', f"{base_name}.csv")  # Changed 'csvs' to 'csv'

    # Ensure base folders exist
    os.makedirs(os.path.join(BASE_FOLDER_PATH, 'dupes'), exist_ok=True)  # Create dupes folder if it doesn't exist
    os.makedirs(os.path.join(BASE_FOLDER_PATH, 'csv'), exist_ok=True)  # Changed 'csvs' to 'csv'

    print(FOLDER_PATH, DUPLICATE_OUTPUT, CSV_OUTPUT)

    # Find duplicates and create CSV
    duplicates = find_duplicates_with_ssim(FOLDER_PATH, DUPLICATE_OUTPUT, CSV_OUTPUT)

    # Organize duplicates into folders and move them directly above the possible original
    organize_duplicates_from_csv(CSV_OUTPUT, FOLDER_PATH)