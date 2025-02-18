import os
from openai import OpenAI

base_url = "https://api.aimlapi.com/v1"

# Insert your AIML API Key in the quotation marks instead of my_key:
api_key = "fdc7e528621d4914bc32586ced14e752"

system_prompt = "You are an AI assistant who knows everything."
user_prompt = "Create a work out EDM playlist for Spotify with at least 15 songs"

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

    print("User:", user_prompt)
    print("AI:", response)


if __name__ == main():
    main()