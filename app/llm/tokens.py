import json
from transformers import AutoTokenizer
from numpy import argsort

TOKEN_LIMIT = 30000
TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))

def adjust_max_tokens_results(results:list,base:str):
    ntokens = count_tokens(base)
    i_scores = argsort([r['score'] for r in results],descending=True)
    print(f"highest score {results[i_scores[0]]['score']}")
    util,i = [],0
    coded = []
    while (ntokens<=TOKEN_LIMIT) & (i < i_scores.size):
        j = i_scores[i]
        txt = f"score={results[j]['score']}" + json.dumps(results[j]['title']+results[j]['content'], 
                         ensure_ascii=False,indent=2)
        ntokens += count_tokens(txt)
        coded.append(txt)
        util.append(results[j])
        i+=1
    print(f"\n[WEB SEARCH] {ntokens} tokens in info.")
    return util[::-1],coded[::-1]

