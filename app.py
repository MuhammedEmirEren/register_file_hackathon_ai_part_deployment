try:
    from process_image import process_image
    PROCESS_IMAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: process_image module not available: {e}")
    PROCESS_IMAGE_AVAILABLE = False

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import shutil
import os
import base64
from io import BytesIO
from PIL import Image
import uuid
import tempfile

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

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Headers: {request.headers}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response

app = FastAPI()

# Add Logging Middleware
app.add_middleware(LoggingMiddleware)

# Add CORS middleware to allow frontend to call the API
# Define allowed origins for CORS
origins = [
    "http://localhost",
    "http://localhost:3000", 
    "http://localhost:5173",  
    "https://register-file-hackathon-ai-part-dep.vercel.app",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active processors
processors = {}

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
        
        # Convert to base64 for frontend
        image_base64 = pil_image_to_base64(pil_image)
        
        # Generate unique ID for this upload session
        upload_id = str(uuid.uuid4())
        
        return {
            "upload_id": upload_id,
            "filename": image.filename,
            "image_base64": image_base64,
            "width": pil_image.width,
            "height": pil_image.height
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/enhance_and_return_all_options")
async def enhance_image(request: dict):
    """Process image through all enhancement options using base64 data"""
    try:
        if not PROCESS_IMAGE_AVAILABLE:
            raise HTTPException(status_code=503, detail="Image processing module not available")
        
        image_data = request.get("image_base64")
        background_color = request.get("background")

        if not image_data:
            raise HTTPException(status_code=400, detail="image_base64 field is required")

        # Decode base64 image
        if image_data.startswith('data:image'):
            image_data = image_data.split(',', 1)[1]
        
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Create a temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image:
            temp_image.write(image_bytes)
            temp_image_path = temp_image.name

        print(f"Starting enhancement for temporary image: {temp_image_path}")
        
        # Create a new processor instance
        processor_id = str(uuid.uuid4())
        img_processor = process_image()
        
        # Process the image step by step
        img_processor.process(temp_image_path)
        
        img_processor.raw_image.save("processed_image.png")  # Save processed image for debugging
        
        print("Step 2: Detecting objects...")
        img_processor.detect_object()
        
        img_processor.cropped_image.save("detected_objects_image.png")  # Save detected objects image for debugging
        print(img_processor.detected_objects)
        
        print("Step 3: Removing background...")
        img_processor.remove_background()
        
        if background_color:
            img_processor.no_background_image = apply_background(img_processor.no_background_image, background_color)
        
        img_processor.no_background_image.save("no_background_image.png")  # Save no background image for debugging
        
        print("Step 4: Enhancement option 1...")
        try:
            img_processor.enhance_image_option1()
            print("Enhancement option 1 completed")
        except Exception as e:
            print(f"Enhancement option 1 failed: {str(e)}")
            img_processor.enhanced_image_1 = img_processor.no_background_image
        
        print("Step 5: Enhancement option 2...")
        try:
            img_processor.enhance_image_option2()
            print("Enhancement option 2 completed")
        except Exception as e:
            print(f"Enhancement option 2 failed: {str(e)}")
            img_processor.enhanced_image_2 = img_processor.no_background_image
        
        print("Step 6: Enhancement option 3...")
        try:
            img_processor.enhance_image_option3()
            print("✓ Enhancement option 3 completed")
        except Exception as e:
            print(f"Enhancement option 3 failed: {str(e)}")
            img_processor.enhanced_image_3 = img_processor.no_background_image
        
        # Store the processor for later use
        processors[processor_id] = img_processor
        print(f"Enhancement completed successfully. Processor ID: {processor_id}")
        
        # Clean up the temporary file
        os.unlink(temp_image_path)
        
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
        raise
    except Exception as e:
        # Clean up temp file on error
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
        
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
            return {"image": encoded_image
                    , "public_url": public_url, "file_name": file_name
                    , "file_path": image_path}
            
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
