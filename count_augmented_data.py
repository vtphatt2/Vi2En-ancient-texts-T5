import os
import json

def count_augmented_lines(folder_dir: str):
    results = {}

    # Iterate through all JSON files in the folder
    for filename in os.listdir(folder_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Count number of entries in data
                    num_lines = len(data.get('data', []))
                    
                    # Store results
                    results[data.get('file_name', filename)] = num_lines
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Sort results by number of lines in descending order
    sorted_results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

    # Print results in a formatted way
    print("\nNumber of augmented lines per file:")
    print("-" * 50)
    for file_name, count in sorted_results.items():
        print(f"{file_name:<40} : {count:>6} lines")
    print("-" * 50)
    print(f"Total files: {len(results)}")
    print(f"Total augmented lines: {sum(results.values())}")

if __name__ == "__main__":
    # FOLDER_DIR = "augmented_data_ver01"
    # count_augmented_lines(FOLDER_DIR)
    count_augmented_lines("augmented_data_ver01")
    count_augmented_lines("augmented_data_ver02")