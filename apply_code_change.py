import sys
import json
import re
import redis

def apply_change():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    instruction_json_str = r.get("instruction:json:learn_from_execution")
    
    if not instruction_json_str:
        print("Error: Instruction JSON not found in Redis.")
        sys.exit(1)

    print(f"Raw string from Redis: {instruction_json_str[:200]}...") # Print first 200 chars

    instruction = json.loads(instruction_json_str)

    file_path = instruction["file_path"]
    function_name = instruction["function_name"]
    new_body_content = instruction["new_body_content"]

    with open(file_path, 'r') as f:
        content = f.read()

    # Regex to find the function definition and its body
    # This regex is sensitive to indentation and assumes a standard Python function definition.
    # It captures the function definition line and the indented body.
    # It assumes the function body is indented by 4 spaces.
    pattern = r"(async\s+def\s+" + re.escape(function_name) + r"\s*\(self,.*?\):\s*\n)([\s\S]*?)(?=\n\s*\S|\Z)"

    match = re.search(pattern, content)

    if not match:
        print(f"Error: Function '{function_name}' not not found or pattern mismatch in {file_path}")
        sys.exit(1)

    def_line = match.group(1)
    old_body = match.group(2)

    # Determine the indentation of the function body
    # Find the first non-empty line in the old body to get its indentation
    body_lines = old_body.split('\n')
    indentation = ""
    for line in body_lines:
        if line.strip():
            indentation = line[:len(line) - len(line.lstrip())]
            break
    
    # Re-indent the new_body_content to match the function's indentation
    re_indented_new_body = ""
    for line in new_body_content.split('\n'):
        if line.strip(): # Only indent non-empty lines
            re_indented_new_body += indentation + line + '\n'
        else:
            re_indented_new_body += '\n' # Preserve empty lines

    # Replace the old body with the new, re-indented body
    new_content = content.replace(old_body, re_indented_new_body)

    with open(file_path, 'w') as f:
        f.write(new_content)

    print(f"Successfully updated function '{function_name}' in {file_path}")

if __name__ == "__main__":
    apply_change()