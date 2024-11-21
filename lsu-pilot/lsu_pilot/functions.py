from cairosvg import svg2png
import requests
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

functions = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather forecast for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state/country, e.g. 'London, UK' or 'New York, NY'"
                    },
                    "days": {
                        "type": "integer", 
                        "description": "Number of days to forecast (1-7)",
                        "minimum": 1,
                        "maximum": 7
                    }
                },
                "required": ["location"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "svg_to_png_bytes",
            "description": "Generate a PNG from an SVG",
            "parameters": {
                "type": "object",
                "properties": {
                    "svg_string": {
                        "type":
                        "string",
                        "description":
                        "A fully formed SVG element in the form of a string",
                    },
                },
                "required": ["svg_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "python_math_execution",
            "description": "Solve a math problem using python code",
            "parameters": {
                "type": "object",
                "properties": {
                    "math_string": {
                        "type":
                        "string",
                        "description":
                        "A string that solves a math problem that conforms with python syntax that could be passed directly to an eval() function",
                    },
                },
                "required": ["math_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an image using DALL-E based on a text prompt and it will return the url of the image",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text prompt to generate the image as required by the user"
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]


def get_weather(location, days=1):
    """Get weather prediction for a location and number of days."""
    try:
        # Build the API URL with the location and days parameters
        base_url = "http://api.weatherapi.com/v1/forecast.json"
        api_key = os.getenv("WEATHER_API_KEY")
        
        params = {
            "key": api_key,
            "q": location,
            "days": days,
            "aqi": "no"
        }
        
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        # Parse and return the JSON response
        return response.json()
        
    except requests.RequestException as e:
        return f"Error fetching weather data: {str(e)}"



def svg_to_png_bytes(svg_string):
  # Convert SVG string to PNG bytes
  png_bytes = svg2png(bytestring=svg_string.encode('utf-8'))
  return png_bytes


def python_math_execution(math_string):
  try:
    answer = eval(math_string)
    if answer:
      return str(answer)
  except:
    return 'invalid code generated'

def generate_image(prompt):
    try:
        print(f"Attempting to generate image with prompt: {prompt}")
        response = openai.images.generate(prompt=prompt,
                                        model="dall-e-3",
                                        n=1,
                                        size="1024x1024")
        image_url = response.data[0].url
        print(f"Successfully generated image. URL: {image_url}")
        return image_url
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return f"Failed to generate image: {str(e)}"

def run_function(name_of_function: str, args: dict):
     
    list_of_functions = {
        "svg_to_png_bytes": svg_to_png_bytes,
        "python_math_execution": python_math_execution,
        "get_weather": get_weather,
        "generate_image": generate_image,
        # future functions go here
    }
    
    func = list_of_functions.get(name_of_function)

    if func:
        return func(**args)
    else:
        return None