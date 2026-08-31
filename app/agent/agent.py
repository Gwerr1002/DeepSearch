from copy import copy
from numpy import asarray,argsort
from llm.ollama import chat
from agent.tools import (
    search_web,
    open_webpage,
    SEARCH_WEB_TOOL,
    OPEN_WEBPAGE_TOOL,
)
from search.web import is_block_content
from search.scoring import keyword_based_score
from llm.tokens import count_tokens,adjust_max_tokens_results,json
from config.config import task, cnf

class Workflow:
    def __init__(self):
        self.querys = list()
        self.total_web_history = set()
        self.relevant_sources = []
    #
    def run(self):
        self.analyze_task(task.research_task)
        info_insufficient = True
        i = 0
        while info_insufficient & (i<cnf.MAX_ITER):
            self.generate_query()
            restart = self.search()
            if restart:
                continue
            self.result_web_evaluator()
            info_insufficient = self.evaluator_info()
            i+=1
        final = self.open_relevant_sources()
        self.summary(final)
    #
    def analyze_task(self,task : str):
        print("\n[TASK ANALYZER] analysing task ...")
        task += """\nRemember: the traduction task MUST be grammatically 
            and orthographically correct in english."""
        print(f"\t{count_tokens(cnf.TASK_ANALYZER_PROMPT+task)} tokens")
        messages = [
            {
                "role": "system",
                "content": cnf.TASK_ANALYZER_PROMPT,
            },
            {
                "role": "user",
                "content": task,
            },
        ]
        response = chat(messages,format=cnf.TASK_ANALYZER_SCHEMA)
        content = response["message"]["content"]
        self.task_analysis = json.loads(content)
        print("\n[task ANALYZER] Analysis:")
        print(json.dumps(self.task_analysis, ensure_ascii=False,indent=2))
    #
    def generate_query(self):
        print("\n[QUERY GENERATOR] generating query ...")
        content = self.task_analysis
        content.pop("original_task", None)
        content.pop("language", None)
        content.pop("domain", None)
        content = "\ntask analysis:\n"+json.dumps(content, 
                                                  ensure_ascii=False,indent=2)
        content += "\nQueries:\n"+json.dumps([f'{i}: score = {q['score']} query: '+q['query'] 
                                              for i,q in enumerate(self.querys)], 
                                             ensure_ascii=False,indent=2)
        content += "\nSearch terminology (from most relevant to less relevant): " + json.dumps(task.search_terms)
        content += """\nRemember: If there are previous queries, you 
        MUST generate a different query. Query MUST contain letters and numbers. 
        Prioritize the most compact query possible and must relevant terminology."""
        print(f"\t{count_tokens(cnf.QUERY_GENERATOR_PROMPT+content)} tokens")
        messages = [
            {
                "role": "system",
                "content": cnf.QUERY_GENERATOR_PROMPT,
            },
            {
                "role": "user",
                "content": content,
            },
        ]
        response = chat(messages,format=cnf.QUERY_GENERATOR_SCHEMA)
        content = response["message"]["content"]
        new_query = json.loads(content)
        self.querys.append(new_query)
        print("\n[QUERY GENERATOR] query:")
        print(json.dumps(new_query,ensure_ascii=False,indent=2))
    #
    def search(self):
        print("\n[WEB SEARCH] searching ...")
        new_query = self.querys[-1]["query"]
        result = search_web(new_query)
        print(f"\n[WEB SEARCH] I founded {len(result)} results, cleaning ...")
        #
        self.search_results = []
        for r in result:
            url = r["url"]
            if url not in self.total_web_history:
                r['score'] = keyword_based_score(task.search_terms, r)
                self.search_results.append(r)
                self.total_web_history.add(url)
        # 
        print(f"\n[WEB SEARCH] {len(self.search_results)} new results were found.")
        if len(self.search_results) == 0:
            self.querys[-1]['score'] = 0
            return True
        else:
            return False
    #
    def result_web_evaluator(self):
        search_results,info,max_score = adjust_max_tokens_results(self.search_results,
                                                                                cnf.RESULT_WEB_EVALUATOR_PROMPT)
        self.search_results = search_results
        self.querys[-1]['score'] = max_score
        print("\n[WEB EVALUATOR] evaluating posible sources ...")
        prompt = cnf.RESULT_WEB_EVALUATOR_PROMPT.replace("[NSRC]",str(cnf.MAX_RELEVANT_SRC))
        content = "\ntask analysis:\n"+json.dumps(self.task_analysis['english_task'], ensure_ascii=False,indent=2)
        content += "\nPosible web sources:\n"+json.dumps([f'{i}: '+txt for i,txt in enumerate(info)], 
                                                         ensure_ascii=False,indent=2)
        content += """\nRemember: sources MUST have directly related with technical words of the task not
        only related with the topic. The source that have exactly all the technical words in the answer 
        ist the highest relevance. If there is no relevent source you can return empty list [] and 
        by default, you MUST select the source with the highest score. Select valid index"""
        print(f"{count_tokens(cnf.RESULT_WEB_EVALUATOR_PROMPT+content)} tokens")
        messages = [
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": content,
                    },
                ]
        format = copy(cnf.RESULT_WEB_EVALUATOR_SCHEMA)
        format['items']['properties']['index']['maximum'] = len(info)-1
        response = chat(messages,format=format)
        content = response["message"]["content"]
        relevant_sources = json.loads(content)
        #
        l = []
        for c in relevant_sources:
            relevant = self.search_results[int(c["index"])]
            relevant["relevance"] = c["relevance"]
            relevant["reason"] = c["reason"]
            l.append(relevant)
        print(f"\n[WEB EVALUATOR] I consider {len(l)} relevant sources")
        self.relevant_sources+=l
    #
    def evaluator_info(self):
        print("\n[EVIDENCE EVALUATOR] evaluting...")
        # sort scores terminology
        scoresk = asarray([r['score'] for r in self.relevant_sources])
        i_scores = argsort(scoresk)
        #
        content = json.dumps(['Title: '+self.relevant_sources[i]['title']+ 'content: ' + self.relevant_sources[i]['content'] 
                              for i in i_scores],
                             ensure_ascii=False,indent=2)
        content += '\nTask: ' + task.research_task
        content += '\nSearch terminology: ' + json.dumps(task.search_terms,
                                               ensure_ascii=False,indent=2)
        content += """\nRemember: You MUST prioritize evaluating the sources based on their ability 
        to answer each aspect of the task."""
        print(f"{count_tokens(cnf.EVIDENCE_EVALUATOR_PROMPT+content)} tokens")
        #
        messages = [
                            {
                                "role": "system",
                                "content": cnf.EVIDENCE_EVALUATOR_PROMPT,
                            },
                            {
                                "role": "user",
                                "content": content,
                            },
                        ]
        response = chat(messages,format=cnf.EVIDENCE_EVALUATOR_SCHEMA)
        evaluation = response["message"]["content"]
        evaluation = json.loads(evaluation)
        print(evaluation)
        n_scores = sum(scoresk>cnf.THRES_SCORE_TERMS)
        score_eval = 0.4*max(scoresk)
        score_eval += cnf.COVER[evaluation['coverage']]
        score_eval += cnf.EVIDENCE[evaluation['evidence']]
        score_eval += cnf.INFO[evaluation['information']]
        print(f"Evidence score: {score_eval}")
        print(n_scores)
        return (score_eval<cnf.THRES_SCORE_EVAL) | (n_scores < cnf.MIN_TERMS_SCORE_SRCS)
    #
    def open_relevant_sources(self):
        scoresk = asarray([r['score'] for r in self.relevant_sources])
        i_scores = argsort(scoresk)
        res = []
        n=0
        for k in range(i_scores.size-1,-1,-1):
            i = i_scores[k]
            r = self.relevant_sources[i]
            '''
            try:
                page = open_webpage(r['url'])
                if is_block_content(page):
                    status = 'block_content'
                else:
                    status = 'relevant'
            except Exception:
                page = ''
                status = 'denied_access'
            '''
            res.append({'web_info':r})
            n+=1
            if n+1 >= cnf.MAX_SRC:
                break
        return res
    #
    def summary(self,info:list):
        print("[SUMMARY] creating...")
        content = {}
        for i in range(len(info)-1,-1,-1):
            r = info[i]
            content[i] = copy(r)
        content = json.dumps(content,ensure_ascii=False,indent=2)
        content += "\n" + cnf.ANSWER_PROMPT_FINAL
        print(f'{count_tokens(cnf.ANSWER_PROMPT+content)} tokens')
        #
        messages = [
            {
                    "role": "system",
                    "content": cnf.ANSWER_PROMPT,
                },
                {
                    "role": "user",
                    "content": content,
            },
            ]
        response = chat(messages)
        with open(f"/app/results/"+self.querys[0]['query']+'.txt', 
                  "w", encoding="utf-8") as f:
            f.write(response["message"]["content"]+5*"\n"+json.dumps(info,ensure_ascii=False,indent=4))
        print(response["message"]["content"])