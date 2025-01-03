import re
RE_NUMBER = re.compile(r"^\d+\)")
RE_REMOVE_NUMBER = re.compile(r"\[\d+\]")

def remove_number(text):
    return RE_REMOVE_NUMBER.sub("", text)
def remove_index(text):
    return RE_NUMBER.sub("", text)

with open("Proclamation of Victory.txt", "r", encoding="utf-8") as f:
    en_lines = [line.strip() for line in f if line.strip()]

en_lines = [remove_number(line) for line in en_lines]
en_lines = [remove_index(line) for line in en_lines]

with open("Proclamation of Victory_cleaned.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(en_lines))