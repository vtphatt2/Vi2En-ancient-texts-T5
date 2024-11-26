# Le Phat Minh
from sentence_transformers import SentenceTransformer
import torch
import json

with open('../provided_cleaned_dataset/CPN_vie.txt', 'r', encoding='utf-8') as f:
    vietnamese_lines = [line.strip() for line in f if line.strip()]

# Read English text
with open('../provided_cleaned_dataset/CPN_eng_1.txt', 'r', encoding='utf-8') as f:
    english_lines = [line.strip() for line in f if line.strip()]

# Load the pre-trained multilingual model
model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
# Encode Vietnamese sentences
vi_embeddings = model.encode(vietnamese_lines, convert_to_tensor=True)

# Encode English sentences
en_embeddings = model.encode(english_lines, convert_to_tensor=True)


# Compute cosine similarity matrix between Vietnamese and English embeddings
similarity_matrix = torch.matmul(vi_embeddings, en_embeddings.T)
aligned_pairs = []

# Set a similarity threshold
similarity_threshold = 0.5  # Adjust based on your data

# Find the index (x,y) with the negative value
idx = torch.where(similarity_matrix < 0)
# Print the pairs with negative values
remove = []
for i in range(len(idx[0])):
    # print the index of the pair
    # Store the index of the pair if x = y
    if idx[0][i].item() == idx[1][i].item():
        remove.append(idx[0][i].item())
        
# Remove the English element with the negative value, one by one, and then 
# recomputing the similarity matrix
for i in remove:
    # Remove the English element with the negative value
    english_lines.pop(i)
    # Encode English sentences
    en_embeddings = model.encode(english_lines, convert_to_tensor=True)
    # Compute cosine similarity matrix between Vietnamese and English embeddings
    similarity_matrix = torch.matmul(vi_embeddings, en_embeddings.T)
    # Find the index (x,y) with the negative value
    idx = torch.where(similarity_matrix < 0)
    # Print the pairs with negative values
    remove = []
    count = 0
    for i in range(len(idx[0])):
        # print the index of the pair
        # Store the index of the pair if x = y
        if idx[0][i].item() == idx[1][i].item():
            print(idx[0][i].item(), idx[1][i].item())
            count += 1
            remove.append(idx[0][i].item())
    if (count == 0):
        break

print(len(english_lines))
print(len(vietnamese_lines))

if (len(english_lines) == len(vietnamese_lines)):
    # Align Vietnamese and English sentences
    for i in range(len(vietnamese_lines)):
        pair = {
            "id": i,
            "vi": vietnamese_lines[i],
            "en": english_lines[i]
        }
        aligned_pairs.append(pair)
        
# Save to json, including the index (save as "id"), the Vietnamese sentence, and the English sentence

with open('../data/cpn_1.json', 'w', encoding='utf-8') as f:
    json.dump(aligned_pairs, f, ensure_ascii=False, indent=4)