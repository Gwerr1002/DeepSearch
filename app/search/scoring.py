import re
from itertools import combinations


STOPWORDS = {
    "and", "or", "the", "of", "in", "on", "a", "an","with"
}

def keyword_based_score(search_terms : list, results:str):
    txt = results['title']+"\n"+results['content']
    txt = txt.lower()
    score_key = 0
    for terms in search_terms:
        pattern = r"\b(?:" + "|".join(re.escape(term) for term in terms) + r")\b"
        match = re.search(pattern, txt, re.IGNORECASE)
        if match:
            score_key+=1
    return score_key/len(search_terms)

