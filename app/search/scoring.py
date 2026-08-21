import re
from itertools import combinations


STOPWORDS = {
    "and", "or", "the", "of", "in", "on", "a", "an","with"
}

def keyword_based_score(keywords : list, results:str):
    txt = results['title']+"\n"+results['content']
    txt = txt.lower()
    scores = []
    for key in keywords:
        key = key.lower()
        words = key.split()
        score_key = 0
        total = 0
        for word in (set(words)-STOPWORDS):
            if re.search(rf"\b{re.escape(word)}\b", txt, re.IGNORECASE):
                score_key += 0.5
            total+=0.5
        #
        for i in range(len(words) - 1):
            pair = rf"\b{re.escape(words[i])}\s+{re.escape(words[i+1])}\b"
            if re.search(pair, txt, re.IGNORECASE):
                score_key += 1
            total+=1
        #
        scores.append(score_key/total)
    return sum(scores)/len(scores)

