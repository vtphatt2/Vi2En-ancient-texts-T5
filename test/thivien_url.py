from bs4 import BeautifulSoup
import requests
from urllib.parse import unquote, urlparse

def thivien_crawler(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        parsed = urlparse(url)
        parts = parsed.path.split('/')
        author = unquote(parts[1])
        title = unquote(parts[2])
        soup = BeautifulSoup(response.text, 'html.parser')
        base_link = "https://www.thivien.net"
        
        content_tag = soup.find('div', class_='poem-group-list')
        items = content_tag.find_all('li')
        list_link = []
        for item in items:
            link = item.find('a')['href']
            title = item.find('a').string
            # Find the last slash in the URL
            last_slash = link.rfind('/')
            # Extract the poem ID
            id = link[last_slash + 1:]
            title = title.replace(' ', '-')
            link = base_link + "/" + author + "/" + title + "/" + id
            list_link.append(link)
        return list_link
    except Exception as e:
        print(f"Error: {e}")
        return None
    
url = "https://www.thivien.net/Khuy%E1%BA%BFt-danh-Vi%E1%BB%87t-Nam/L%E1%BB%A5c-s%C3%BAc-tranh-c%C3%B4ng/group-i0xhHtc-7a8QaZ6JcRDVHQ"
list_link = thivien_crawler(url)
with open('The quarrel of the six beasts.txt', 'w', encoding='utf-8') as f:
    for link in list_link:
        f.write(link + '\n')