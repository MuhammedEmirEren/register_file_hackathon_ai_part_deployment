---
title: AI Image Enhancement API
emoji: �️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🚀 Register File AI API

A comprehensive AI-powered image processing and product search API with both **FastAPI backend** and **Gradio interface**.

## ✨ Features

### 🖼️ Image Processing
- **Object Detection**: Automatically detect and crop products in images
- **Background Removal**: Remove backgrounds with AI precision
- **Image Enhancement**: Three different enhancement options
- **Custom Backgrounds**: Apply custom backgrounds to products
- **AI Description Generation**: Generate SEO-optimized product descriptions

### 🔍 Product Search
- **Google Custom Search**: Find similar products across the web
- **Multi-platform Results**: Get results from various e-commerce platforms

### 🎨 Background Generation
- **AI Background Creation**: Generate custom backgrounds using text prompts
- **Multiple Styles**: Support for different background styles and colors

## 🚀 Quick Start

### Using the Gradio Interface
1. Visit the space URL
2. Upload your product image
3. Choose enhancement options
4. Generate descriptions
5. Search for similar products

### Using the API Directly

The FastAPI server provides REST endpoints for programmatic access:

```bash
# Health check
curl https://your-space-url.hf.space/

# Upload image
curl -X POST "https://your-space-url.hf.space/upload" \
  -F "image=@your_image.jpg"

# Enhance image with all options
curl -X POST "https://your-space-url.hf.space/enhance_and_return_all_options" \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "uploads/your_image.jpg",
    "background": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAcFFhtgAAAABJRU5ErkJggg=="
  }'

# Generate description
curl -X POST "https://your-space-url.hf.space/choose_image_and_generate_description" \
  -H "Content-Type: application/json" \
  -d '{
    "processor_id": "your_processor_id",
    "option_number": 1
  }'

# Search products
curl -X POST "https://your-space-url.hf.space/get_search_results" \
  -H "Content-Type: application/json" \
  -d '"laptop computer"'

# Generate background
curl -X POST "https://your-space-url.hf.space/generate_background" \
  -H "Content-Type: application/json" \
  -d '"modern office background with soft lighting"'
```

## 📡 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and API info |
| `GET` | `/health` | Service health status |
| `GET` | `/status` | Detailed status with active processors |

### Image Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload image file |
| `POST` | `/enhance_and_return_all_options` | Process image with all enhancement options |
| `POST` | `/choose_image_and_generate_description` | Generate AI description for selected image |
| `DELETE` | `/cleanup/{processor_id}` | Clean up processor to free memory |

### Utility Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/get_search_results` | Search for similar products |
| `POST` | `/generate_background` | Generate custom backgrounds |

## 🔧 Environment Variables

To use all features, set these environment variables:

```bash
SECRET_API_KEY=your_google_gemini_api_key
GOOGLE_CSE_ID=your_google_custom_search_engine_id
GOOGLE_API_KEY=your_google_api_key
```

## 💡 Usage Examples

### Python Client Example

```python
import requests
import base64
from PIL import Image

# Base URL for your Hugging Face Space
BASE_URL = "https://your-space-url.hf.space"

# Upload image
with open("product.jpg", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload", files={"image": f})
    upload_result = response.json()

# Enhance image
enhance_request = {
    "image_path": upload_result["file_path"],
    "background": "data:image/png;base64,white_background_base64"
}
response = requests.post(f"{BASE_URL}/enhance_and_return_all_options", json=enhance_request)
enhancement_result = response.json()

# Generate description
desc_request = {
    "processor_id": enhancement_result["processor_id"],
    "option_number": 1
}
response = requests.post(f"{BASE_URL}/choose_image_and_generate_description", json=desc_request)
description = response.json()

print("Generated Description:", description["description"])
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const BASE_URL = 'https://your-space-url.hf.space';

async function processImage() {
    // Upload image
    const form = new FormData();
    form.append('image', fs.createReadStream('product.jpg'));
    
    const uploadResponse = await axios.post(`${BASE_URL}/upload`, form, {
        headers: form.getHeaders()
    });
    
    // Enhance image
    const enhanceResponse = await axios.post(`${BASE_URL}/enhance_and_return_all_options`, {
        image_path: uploadResponse.data.file_path,
        background: "data:image/png;base64,white_background_base64"
    });
    
    console.log('Enhancement completed:', enhanceResponse.data.processor_id);
}

processImage();
```

## 🛠️ Technical Details

### Architecture
- **Backend**: FastAPI with async support
- **Frontend**: Gradio interface for easy interaction
- **AI Models**: 
  - OwlViT for object detection
  - REMBG for background removal
  - Google Gemini for description generation
  - Various enhancement algorithms

### Performance
- Optimized for CPU inference
- Background processing for long-running tasks
- Memory management with processor cleanup
- Efficient image handling with PIL/OpenCV

## 📄 License

MIT License - feel free to use in your projects!

## 🤝 Contributing

This project is part of a hackathon submission. Feel free to fork and improve!

## 🐛 Issues

If you encounter any issues, please check:
1. Image formats (JPG, PNG supported)
2. API key configuration
3. Network connectivity for external services

For bug reports, please include:
- Error messages
- Input image details
- Expected vs actual behavior
