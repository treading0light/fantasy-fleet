import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import random
import requests
import uuid
import mimetypes

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  
)

def init_guessing_game() -> dict:
    prompt = f"""You are the LLM in a text based guessing game. Always respond in JSON format without markdown syntax, JSON object only.
    Come up with a random word with substance to it (not 'the' or 'to') and put it as the value
    to the key: word; Come up with a single hint in case the user gets it wrong, specifically a bad hint as it shouldn't be too easy, and include it as the 
    value in the form of an array for the key: hints; Come up with a success message preferably related to the word or 
    use the word in the message, and include it as the value for the key: success_message"""

    try:
    
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "developer",
                    "content": prompt
                }
            ],
            model="gpt-4o"
        )

        json_str = completion.choices[0].message.content
        if "```json" in json_str:
            return json.loads(json_str.split("```json")[1].split("```")[0].strip())
        else:
            return json.loads(json_str)
    
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing JSON response: {e}")
        return {}
    

def next_hint(attempts: int, word: str, hints: list, prev_guess: str) -> str:
    hints_text = "\n".join(f"- {hint}" for hint in hints) if hints else "No hints given yet."

    prompt = f"""You are the LLM in a text based guessing game. The user has made {attempts} wrong
    guesses. 
    The word the user is trying to guess is: {word}
    The user just guessed: {prev_guess}
    Hints you've given so far: 
    {hints_text}

    Respond with a new hint as a plain string. Respond with the hint only."""

    completion = client.chat.completions.create(
            messages=[
                {
                    "role": "developer",
                    "content": prompt
                }
            ],
            model="gpt-4o"
        )
    
    return completion.choices[0].message.content

def cheeky_quit(attempts: int, word: str) -> str:
    prompt = f"""You are the LLM in a text based guessing game. The user has made {attempts} attempts at guessing
    and has just given up. The word was {word}. Respond in a {random_attitude()} manner and reveal the word."""

    completion = client.chat.completions.create(
            messages=[
                {
                    "role": "developer",
                    "content": prompt
                }
            ],
            model="gpt-4o"
        )
    
    return completion.choices[0].message.content


def random_attitude() -> str:
    choices = [
        "Encouraging and pleasant",
        "Mocking and cheeky",
        "Long-winded and misguided"
    ]

    weights = [
        0.4,
        0.4,
        0.2
    ]

    return random.choices(choices, weights=weights, k=1)[0]

def generate_image(prompt) -> str:
    try:
        response = client.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        )

    except Exception as error:

        if error.response: 
            print(error.response.status);
            print(error.response.data);
        else:
            print(error.message);
        
    
    print(response.data[0].url)
    return response.data[0].url

def download_image(url, save_dir="images"):
    os.makedirs(save_dir, exist_ok=True)
    unique_id = uuid.uuid4().hex

    res = requests.get(url, stream=True)
    if res.status_code == 200:
        content_type = res.headers.get("Content-Type", "")
        extension = mimetypes.guess_extension(content_type) or ".jpg"
        filename = f"{unique_id}{extension}"
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as file:
            for chunk in res.iter_content(1024):
                file.write(chunk)
        print("image downloaded and saved")
        return filepath
    else:
        print(f"Image failed to download. Status code: {res.status_code}")

def seed_assets():

    with open("asset-prompts.json", "r") as file:
        data = json.load(file)
    
        for asset in data:
            prompt = f"{asset["name"]}/n{asset["prompt"]}"
            url = generate_image(prompt)
            print(download_image(url))

if __name__ == "__main__":
    seed_assets()
