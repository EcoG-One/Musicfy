import os
from openai import OpenAI
import json

base_url = "https://api.aimlapi.com/v1"

# Insert your AIML API Key in the quotation marks instead of my_key:
api_key = "fdc7e528621d4914bc32586ced14e752"

system_prompt = "You are an AI assistant who knows everything."
user_prompt = "Provide a list of 15 slow rock songs suitable for chilling"

api = OpenAI(api_key=api_key, base_url=base_url)


def main():
    completion = api.chat.completions.create(
        model="mistralai/Mistral-7B-Instruct-v0.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=256,
    )

    response = completion.choices[0].message.content
    print(response)
'''

    clean_response = response.split('= ')[1]
    very_clean_response = clean_response.replace("'", '"')
    playlist = json.loads(very_clean_response)
    titles = []
    for song in playlist:
        titles.append(song['track_name'])
        print(song['track_name'])
'''

if __name__ == main():
    main()