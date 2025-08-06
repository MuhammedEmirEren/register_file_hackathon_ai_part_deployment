try:
    from process_image import process_image
    PROCESS_IMAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: process_image module not available: {e}")
    PROCESS_IMAGE_AVAILABLE = False

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import base64
from io import BytesIO
from PIL import Image
import uuid

try:
    from search_product import search_product
    SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: search_product module not available: {e}")
    SEARCH_AVAILABLE = False

try:
    from background_generator import BackgroundGenerator
    BACKGROUND_GEN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: background_generator module not available: {e}")
    BACKGROUND_GEN_AVAILABLE = False
from search_product import search_product

app = FastAPI()

# Add CORS middleware to allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active processors and uploaded images
processors = {}
uploaded_images = {}  # upload_id -> file_path mapping

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Register File AI API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class ImageEnhancementRequest(BaseModel):
    image_path: str
    background: str

class ImageSelectionRequest(BaseModel):
    image_path: str
    option_number: int

def pil_image_to_base64(pil_image):
    """Convert PIL Image to base64 string for JSON serialization"""
    if pil_image is None:
        return None
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    buffer = BytesIO()
    pil_image.save(buffer, format='JPEG', quality=95)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def apply_background(image: Image.Image, background: str) -> Image.Image:
    """Apply a given base64 background image to an RGBA image"""
    if image.mode != 'RGBA':
        image = image.convert("RGBA")

    try:
        # Decode the base64 background image
        background_data = base64.b64decode(background.split(",")[1])  # Remove the "data:image/...;base64," prefix
        background_image = Image.open(BytesIO(background_data))

        # Ensure the background image matches the size of the input image
        background_image = background_image.resize(image.size)

        # Paste the input image (with transparency) on top of the background
        combined_image = Image.new("RGB", image.size)
        combined_image.paste(background_image, (0, 0))
        combined_image.paste(image, (0, 0), mask=image.split()[3])  # Use alpha channel as mask

        return combined_image
    except Exception as e:
        raise ValueError(f"Error applying background: {str(e)}")

@app.post("/upload")
async def upload_image(image: UploadFile = File(...)):
    """Upload an image file and return base64 data"""
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read the uploaded file directly into memory
        image_data = await image.read()
        
        # Convert to PIL Image
        pil_image = Image.open(BytesIO(image_data))
        
        # Generate unique ID for this upload session
        upload_id = str(uuid.uuid4())
        
        # Store in memory for processing (optional local save for debugging)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(script_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save locally for processing
        file_extension = os.path.splitext(image.filename)[1] or '.jpg'
        local_filename = f"{upload_id}{file_extension}"
        local_file_path = os.path.join(upload_dir, local_filename)
        
        pil_image.save(local_file_path)
        
        # Convert to base64 for frontend
        image_base64 = pil_image_to_base64(pil_image)
        
        # Store the upload_id -> file_path mapping
        uploaded_images[upload_id] = local_file_path
        
        return {
            "upload_id": upload_id,
            "file_path": f"uploads/{local_filename}",  # Relative path for processing
            "filename": local_filename,
            "image_base64": image_base64,
            "image_url": f"/serve-image/{upload_id}",  # URL to serve the image
            "width": pil_image.width,
            "height": pil_image.height
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/serve-image/{upload_id}")
async def serve_image(upload_id: str):
    """Serve an uploaded image by its upload_id"""
    try:
        if upload_id not in uploaded_images:
            raise HTTPException(status_code=404, detail="Image not found")
        
        file_path = uploaded_images[upload_id]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file not found on disk")
        
        with Image.open(file_path) as img:
            img_base64 = pil_image_to_base64(img)
            return {"image_base64": img_base64, "upload_id": upload_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")

@app.post("/upload-base64")
async def upload_base64_image(request: dict):
    """Upload an image via base64 data"""
    try:
        if 'image_data' not in request:
            raise HTTPException(status_code=400, detail="image_data field is required")
        
        image_data = request['image_data']
        
        # Handle data URLs (remove data:image/...;base64, prefix if present)
        if image_data.startswith('data:image'):
            image_data = image_data.split(',', 1)[1]
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Convert to PIL Image
        pil_image = Image.open(BytesIO(image_bytes))
        
        # Generate unique ID
        upload_id = str(uuid.uuid4())
        
        # Save locally for processing
        script_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(script_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        local_filename = f"{upload_id}.jpg"
        local_file_path = os.path.join(upload_dir, local_filename)
        
        # Save as JPEG
        if pil_image.mode in ('RGBA', 'LA', 'P'):
            pil_image = pil_image.convert('RGB')
        pil_image.save(local_file_path, 'JPEG', quality=95)
        
        # Store the mapping
        uploaded_images[upload_id] = local_file_path
        
        # Convert back to base64 for response
        image_base64 = pil_image_to_base64(pil_image)
        
        return {
            "upload_id": upload_id,
            "file_path": f"uploads/{local_filename}",
            "filename": local_filename,
            "image_base64": image_base64,
            "image_url": f"/serve-image/{upload_id}",
            "width": pil_image.width,
            "height": pil_image.height
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing base64 image: {str(e)}")

@app.post("/enhance_and_return_all_options")
async def enhance_image(request: ImageEnhancementRequest):
    """Process image through all enhancement options"""
    try:
        if not PROCESS_IMAGE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Image processing module not available")
            
        print(f"Starting enhancement for image: {request.image_path}")
        background_color = request.background
        print(f"Using background color: {background_color}")
        # Create a new processor instance
        processor_id = str(uuid.uuid4())
        img_processor = process_image()
        
        # Check if the image path is absolute or relative
        if os.path.isabs(request.image_path):
            # If absolute path, convert to relative from the script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            relative_path = os.path.relpath(request.image_path, script_dir)
            image_path_to_use = relative_path
        else:
            # If relative path, use as is
            image_path_to_use = request.image_path
        
        print(f"Using image path: {image_path_to_use}")
        
        # Check if file exists before processing
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_path_to_use)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"Image file not found: {full_path}")
        
        # Process the image step by step with error handling
        print("Step 1: Processing image...")
        img_processor.process(image_path_to_use)
        
        img_processor.raw_image.save("processed_image.png")  # Save processed image for debugging
        
        print("Step 2: Detecting objects...")
        img_processor.detect_object()
        
        img_processor.cropped_image.save("detected_objects_image.png")  # Save detected objects image for debugging
        print(img_processor.detected_objects)
        
        print("Step 3: Removing background...")
        img_processor.remove_background()
        
        img_processor.no_background_image = apply_background(img_processor.no_background_image, background_color)
        
        img_processor.no_background_image.save("no_background_image.png")  # Save no background image for debugging
        
        print("Step 4: Enhancement option 1...")
        try:
            img_processor.enhance_image_option1()
            print("Enhancement option 1 completed")
        except Exception as e:
            print(f"Enhancement option 1 failed: {str(e)}")
            # Set a placeholder or skip this enhancement
            img_processor.enhanced_image_1 = img_processor.no_background_image
        
        print("Step 5: Enhancement option 2...")
        try:
            img_processor.enhance_image_option2()
            print("Enhancement option 2 completed")
        except Exception as e:
            print(f"Enhancement option 2 failed: {str(e)}")
            # Set a placeholder or skip this enhancement
            img_processor.enhanced_image_2 = img_processor.no_background_image
        
        print("Step 6: Enhancement option 3...")
        try:
            img_processor.enhance_image_option3()
            print("✓ Enhancement option 3 completed")
        except Exception as e:
            print(f"Enhancement option 3 failed: {str(e)}")
            # Set a placeholder or skip this enhancement
            img_processor.enhanced_image_3 = img_processor.no_background_image
        
        # Store the processor for later use
        processors[processor_id] = img_processor
        print(f"Enhancement completed successfully. Processor ID: {processor_id}")
        
        # Convert PIL images to base64 for JSON response
        return {
            "processor_id": processor_id,
            "enhanced_image_1": pil_image_to_base64(img_processor.enhanced_image_1),
            "enhanced_image_2": pil_image_to_base64(img_processor.enhanced_image_2),
            "enhanced_image_3": pil_image_to_base64(img_processor.enhanced_image_3),
            "original_image": pil_image_to_base64(img_processor.raw_image),
            "no_background_image": pil_image_to_base64(img_processor.no_background_image)
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error during enhancement: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error enhancing image: {str(e)}")

@app.post("/choose_image_and_generate_description")
async def choose_image_and_generate_description(
    processor_id: str,
    option_number: int
):
    """Choose an enhanced image option and generate description"""
    try:
        # Get the processor instance
        if processor_id not in processors:
            raise HTTPException(status_code=404, detail="Processor not found. Please enhance image first.")
        
        img_processor = processors[processor_id]
        
        # Choose the image
        img_processor.choose_image(option_number)
        
        # Generate description
        description = img_processor.generate_description()
        
        return {
            "chosen_image": pil_image_to_base64(img_processor.chosen_image),
            "description": description,
            "option_number": option_number
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating description: {str(e)}") 

@app.delete("/cleanup/{processor_id}")
async def cleanup_processor(processor_id: str):
    """Clean up processor instance to free memory"""
    if processor_id in processors:
        del processors[processor_id]
        return {"message": "Processor cleaned up successfully"}
    else:
        raise HTTPException(status_code=404, detail="Processor not found")

@app.get("/status")
async def status_check():
    """Status check endpoint with processor count"""
    return {"status": "healthy", "active_processors": len(processors)}

@app.get("/health")
async def health_check():
    """Health check endpoint for Hugging Face Spaces"""
    return {"status": "ok", "message": "API is running"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Image Enhancement API is running", "docs": "/docs"}

@app.post("/get_search_results")
async def get_search_results(query:str):
    """Get search results for a query"""
    try:
        if not SEARCH_AVAILABLE:
            raise HTTPException(status_code=503, detail="Search module not available")
            
        print(f"Searching for: {query}")
        searcher = search_product()
        results = searcher.search_products_google_cse(query, 5)
        
        print(f"Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"Result {i+1}: {result.get('title', 'No title')}")
            print(f"URL: {result.get('link', 'No URL')}")
        
        return {
            "results": results, 
        }
    except Exception as e:
        print(f"Error in search: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")
    
@app.post("/generate_background")
async def generate_background(promptFromUser: str):
    """Generate a background image using Google GenAI"""
    try:
        if not BACKGROUND_GEN_AVAILABLE:
            raise HTTPException(status_code=503, detail="Background generation module not available")
            
        background_gen = BackgroundGenerator()
        print("Generating background image...")
        result = background_gen.generate(prompt=promptFromUser)
        image_path = result.get("file_path")
        public_url = result.get("public_url")
        file_name = result.get("file_name")
        print("Background image generated successfully.")
        
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Generated background image not found")
        
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            encoded_image = pil_image_to_base64(img)
            if encoded_image is None:
                raise HTTPException(status_code=500, detail="Error converting image to base64")
            
            # Generate unique ID for serving this background
            bg_id = str(uuid.uuid4())
            uploaded_images[bg_id] = image_path  # Store for serving
            
            return {
                "image": encoded_image,
                "image_base64": encoded_image,  # For consistency
                "background_id": bg_id,
                "serve_url": f"/serve-image/{bg_id}",
                "file_name": file_name,
                "prompt": promptFromUser
            }
            
    except Exception as e:
        print(f"Error generating background: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating background: {str(e)}")

# Create Gradio interface for Hugging Face Spaces
import gradio as gr

def gradio_interface():
    """Simple Gradio interface to keep the space alive"""
    return """
    # AI Image Enhancement API
    
    This Hugging Face Space provides an AI-powered image enhancement API with the following endpoints:
    
    ## FastAPI Endpoints Available:
    
    - **POST /upload** - Upload an image file
    - **POST /enhance_and_return_all_options** - Process image through all enhancement options
    - **POST /choose_image_and_generate_description** - Choose enhanced image and generate description
    - **POST /get_search_results** - Get search results for a query
    - **POST /generate_background** - Generate background using AI
    - **GET /status** - Health check endpoint
    
    ## API Documentation:
    Access the interactive API documentation at: `/docs`
    
    ## Usage:
    The API is running on this Space and can be accessed programmatically.
    """

# Create Gradio app
iface = gr.Interface(
    fn=gradio_interface,
    inputs=[],
    outputs=gr.Markdown(),
    title="AI Image Enhancement API",
    description="FastAPI backend for AI-powered image enhancement and processing"
)

# Mount Gradio app with FastAPI
app = gr.mount_gradio_app(app, iface, path="/")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
