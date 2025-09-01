import os
import time
import pathlib
from typing import Optional
from dotenv import load_dotenv
from langchain_core.tools import tool
import requests

# Output directory (override with DATA_DIR env var)
DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _safe_filename(stem: Optional[str]) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = "".join(c for c in (stem or "vision") if c.isalnum() or c in ("-", "_")) or "vision"
    return f"{base}-{ts}.png"

@tool
def generate_vision_image(
    prompt: str,
    size: str = "1024x1024",
    filename_stem: Optional[str] = None,
) -> str:
    """
    Generate a vision board image using Azure OpenAI DALL-E.

    Args:
        prompt: Text description of the vision to generate (required).
        size: Image size - one of "1024x1024", "1792x1024", or "1024x1792" (default "1024x1024").
        filename_stem: Optional base filename (timestamp appended).

    Returns:
        A formatted string with both the vision text and local image path.

    Example:
        generate_vision_image(
            prompt="A peaceful mountain landscape with a sunrise, representing personal growth and achievement"
        )
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt is required and cannot be empty.")
    
    # Validate size parameter
    valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
    if size not in valid_sizes:
        raise ValueError(f"Size must be one of {valid_sizes}")

    load_dotenv()
    
    # Get Azure OpenAI configuration
    api_key = os.getenv("AZURE_OPENAI_DALLE_API_KEY")
    # endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DALLE_DEPLOYMENT", "dall-e-3")
    # api_version = "2024-02-01"

    # Construct the Azure OpenAI DALL-E endpoint
    # url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment_name}/images/generations"
    url = os.getenv("AZURE_OPENAI_DALLE_ENDPOINT")
    if not api_key or not url:
        raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_DALLE_ENDPOINT must be set in environment variables")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    payload = {
        "prompt": prompt,
        "size": size,
        "n": 1,
        "quality": "standard"
    }
    
    try:
        # Call Azure OpenAI DALL-E API
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Azure OpenAI DALL-E API error {response.status_code}: {response.text}")
        
        result = response.json()
        image_url = result["data"][0]["url"]
        
        # Download the image and save locally
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code != 200:
            raise RuntimeError(f"Failed to download image: HTTP {img_response.status_code}")
        
        # Save the image locally
        local_path = DATA_DIR / _safe_filename(filename_stem)
        with open(local_path, "wb") as f:
            f.write(img_response.content)
        
        # Return formatted response with both vision text and image info
        return {
            "content": [f"Image generated for prompt: {prompt}", f"Saved at: {local_path}"],
            "image_path": str(local_path)
        }
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to generate vision image: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Error generating vision image: {e}") from e