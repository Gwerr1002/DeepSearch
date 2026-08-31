import yaml
from re import split

class UsrDefined:
    def _load_content(self):
        with open("/app/research_task.yml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.research_task = config['research_task']
        self.search_terms = [split(r"\s*,\s*",st.lower())
                             for st in config['search_terms']]
        return config['search'], config['evaluations']

class Config:
    def __init__(self,usr : UsrDefined):
        self._usr_constants(*usr._load_content())
        self._promt_related()
        self._rubrik_evaluations()
        self._web_block_patterns()
    #
    def _usr_constants(self,search,eval):
        # Search
        self.MAX_SRC = search['max_results']
        self.MAX_RELEVANT_SRC = search['max_relevant_sources_per_iteration']
        self.MAX_ITER = search['max_queries']
        # Evaluations
        self.THRES_SCORE_EVAL = eval['threshold_score_eval']
        self.THRES_SCORE_TERMS = eval['threshold_score_terms']
        self.MIN_TERMS_SCORE_SRCS = eval['min_term_score_sources']
    #
    def _promt_related(self):
        from config import syspromt
        # TASK
        self.TASK_ANALYZER_PROMPT = syspromt.TASK_ANALYZER_PROMPT
        self.TASK_ANALYZER_SCHEMA = syspromt.TASK_ANALYZER_SCHEMA
        # QUERY
        self.QUERY_GENERATOR_PROMPT = syspromt.QUERY_GENERATOR_PROMPT
        self.QUERY_GENERATOR_SCHEMA = syspromt.QUERY_GENERATOR_SCHEMA
        # WEB EVALUATOR
        self.RESULT_WEB_EVALUATOR_PROMPT = syspromt.RESULT_WEB_EVALUATOR_PROMPT
        self.RESULT_WEB_EVALUATOR_SCHEMA = syspromt.RESULT_WEB_EVALUATOR_SCHEMA
        # EVIDENCE EVALUATOR
        self.EVIDENCE_EVALUATOR_PROMPT = syspromt.EVIDENCE_EVALUATOR_PROMPT
        self.EVIDENCE_EVALUATOR_SCHEMA = syspromt.EVIDENCE_EVALUATOR_SCHEMA
        # SUMMARY
        self.ANSWER_PROMPT = syspromt.ANSWER_PROMPT
        self.ANSWER_PROMPT_FINAL = syspromt.ANSWER_PROMPT_FINAL
    #
    def _rubrik_evaluations(self):
        #
        self.COVER = {
            "NONE" : 0, 
            "PARTIAL" : 0.1, 
            "MOST":0.15, 
            "FULL":0.3
            }
        #
        self.EVIDENCE = {
            "NULL" : 0, 
            "SOME" : 0.0375, 
            "MODERATE" : 0.075, 
            "SUFFICIENT" : 0.15
        }
        #
        self.INFO = {
            "SAME" : 0, 
            "RELATED" : 0.075, 
            "COMPLEMENTARY" : 0.15
            }
    #
    def _web_block_patterns(self):
        self.BLOCK_PATTERNS = [
            "cookies must be enabled",
            "verify you are human",
            "prove you are human",
            "access denied",
            "request blocked",
            "bot verification",
            "robot check",
            "captcha",
            "recaptcha",
            "hcaptcha",
        ]

task = UsrDefined()
cnf = Config(task)