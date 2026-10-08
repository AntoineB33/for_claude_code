import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def extract_and_sort_prompts(project_dir, output_txt, history_json):
    target_path = Path(project_dir)
    
    # 1. Load existing history to preserve old prompts (even if source files are deleted)
    history = {}
    if os.path.exists(history_json):
        try:
            with open(history_json, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load history file. Starting fresh. Error: {e}")

    # 2. Check all files, looking specifically for jsonl data
    for filepath in target_path.rglob('*'):
        if not filepath.is_file():
            continue
            
        mtime = os.path.getmtime(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_idx, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        data = json.loads(line)
                        if not isinstance(data, dict):
                            continue
                        
                        # Attempt to extract exact timestamp (common keys in Claude data)
                        raw_time = data.get('created_at') or data.get('updated_at') or data.get('timestamp')
                        if not raw_time:
                            msg_obj_time = data.get('message', {})
                            raw_time = msg_obj_time.get('created_at') or msg_obj_time.get('timestamp')
                            
                        msg_obj = data.get('message', {})
                        
                        is_nested_user = data.get('type') == 'user' or msg_obj.get('role') == 'user'
                        is_flat_user = data.get('role') == 'user'
                        
                        if is_nested_user or is_flat_user:
                            # --- NEW: Ignore automated background tasks and system-injected messages ---
                            if data.get('promptSource') == 'system' or data.get('turnOrigin') == 'task_notification':
                                continue
                            
                            if is_flat_user:
                                content = data.get('content', '')
                            else:
                                content = msg_obj.get('content', '')
                                
                            # Secondary fallback check: skip if it's clearly an XML system notification
                            if isinstance(content, str) and content.strip().startswith('<task-notification>'):
                                continue
                            # --------------------------------------------------------------------------

                            text_content = ""
                            
                            if isinstance(content, str):
                                text_content = content
                            elif isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict) and block.get('type') == 'text':
                                        text_content += block.get('text', '')
                            
                            text_content = text_content.strip()
                            
                            if text_content:
                                # Create a unique ID to prevent duplicates
                                # Use uuid if provided by Claude, else hash the text and time
                                item_id = data.get('uuid') or msg_obj.get('uuid')
                                if not item_id:
                                    hash_input = f"{text_content}_{raw_time}_{mtime}"
                                    item_id = hashlib.md5(hash_input.encode('utf-8')).hexdigest()
                                
                                # Add or update in history database
                                history[item_id] = {
                                    'text': text_content,
                                    'mtime': mtime,
                                    'index': line_idx,
                                    'time': raw_time
                                }
                    except json.JSONDecodeError:
                        continue
                        
        except UnicodeDecodeError:
            continue

    # 3. Convert history dictionary back to a list for sorting
    all_prompts = list(history.values())

    # Sort from most recent to least recent
    # ISO string dates sort naturally alphabetically. Fallback to mtime, then index
    def sort_key(x):
        time_str = str(x.get('time') or "")
        return (time_str, x['mtime'], x['index'])

    all_prompts.sort(key=sort_key, reverse=True)

    # 4. Save the updated history database so we remember them next time
    with open(history_json, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # 5. Write the extracted prompts to the human-readable text file
    with open(output_txt, 'w', encoding='utf-8') as f:
        for i, prompt in enumerate(all_prompts):
            time_display = prompt.get('time')
            
            # If no exact timestamp was in the JSON, fallback to formatting the file's modified time
            if not time_display:
                time_display = datetime.fromtimestamp(prompt['mtime'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') + " (File Modified)"
                
            f.write(f"========== PROMPT {i+1} | {time_display} ==========\n")
            f.write(prompt['text'])
            f.write("\n\n")

    print(f"Successfully tracked/extracted {len(all_prompts)} total prompts to {output_txt}")

if __name__ == "__main__":
    TARGET_DIR = r"C:\Users\antoi\.claude\projects\C--Users-antoi-Documents-Home-code-kotlin-OmniApp"
    OUTPUT_FILE = "extracted_prompts.txt"
    HISTORY_FILE = "prompts_history.json"
    
    if os.path.exists(TARGET_DIR):
        extract_and_sort_prompts(TARGET_DIR, OUTPUT_FILE, HISTORY_FILE)
    else:
        print(f"Error: The directory {TARGET_DIR} does not exist.")