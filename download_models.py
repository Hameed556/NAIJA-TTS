"""
Script to download model files during deployment
Use this if you're hosting model files externally
"""

import os
import requests
from pathlib import Path

# Add gdown import
try:
    import gdown
except ImportError:
    gdown = None
    print("gdown is not installed. Google Drive downloads will not work.")

def download_file(url, filename):
    """Download a file from URL or Google Drive"""
    if "drive.google.com" in url:
        if gdown is None:
            raise ImportError("gdown is required for Google Drive downloads. Please install it.")
        print(f"Downloading {filename} from Google Drive with gdown...")
        gdown.download(url, filename, quiet=False)
    else:
        print(f"Downloading {filename} from {url} with requests...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {filename} successfully!")

def main():
    """Download required model files"""
    # Get URLs from environment variables
    config_url = os.getenv("MODEL_CONFIG_URL")
    model_url = os.getenv("MODEL_CHECKPOINT_URL")
    if not config_url or not model_url:
        print("MODEL_CONFIG_URL and MODEL_CHECKPOINT_URL environment variables must be set")
        return False
    try:
        # Download config file
        download_file(
            config_url, 
            "wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml"
        )
        # Download model file
        download_file(
            model_url,
            "wavtokenizer_large_speech_320_24k.ckpt"
        )
        print("All model files downloaded successfully!")
        return True
    except Exception as e:
        print(f"Error downloading model files: {e}")
        return False

if __name__ == "__main__":
    main()