import json
from openai import OpenAI


def chatgpt(prompt, function_call_flag=1):
    question_parser = [
        {
            "name": "question_parser",
            "description": "Parse the given question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hq_representation": {
                        "type": "string",
                        "description": "Parsed representation of the given question",
                    }
                }
            }

        }
    ]
    title_extraction_function = [
        {
            "name": "title_extraction_function",
            "description": "Extract the title from the given phrase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Publication title in a question. Be sure to follow the examples given in the prompt",
                    }
                }
            }

        }
    ]
    sparql_generation_function = [
        {
            "name": "sparql_generation_function",
            "description": "Generate a SPARQL query for the given question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sparql": {
                        "type": "string",
                        "description": "SPARQL of a given question",
                    }
                }
            }

        }
    ]

    if function_call_flag == 2:
        function_call = title_extraction_function
    elif function_call_flag == 3:
        function_call = sparql_generation_function
    else:
        function_call = question_parser
    model = "gpt-3.5-turbo"
    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        functions=function_call,
        function_call='auto'
    )
    try:
        json_response = json.loads(completion.choices[0].message.function_call.arguments)
        return json_response
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""


if __name__ == "__main__":
    print("test")