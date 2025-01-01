from bs4 import BeautifulSoup
import requests

def thivien_crawler(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

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
            link = f"https://www.thivien.net/Khuyết-danh-Việt-Nam/" + title + "/" + id
            list_link.append(link)
        return list_link
    except Exception as e:
        print(f"Error: {e}")
        return None
    
url = "https://www.thivien.net/Khuy%e1%ba%bft-danh-Vi%e1%bb%87t-Nam/B%c3%adch-C%c3%a2u-k%e1%bb%b3-ng%e1%bb%99/group-VkIfi7DKP2f1cM8JZZP8yA"
list_link = thivien_crawler(url)
with open('The marvelous neuter.txt', 'w', encoding='utf-8') as f:
    for link in list_link:
        f.write(link + '\n')