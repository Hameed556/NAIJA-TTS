#!/bin/bash
# Setup script for Nigerian TTS API model files
set -e

echo "🚀 Setting up Nigerian TTS API models..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models
mkdir -p logs
mkdir -p temp

# Function to download file with progress
download_file() {
    local url=$1
    local output=$2
    local description=$3
    
    if [ ! -z "$url" ]; then
        echo -e "${YELLOW}📥 Downloading ${description}...${NC}"
        
        if command -v wget >/dev/null 2>&1; then
            wget --progress=bar:force:noscroll -O "$output" "$url"
        elif command -v curl >/dev/null 2>&1; then
            curl -L --progress-bar -o "$output" "$url"
        else
            echo -e "${RED}❌ Error: Neither wget nor curl is available${NC}"
            exit 1
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully downloaded ${description}${NC}"
        else
            echo -e "${RED}❌ Failed to download ${description}${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  No URL provided for ${description}${NC}"
    fi
}

# Function to verify file exists and has minimum size
verify_file() {
    local file=$1
    local min_size=$2
    local description=$3
    
    if [ -f "$file" ]; then
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [ "$size" -gt "$min_size" ]; then
            echo -e "${GREEN}✅ $description verified (${size} bytes)${NC}"
            return 0
        else
            echo -e "${RED}❌ $description too small (${size} bytes)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ $description not found${NC}"
        return 1
    fi
}

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Download model files if URLs are provided
if [ ! -z "$MODEL_CONFIG_URL" ]; then
    download_file "$MODEL_CONFIG_URL" "wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml" "config file"
else
    echo -e "${YELLOW}⚠️  MODEL_CONFIG_URL not set - skipping config download${NC}"
fi

if [ ! -z "$MODEL_CHECKPOINT_URL" ]; then
    download_file "$MODEL_CHECKPOINT_URL" "wavtokenizer_large_speech_320_24k.ckpt" "model checkpoint"
else
    echo -e "${YELLOW}⚠️  MODEL_CHECKPOINT_URL not set - skipping model download${NC}"
fi

# Verify files exist
echo "🔍 Verifying model files..."

config_file="wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml"
model_file="wavtokenizer_large_speech_320_24k.ckpt"

# Verify config file (minimum 1KB)
if [ -f "$config_file" ]; then
    verify_file "$config_file" 1024 "Config file"
else
    echo -e "${YELLOW}⚠️  Config file not found - may need manual download${NC}"
fi

# Verify model file (minimum 100MB for large model)
if [ -f "$model_file" ]; then
    verify_file "$model_file" 104857600 "Model checkpoint"
else
    echo -e "${YELLOW}⚠️  Model file not found - may need manual download${NC}"
fi

# Check Python dependencies
echo "🐍 Checking Python dependencies..."
if command -v python3 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Python3 found${NC}"
    
    # Check if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing Python dependencies..."
        python3 -m pip install -r requirements.txt
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to install dependencies${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
    fi
else
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# Test torch installation
echo "🔥 Testing PyTorch installation..."
python3 -c "import torch; print('PyTorch version:', torch.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PyTorch working correctly${NC}"
else
    echo -e "${RED}❌ PyTorch not working${NC}"
    exit 1
fi

# Create necessary directories in models folder
echo "📁 Creating model directory structure..."
mkdir -p models/wavtokenizer
mkdir -p models/yarngpt

# Move files to appropriate locations
if [ -f "$config_file" ]; then
    mv "$config_file" models/wavtokenizer/
    echo -e "${GREEN}✅ Config file moved to models/wavtokenizer/${NC}"
fi

if [ -f "$model_file" ]; then
    mv "$model_file" models/wavtokenizer/
    echo -e "${GREEN}✅ Model file moved to models/wavtokenizer/${NC}"
fi

# Set up git LFS for large files if needed
if command -v git >/dev/null 2>&1; then
    if [ -d ".git" ]; then
        echo "🗂️  Setting up Git LFS for large files..."
        git lfs track "*.ckpt" "*.bin" "*.pt" "*.pth" 2>/dev/null || echo "Git LFS not available"
    fi
fi

# Final verification
echo "🔍 Final verification..."
total_files=0
found_files=0

if [ -f "models/wavtokenizer/$config_file" ]; then
    echo -e "${GREEN}✅ Config file in place${NC}"
    found_files=$((found_files + 1))
fi
total_files=$((total_files + 1))

if [ -f "models/wavtokenizer/$model_file" ]; then
    echo -e "${GREEN}✅ Model file in place${NC}"
    found_files=$((found_files + 1))
fi
total_files=$((total_files + 1))

# Summary
echo ""
echo "="*50
echo "📊 Setup Summary:"
echo "Files found: $found_files/$total_files"

if [ $found_files -eq $total_files ]; then
    echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
    echo "You can now run the TTS API with: python3 main.py"
else
    echo -e "${YELLOW}⚠️  Setup completed with warnings${NC}"
    echo "Some files may need manual download"
fi

echo "="*50