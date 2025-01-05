import json
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('sentence-transformers/LaBSE')

with open("LVT_vie.txt", "r", encoding="utf-8") as f_vie:
    lines = [line.strip() for line in f_vie.readlines()]

with open("LVT_eng.txt", "r", encoding="utf-8") as f_eng:
    lines_eng = [line.strip() for line in f_eng.readlines()]

diff = len(lines) - len(lines_eng)

# 3. Encode all sentences
embeddings_vie = model.encode(lines)       # Shape: [V, d]
embeddings_eng = model.encode(lines_eng)   # Shape: [E, d]

# 4. Compute similarity matrix (PyTorch tensor), shape: [V, E]
similarity_matrix = util.cos_sim(embeddings_vie, embeddings_eng)

threshold = 0.55
lower_bound = 0.45
pairs_above_threshold = []
length = min(len(lines), len(lines_eng))
if diff > 0: # Vietnamese more than English
    j = 0
    while j < length:
        i = j - diff
        if i < 0:
            i = 0
        signal = False
        pairs_under_threshold = []
        while i < length and i < j + 2*diff:
            score = similarity_matrix[i, j].item()
            if score > threshold:
                signal = True
                pairs_above_threshold.append({
                    "vie_sentence": lines[i],
                    "eng_sentence": lines_eng[j],
                    "score": score
                })
                break
            else: 
                pairs_under_threshold.append({
                    "vie_sentence": lines[i],
                    "eng_sentence": lines_eng[j],
                    "score": score
                }) # Temporarily store pairs under threshold
            i += 1
        if not signal:
            max_score = max([pair["score"] for pair in pairs_under_threshold])
            if max_score > lower_bound:
                for pair in pairs_under_threshold:
                    if pair["score"] == max_score:
                        pairs_above_threshold.append(pair)
        j += 1

elif diff < 0:
    diff = abs(diff)
    i = 0
    while i < length:
        j = i - diff
        if j < 0:
            j = 0
        signal = False
        pairs_under_threshold = []
        while j < length and j < i + 2*diff:
            score = similarity_matrix[i, j].item()
            if score > threshold:
                signal = True
                pairs_above_threshold.append({
                    "vie_sentence": lines[i],
                    "eng_sentence": lines_eng[j],
                    "score": score
                })
                break
            else: 
                pairs_under_threshold.append({
                    "vie_sentence": lines[i],
                    "eng_sentence": lines_eng[j],
                    "score": score
                }) # Temporarily store pairs under threshold
            j += 1
        if not signal:
            max_score = max([pair["score"] for pair in pairs_under_threshold])
            for pair in pairs_under_threshold:
                if pair["score"] == max_score:
                    pairs_above_threshold.append(pair)
        i += 1

print(f"Original pairs above threshold: {len(pairs_above_threshold)}")
with open("pairs_above_threshold.json", "w", encoding="utf-8") as f:
    json.dump(pairs_above_threshold, f, ensure_ascii=False, indent=4)