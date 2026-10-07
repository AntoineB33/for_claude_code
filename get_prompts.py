import json
import os
from pathlib import Path


def extract_and_sort_prompts(project_dir, output_file):
    target_path = Path(project_dir)
    all_prompts = []

    # Check all files, looking specifically for jsonl data
    for filepath in target_path.rglob('*'):
        if not filepath.is_file():
            continue
            
        mtime = os.path.getmtime(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Read line by line for .jsonl format
                for line_idx, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        
                        # Fix for the AttributeError: Ensure data is a dictionary
                        if not isinstance(data, dict):
                            continue
                        
                        # Match the structure you provided: "type": "user" or "message.role": "user"
                        is_user = data.get('type') == 'user'
                        msg_obj = data.get('message', {})
                        
                        if is_user or msg_obj.get('role') == 'user':
                            content = msg_obj.get('content', '')
                            text_content = ""
                            
                            # Handle standard string content
                            if isinstance(content, str):
                                text_content = content
                            # Handle potential array formats just in case
                            elif isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict) and block.get('type') == 'text':
                                        text_content += block.get('text', '')
                            
                            if text_content.strip():
                                all_prompts.append({
                                    'text': text_content.strip(),
                                    'mtime': mtime,
                                    'index': line_idx # higher line index means recent in the file
                                })
                    except json.JSONDecodeError:
                        # Skip lines that aren't valid JSON
                        continue
                        
        except UnicodeDecodeError:
            # Skip binary or unreadable files
            continue

    # Sort from most recent to least recent
    # Highest mtime (newest file) first, then highest index (newest message at the bottom of the file) first
    all_prompts.sort(key=lambda x: (x['mtime'], x['index']), reverse=True)

    # Write the extracted prompts to the output text file
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, prompt in enumerate(all_prompts):
            f.write(f"========== PROMPT {i+1} ==========\n")
            f.write(prompt['text'])
            f.write("\n\n")

    print(f"Successfully extracted {len(all_prompts)} prompts to {output_file}")

if __name__ == "__main__":
    TARGET_DIR = r"C:\Users\antoi\.claude\projects\C--Users-antoi-Documents-Home-code-kotlin-OmniApp"
    OUTPUT_FILE = "extracted_prompts.txt"
    
    if os.path.exists(TARGET_DIR):
        extract_and_sort_prompts(TARGET_DIR, OUTPUT_FILE)
    else:
        print(f"Error: The directory {TARGET_DIR} does not exist.")