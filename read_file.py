import json
import os

def read_and_print_json(file_path):
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: The file '{file_path}' does not exist.")
            return

        # Check if the file is a valid JSON file (optional)
        if not file_path.endswith('.json'):
            print(f"Warning: The file '{file_path}' does not have a .json extension.")

        # Open and read the JSON file
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                # Pretty-print the JSON data
                print(json.dumps(data, indent=4))
            except json.JSONDecodeError as e:
                print(f"Error: The file '{file_path}' contains invalid JSON. Details: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while reading the JSON file: {e}")

    except PermissionError:
        print(f"Error: Permission denied when trying to read the file '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
read_and_print_json('conversations.json')