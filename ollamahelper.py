from ollama import chat
from dbhelper import get_description_by_title

async def get_response(prompt: str) -> str:
    # System and user messages
    messages = [
        {
            'role': 'system',
            'content': (
                'You are a helpful assistant that provides information about EONET events based on their titles. '
                'Use the provided tools to fetch detailed descriptions of events. '
                'Do not show the tool response directly — instead, frame your answer using it.'
            ),
        },
        {
            'role': 'user',
            'content': prompt,
        },
    ]

    # Call LLM with tools
    response = chat(
        model='llama3.2:latest',
        messages=messages,
        tools=[get_description_by_title],
    )

    tool_calls = response.get('message', {}).get('tool_calls', [])

    if tool_calls:
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            arguments = tool_call['function']['arguments']

            available_functions = {
                'get_description_by_title': get_description_by_title,
            }

            function_to_call = available_functions.get(function_name)

            if not function_to_call:
                return f"Function '{function_name}' not found."

            try:
                result = function_to_call(**arguments)

                # Append tool call + tool response to messages
                messages.append(response['message'])  # tool_call metadata
                messages.append({
                    'role': 'tool',
                    'name': function_name,
                    'content': result,
                })

            except Exception as e:
                return f"Error executing function '{function_name}': {str(e)}"

        # Second round: give model the tool output
        final_response = chat(
            model='llama3.2:latest',
            messages=messages,
        )

        return final_response.get('message', {}).get('content', "No final content returned.")

    # No tool call — return the model's first response directly
    return response.get('message', {}).get('content', "No content returned.")
