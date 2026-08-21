from copy import copy
from numpy import asarray
from llm.ollama import chat
from agent.tools import (
    search_web,
    open_webpage,
    SEARCH_WEB_TOOL,
    OPEN_WEBPAGE_TOOL,
)
from search.scoring import keyword_based_score
from llm.tokens import count_tokens,adjust_max_tokens_results,json
from config.config import task, cnf

class Workflow:
    def __init__(self):
        self.querys = list()
        self.total_web_history = set()
        self.relevant_info_hystory = []
    #
    def run(self):
        self.analyze_question(task.research_task)
        self.generate_query()
        '''
        info_insufficient = True
        i = 0
        while info_insufficient & (i<cnf.MAX_ITER):
            self.generate_query()
            coded = self.search()
            self.result_web_evaluator(coded)
            info_insufficient = self.evaluator_info()
            i+=1
        '''
    #
    def analyze_question(self,question : str):
        print("\n[QUESTION ANALYZER] analysing question ...")
        question += """\nRemember: the traduction task MUST be grammatically 
            and orthographically correct in english."""
        print(f"\t{count_tokens(cnf.TASK_ANALYZER_PROMPT+question)} tokens")
        messages = [
            {
                "role": "system",
                "content": cnf.TASK_ANALYZER_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ]
        response = chat(messages,format=cnf.TASK_ANALYZER_SCHEMA)
        content = response["message"]["content"]
        self.question_analysis = json.loads(content)
        print("\n[QUESTION ANALYZER] Analysis:")
        print(json.dumps(self.question_analysis, ensure_ascii=False,indent=2))
    #
    def generate_query(self):
        print("\n[QUERY GENERATOR] generating query ...")
        content = self.question_analysis.copy()
        content.pop("original_question", None)
        content.pop("language", None)
        content = "\nQuestion analysis:\n"+json.dumps(content, ensure_ascii=False,indent=2)
        content += "\nQueries:\n"+json.dumps(self.querys)
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
                r['score'] = keyword_based_score(self.question_analysis['keywords'],r)
                self.search_results.append(r)
                self.total_web_history.add(url)
        #
        self.search_results,coded = adjust_max_tokens_results(self.search_results,cnf.RESULT_WEB_EVALUATOR_PROMPT)
        print(f"\n[WEB SEARCH] {len(self.search_results)} new results were found.")
        return coded
    #
    def result_web_evaluator(self,info:list):
        print("\n[WEB EVALUATOR] evaluating posible sources ...")
        content = "\nQuestion analysis:\n"+json.dumps(self.question_analysis['english_question'], ensure_ascii=False,indent=2)
        content += "\nPosible web sources:\n"+json.dumps([f'{i}: '+txt for i,txt in enumerate(info)], 
                                                         ensure_ascii=False,indent=2)
        content += """\nRemember: sources MUST have directly related with technical words of the question not
        only related with the topic. The source that have exactly all the technical words in the answer 
        ist the highest relevance. If there is no relevent source you can return empty list [] and 
        by default, you MUST select the source with the highest score. Select valid index"""
        print(f"{count_tokens(cnf.RESULT_WEB_EVALUATOR_PROMPT+content)} tokens")
        messages = [
                    {
                        "role": "system",
                        "content": cnf.RESULT_WEB_EVALUATOR_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": content,
                    },
                ]
        response = chat(messages,format=cnf.RESULT_WEB_EVALUATOR_SCHEMA)
        content = response["message"]["content"]
        self.relevant_sources = json.loads(content)
        self.relevant_sources = [self.search_results[int(c["index"])] for c in self.relevant_sources]
        print(f"{json.dumps(self.relevant_sources)} \ntotal:{len(self.search_results)}")
        print(f"\n[WEB EVALUATOR] I consider {len(self.relevant_sources)} relevant sources")
        print(self.relevant_sources)
    #
    def evaluator_info(self):
        print("\n[EVIDENCE EVALUATOR] evaluting...")
        content = json.dumps(['Title'+r['title']+r['content'] for r in self.relevant_sources],
                             ensure_ascii=False,indent=2)
        content += '\nKeywords: ' + json.dumps(self.question_analysis['keywords'],
                                               ensure_ascii=False,indent=2)
        content += '\nSearch_terminology' + json.dumps(self.question_analysis['search_terminology'],
                                                       ensure_ascii=False,indent=2)
        content += """\nRemember: You MUST prioritize evaluating the sources based on their ability 
        to answer each aspect of the question."""
        print(f"{count_tokens(cnf.EVIDENCE_EVALUATOR_PROMPT+content)} tokens")
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
        scoresk = asarray([r['score'] for r in self.relevant_sources])
        n_scores = sum(scoresk>cnf.THRES_SCORE_KEYWORDS)
        score_eval = 0.4*max(scoresk)
        score_eval += self.COVER[evaluation['coverage']]
        score_eval += self.EVIDENCE[evaluation['evidence']]
        score_eval += self.INFO[evaluation['information']]
        print(f"score: {score_eval}")
        self.relevant_info_hystory += self.relevant_sources
        return (score_eval<cnf.THRES_SCORE_EVAL) | (n_scores > cnf.MIN_KEYWORDSCORE_SRCS)
    #
    def open_relevant_sources(self):
        for r in self.relevant_sources:
            source = self.search_results[int(r["index"])]
            try:
                result = open_webpage(source['url'])
                print(result)
                if len(result) >= 1000:
                    pass
                else:
                    pass
            except Exception as e:
                result = (
                    f"The source could not be accessed.\n"
                    f"URL: {source['url']}\n"
                    f"Error: {str(e)}\n"
                    f"Do not rely on this source. Try another relevant source."
                )
    #


'''
def run(question: str):
    #
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": question,
        }
    ]
    tools = [SEARCH_WEB_TOOL, OPEN_WEBPAGE_TOOL]
    #
    searched = False
    opened_source = False
    while True:

        response = chat(messages, tools)

        tool_calls = response["message"].get("tool_calls", [])

        if not tool_calls:
            if searched and not opened_source:
                messages.append({
                    "role": "user",
                    "content": (
                        "Has realizado una búsqueda, pero todavía no has "
                        "abierto ninguna fuente. Abre al menos una fuente "
                        "relevante antes de responder."
                    ),
                })
                continue
            return response["message"]["content"]

        messages.append(response["message"])

        for tool_call in tool_calls:

            name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            print(f"[AGENT] Ejecutando herramienta: {name}")
            print(f"[AGENT] Argumentos: {arguments}")

            if name == "search_web":

                result = search_web(arguments["query"])
                searched = True

            elif name == "open_webpage":

                try:
                    result = open_webpage(arguments["url"])
                    if len(result) >= 1000:
                        opened_source = True
                    else:
                        result = (
                            "The source could not be reliably extracted. "
                            "Only a very small amount of content was retrieved. "
                            "Do not use this source as evidence. Try another source."
                        )
                except Exception as e:
                    result = (
                        f"The source could not be accessed.\n"
                        f"URL: {arguments['url']}\n"
                        f"Error: {str(e)}\n"
                        f"Do not rely on this source. Try another relevant source."
                    )

            else:

                result = f"Herramienta desconocida: {name}"
            print(f"[AGENT] Resultado obtenido: {len(str(result))} caracteres")
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": str(result),
            })
'''