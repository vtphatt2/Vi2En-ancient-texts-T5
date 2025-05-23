import requests
from bs4 import BeautifulSoup
import json


def english_crawler(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        content_tag = soup.find('div', class_='my-4')
        english_trans = content_tag.find_all('p')

        eng_content = []
        for p in english_trans:
            text = p.string.strip() if p.string else ""
            if text:
                eng_content.append(text)
        return eng_content
    
    except Exception as e:
        print(f"Error: {e}")
        return None
        
def vietnamese_crawler(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        content_tag = soup.find('div', class_='poem-content')
        start_trans = content_tag.find('strong', string='Dịch nghĩa')
        h4_tag = start_trans.find_parent('h4')
        content = h4_tag.find_next_siblings('p')
        poem_lines = []
        for p in content:
            # Get text lines inside each <p>, splitting on <br> (or block-level breaks)
            lines = p.get_text(separator="\n", strip=True).split("\n")

            # Merge lines if the preceding line ends with a colon.
            merged = []
            for line in lines:
                line = line.strip()
                if merged and merged[-1].endswith(':'):
                    # Append this line to the previous line
                    merged[-1] += ' ' + line
                else:
                    merged.append(line)

            # Accumulate
            poem_lines.extend(merged)
        
        return poem_lines
                    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    
vietnamese_url = "https://www.thivien.net/%C4%90%E1%BB%97-Ph%E1%BB%A7/Xu%C3%A2n-t%C3%BAc-t%E1%BA%A3-t%E1%BB%89nh/poem-rrgfnxw48dEBDL0tvhjeWg"
english_url = "https://www.cn-poetry.com/dufu-poetry/office-spring-night.html"
file_name = "poem19.json"
vietnamese_poem = vietnamese_crawler(vietnamese_url)
english_poem = english_crawler(english_url)

with open("vietnamese_poem.txt", "w", encoding="utf-8") as f:
    for line in vietnamese_poem:
        f.write(line + "\n")
with open("english_poem.txt", "w", encoding="utf-8") as f:
    for line in english_poem:
        f.write(line + "\n")
        
if len(vietnamese_poem) != len(english_poem):
    print("The number of lines in the two poems don't match.")
else:
    data = []
    for i, (vi, en) in enumerate(zip(vietnamese_poem, english_poem)):
        data.append({
            "id": i,
            "vi": vi,
            "en": en
        })
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Exported to poem.json")

