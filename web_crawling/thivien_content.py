import requests
from bs4 import BeautifulSoup
import os
from glob import glob

def vietnamese_crawler(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the poem's content container
        content_tag = soup.find('div', class_='poem-content')
        if not content_tag:
            return []

        # Find the first <p> inside the container
        content = content_tag.find('p')
        if not content:
            return []

        # 1. Remove all <b> tags and their text
        for b_tag in content.find_all('b'):
            b_tag.decompose()

        # 2. Replace <br> tags with newlines
        for br_tag in content.find_all('br'):
            br_tag.replace_with('\n')

        # 3. Extract the text
        raw_text = content.get_text()

        # 4. Split by newlines, strip whitespace, and ignore empty lines
        poem_lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

        return poem_lines

    except (requests.RequestException, AttributeError) as e:
        print(f"Error: {e}")
        return []
                    
    except Exception as e:
        print(f"Error: {e}")
        return None
def export_poem(poem_lines, file_name):
    with open(file_name, 'w', encoding='utf-8') as f:
        for line in poem_lines:
            f.write(line + '\n')
def file_concatenate(file_name, output_file):
    files = glob(file_name)
    files.sort()
    with open(output_file, 'w', encoding='utf-8') as f:
        for file in files:
            with open(file, 'r', encoding='utf-8') as poem_file:
                f.write(poem_file.read())
                f.write('\n')    
def main(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        links = f.readlines()
        for id, link in enumerate(links):
            poem_lines = vietnamese_crawler(link.strip())
            if poem_lines:
                export_poem(poem_lines, file_name + str(id) + '.txt')
if __name__ == "__main__":
    file_name = "The constant mouse" # Specify the file name
    glob_output = file_name + "*.txt"
    # main(file_name + ".txt")
    file_concatenate(glob_output, file_name + ".txt")     
            