# Deployment Guide

## Overview

This guide covers deploying the Nigerian TTS API to various platforms, with a focus on Railway deployment.

## Prerequisites

- Git repository with the complete codebase
- Model files (1.75GB) hosted externally or stored with Git LFS
- Docker (for local testing)
- Railway account (for Railway deployment)

## Railway Deployment (Recommended)

### Step 1: Prepare Model Files

Since the model files are large (1.75GB), you have several options:

#### Option A: External Storage (Recommended)
Upload your model files to cloud storage and use direct URLs:

1. **Google Drive**:
   - Upload `wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml`
   - Upload `wavtokenizer_large_speech_320_24k.ckpt`
   - Get shareable direct download links
   - Convert to direct download format:
     ```
     https://drive.google.com/file/d/FILE_ID/view?usp=sharing
     becomes:
     https://drive.google.com/uc?export=download&id=FILE_ID
     ```

2. **AWS S3**:
   ```bash
   aws s3 cp wavtokenizer_*.yaml s3://your-bucket/models/
   aws s3 cp wavtokenizer_*.ckpt s3://your-bucket/models/
   aws s3 presign s3://your-bucket/models/config.yaml --expires-in 604800
   ```

3. **Dropbox**:
   - Upload files to Dropbox
   - Get direct download links
   - Replace `?dl=0` with `?dl=1` in URLs

#### Option B: Git LFS
```bash
# Initialize Git LFS
git lfs install

# Track large files
git lfs track "*.ckpt"
git lfs track "*.yaml"

# Add .gitattributes
git add .gitattributes

# Add model files
git add wavtokenizer_*.ckpt wavtokenizer_*.yaml
git commit -m "Add model files with LFS"
git push origin main
```

### Step 2: Repository Setup

1. **Create GitHub Repository**:
   ```bash
   git clone https://github.com/yourusername/nigerian-tts-api.git
   cd nigerian-tts-api
   ```

2. **Add All Files** from the complete structure provided

3. **Update requirements.txt** if needed:
   ```txt
   fastapi==0.104.1
   uvicorn==0.24.0
   torch==2.1.0
   torchaudio==2.1.0
   transformers==4.35.0
   # Add your YarnGPT dependency here
   # Either: -e git+https://github.com/username/yarngpt.git#egg=yarngpt
   # Or include the source code in your repo
   ```

### Step 3: Railway Configuration

1. **Connect Repository**:
   - Go to [Railway.app](https://railway.app)
   - Click "Deploy from GitHub repo"
   - Select your repository

2. **Set Environment Variables**:
   ```env
   # Model file URLs (if using external storage)
   MODEL_CONFIG_URL=https://your-storage.com/config.yaml
   MODEL_CHECKPOINT_URL=https://your-storage.com/model.ckpt
   
   # Optional: Custom settings
   HOST=0.0.0.0
   # PORT is set automatically by Railway
   ```

3. **Configure Build Settings**:
   Railway will automatically detect the Dockerfile and build your app.

### Step 4: Deploy

1. **Trigger Deployment**:
   - Push to your main branch
   - Railway will automatically build and deploy
   - Monitor the build logs for any issues

2. **Verify Deployment**:
   ```bash
   # Check health endpoint
   curl https://your-app-name.railway.app/health
   
   # Test TTS endpoint
   curl -X POST https://your-app-name.railway.app/tts \
        -H "Content-Type: application/json" \
        -d '{"text":"Hello Nigeria","language":"english","voice":"idera"}'
   ```

## Alternative Deployment Options

### Docker (Local/VPS)

1. **Build Docker Image**:
   ```bash
   docker build -t nigerian-tts-api .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8000:8000 \
     -e MODEL_CONFIG_URL="https://your-storage.com/config.yaml" \
     -e MODEL_CHECKPOINT_URL="https://your-storage.com/model.ckpt" \
     nigerian-tts-api
   ```

### Heroku

1. **Install Heroku CLI** and login

2. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   ```

3. **Set Config Variables**:
   ```bash
   heroku config:set MODEL_CONFIG_URL="https://your-storage.com/config.yaml"
   heroku config:set MODEL_CHECKPOINT_URL="https://your-storage.com/model.ckpt"
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### Google Cloud Run

1. **Build and Push to Container Registry**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/nigerian-tts-api
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy --image gcr.io/PROJECT_ID/nigerian-tts-api \
     --platform managed \
     --set-env-vars MODEL_CONFIG_URL="https://your-storage.com/config.yaml",MODEL_CHECKPOINT_URL="https://your-storage.com/model.ckpt"
   ```

### AWS ECS/Fargate

1. **Push to ECR**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
   docker tag nigerian-tts-api:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/nigerian-tts-api:latest
   docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/nigerian-tts-api:latest
   ```

2. **Create ECS Service** with environment variables set

## Environment Variables

### Required Variables
- `MODEL_CONFIG_URL`: URL to download the config YAML file
- `MODEL_CHECKPOINT_URL`: URL to download the model checkpoint file

### Optional Variables
- `PORT`: Server port (default: 8000, set automatically by most platforms)
- `HOST`: Server host (default: 0.0.0.0)
- `CLEANUP_INTERVAL_HOURS`: Audio file cleanup interval (default: 1)

### YarnGPT Integration

You'll need to handle the YarnGPT dependency. Choose one option:

#### Option 1: Git Dependency
Add to `requirements.txt`:
```txt
-e git+https://github.com/saheedniyi02/YarnGPT.git#egg=yarngpt
```

#### Option 2: Include Source Code
1. Clone YarnGPT into your repository:
   ```bash
   git submodule add https://github.com/saheedniyi02/YarnGPT.git yarngpt
   ```

2. Update your imports in `main.py`:
   ```python
   from yarngpt.generate import YarnGPTModel  # Adjust path as needed
   ```

#### Option 3: pip install (if available)
```txt
yarngpt>=1.0.0
```

## Troubleshooting Deployment

### Common Issues

**1. Model Download Fails**
```
Error: Failed to download model from URL
```
- Verify URLs are accessible
- Check internet connectivity during build
- Ensure URLs provide direct file downloads (not HTML pages)

**2. Out of Memory Error**
```
Error: CUDA out of memory / RuntimeError: [enforce fail at alloc_cpu.cpp]
```
- Increase memory allocation (Railway: upgrade plan)
- Use CPU-only inference
- Reduce model size or batch size

**3. Build Timeout**
```
Error: Build exceeded maximum time limit
```
- Use external model storage instead of Git LFS
- Optimize Docker layers
- Pre-build and push Docker image

**4. YarnGPT Import Error**
```
ModuleNotFoundError: No module named 'yarngpt'
```
- Verify YarnGPT is properly included in requirements.txt
- Check if the module needs compilation
- Consider including source code directly

### Performance Optimization

**Memory Usage**:
```python
# In main.py, add memory management
import gc
import torch

# After model loading
if torch.cuda.is_available():
    torch.cuda.empty_cache()
gc.collect()
```

**Startup Time**:
```python
# Use background model loading
from threading import Thread

def load_models_background():
    global model_loaded
    # Load models here
    model_loaded = True

# Start loading in background
Thread(target=load_models_background).start()
```

**Docker Optimization**:
```dockerfile
# Multi-stage build to reduce image size
FROM python:3.10-slim as builder
# Install dependencies
RUN pip install --user -r requirements.txt

FROM python:3.10-slim
# Copy only necessary files
COPY --from=builder /root/.local /root/.local
```

## Monitoring and Logs

### Railway Logs
```bash
# View logs
railway logs

# Stream logs
railway logs --follow
```

### Health Monitoring
Set up monitoring for the `/health` endpoint:
```bash
# Simple health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" https://your-app.railway.app/health)
if [ $response -eq 200 ]; then
    echo "API is healthy"
else
    echo "API is down (HTTP $response)"
fi
```

## Security Considerations

1. **Environment Variables**: Never commit sensitive data to Git
2. **CORS Configuration**: Restrict origins in production
3. **Rate Limiting**: Implement to prevent abuse
4. **Input Validation**: Sanitize all user inputs
5. **HTTPS Only**: Ensure SSL/TLS in production

## Scaling

### Horizontal Scaling
- Use load balancers
- Implement stateless design
- Use external storage for audio files

### Vertical Scaling
- Increase memory/CPU allocation
- Use faster storage (SSD)
- Optimize model loading

### Caching
- Implement Redis for audio caching
- Use CDN for static audio files
- Cache model outputs

This deployment guide should help you successfully deploy your Nigerian TTS API to Railway or any other platform. Choose the method that best fits your infrastructure and requirements.