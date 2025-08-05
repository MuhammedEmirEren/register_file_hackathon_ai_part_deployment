import mimetypes
import os
import time
import uuid
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()

class BackgroundGenerator:
    def save_binary_file(self, file_name, data):
        f = open(file_name, "wb")
        f.write(data)
        f.close()
        print(f"File saved to to: {file_name}")


    def generate(self, prompt):
        client = genai.Client(
            api_key=os.getenv("SECRET_API_KEY"),
        )

        model = "gemini-2.0-flash-preview-image-generation"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",  
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE", 
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE", 
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",  
                ),
            ],
        )

        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())

        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)

                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(script_dir))  # Go up 2 levels from merged_models_and_api
                
                # Path to frontend public folder
                frontend_public = os.path.join(project_root, "frontend", "public")
                
                # Create the directory if it doesn't exist
                os.makedirs(frontend_public, exist_ok=True)
                
                unique_filename = f"background_{timestamp}_{unique_id[:8]}{file_extension}"
                output_path = os.path.join(frontend_public, unique_filename)

                self.save_binary_file(output_path, data_buffer)
                
                # Return both the full path and the public URL path
                public_url = f"/backgrounds/{unique_filename}"
                return {
                    'file_path': output_path,
                    'public_url': public_url,
                    'file_name': unique_filename
                }
            else:
                print(chunk.text)
