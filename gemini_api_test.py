import os
import google.generativeai as genai

# Configure API key (assuming it's set as an environment variable)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it before running this script.")
    exit()

genai.configure(api_key=api_key)


async def generate_text_with_gemini(prompt_text: str):
    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash")  # Changed model name
        response = await model.generate_content_async(prompt_text)
        print("Gemini Response:")
        print(response.text)
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")


async def main():
    simple_prompt = "Tell me a short, interesting fact about the ocean."
    await generate_text_with_gemini(simple_prompt)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
