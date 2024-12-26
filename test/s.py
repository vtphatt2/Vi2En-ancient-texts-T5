import requests
from bs4 import BeautifulSoup
import csv

url = "https://www.cn-poetry.com/libai-poetry/hard-way-world-3.html?fbclid=IwZXh0bgNhZW0CMTEAAR0Q1nYyyaX1wPiaQzH0RPzD3A6_2g05G7MahDPhz9_Optzo1XmLbnRDrGs_aem_UcTz1TnOQngOxEZcezAW2w"

output_file = "crawled_data.csv"

try:
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, 'html.parser')

    content_tags = soup.find_all(['p'], string=True)

    with open(output_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)

        for idx, tag in enumerate(content_tags, start=1):
            text = tag.string.strip() if tag.string else "" 
            if text:
                writer.writerow([idx, text])

    print(f"Dữ liệu đã được lưu vào file {output_file}")
except Exception as e:
    print(f"Error: {e}")
