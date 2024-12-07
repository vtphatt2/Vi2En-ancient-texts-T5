from bs4 import BeautifulSoup
import requests

base_link = "https://nhasachmienphi.com/doc-online/so-do-"
id = 306431

def generate_links(base_link, id):
    link_list = []
    for i in range(1, 21):
        id += 1
        link_list.append(base_link + str(id))
    return link_list

def crawl_poem(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.text, "html.parser")
    content = soup.find(class_ = "chapter-content")
    find_p = content.find_all("p")
    sentence = []
    for p in find_p:
        sentence.append(p.text)
    return sentence

def trim_text(text):
    # Traverse backwards, find the string which has multiple ---------------- and remove that string and the sentence after it
    i = len(text) - 1
    while i >= 0:
        if text[i].count("—") >= 2:
            for j in range(i, len(text)):
                text.pop()
            break
        i -= 1
    return text

    
list_link = generate_links(base_link, id)
list_sentence = []
for link in list_link:
    sentence = crawl_poem(link)
    sentence = trim_text(sentence)
    for s in sentence:
        list_sentence.append(s)

with open("dumbluck_vietnamese.txt", "w", encoding="utf-8") as f:
    for s in list_sentence:
        f.write(s + "\n")