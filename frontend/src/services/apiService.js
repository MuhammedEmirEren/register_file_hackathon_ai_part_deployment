// API service for communicating with FastAPI backend
// Update this URL to match your actual Hugging Face Space URL
const API_BASE_URL = 'https://muhammedemireren-glowii.hf.space';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.currentProcessorId = null;
  }

  async uploadImage(imageFile) {
    try {
      console.log('Uploading image:', imageFile.name, imageFile.type, imageFile.size);
      
      const formData = new FormData();
      formData.append('image', imageFile);

      console.log('Making request to:', `${this.baseURL}/upload`);

      const response = await fetch(`${this.baseURL}/upload`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header for FormData, let browser set it automatically
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const data = await response.json();
      console.log('Upload successful:', data);

      base64 = data.image_base64;

      // Save the image and return the path
      return base64;
      } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  }

  async enhanceImage(imageBase64, background = null) {
    try {
      const response = await fetch(`${this.baseURL}/enhance_and_return_all_options`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image_base64: imageBase64,
          background: background
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Store the processor ID for later use
      this.currentProcessorId = data.processor_id;
      
      return data;
    } catch (error) {
      console.error('Error enhancing image:', error);
      throw error;
    }
  }

  async chooseImageAndGenerateDescription(optionNumber) {
    try {
      if (!this.currentProcessorId) {
        throw new Error('No active processor. Please enhance an image first.');
      }

      const response = await fetch(`${this.baseURL}/choose_image_and_generate_description?processor_id=${this.currentProcessorId}&option_number=${optionNumber}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error generating description:', error);
      throw error;
    }
  }

  async cleanup() {
    try {
      if (!this.currentProcessorId) {
        return;
      }

      await fetch(`${this.baseURL}/cleanup/${this.currentProcessorId}`, {
        method: 'DELETE',
      });

      this.currentProcessorId = null;
    } catch (error) {
      console.error('Error cleaning up:', error);
      // Don't throw error for cleanup failures
    }
  }

  async healthCheck() {
    try {
      console.log('Testing health check with URL:', `${this.baseURL}/health`);
      const response = await fetch(`${this.baseURL}/health`);
      console.log('Health check response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Health check error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Health check successful:', data);
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  // Method to test if the space is accessible
  async testConnection() {
    try {
      console.log('Testing connection to:', this.baseURL);
      const response = await fetch(this.baseURL);
      console.log('Root endpoint response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Root endpoint response:', data);
        return { success: true, data };
      } else {
        const errorText = await response.text();
        console.error('Root endpoint error:', errorText);
        return { success: false, error: errorText, status: response.status };
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      return { success: false, error: error.message };
    }
  }

  async searchProduct(query) {
    try {
      const response = await fetch(`${this.baseURL}/get_search_results?query=${encodeURIComponent(query)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // Access the link inside the results object
      if (data.results && data.results[0].link) {
        console.log('Inside the if statement, data.results[0].link:');
        return data.results[0].link;
        
      }
      
      console.warn('Could not find results.link field in response');
      return null;
    } catch (error) {
      console.error('Error searching product:', error);
      throw error;
    }
  }

  async generateBackgroundImage(prompt) {
    try {
      const response = await fetch(`${this.baseURL}/generate_background?promptFromUser=${encodeURIComponent(prompt)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('API response data:', data); // Debug log
      
      return {
        image: data.image, // This is the base64 string
        image_base64: data.image_base64,
        fileName: data.file_name
      };
    } catch (error) {
      console.error('Error generating background image:', error);
      throw error;
    }
  }
}

export default new ApiService();
