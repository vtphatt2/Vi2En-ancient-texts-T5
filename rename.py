import os

def rename_li_bo_files():
    # Get all files in current directory and subdirectories
    for root, dirs, files in os.walk('.'):
        for filename in files:
            if 'Do_Fu' in filename:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, filename.replace('Do_Fu', 'Du_Fu'))
                
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} -> {new_path}")
                except Exception as e:
                    print(f"Error renaming {filename}: {e}")

if __name__ == "__main__":
    rename_li_bo_files()