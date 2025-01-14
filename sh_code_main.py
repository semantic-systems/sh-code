import importlib
import globals
from collections import defaultdict
import json
import sh_code_parser
import sh_code_retriever_reader
import sh_code_utils
import llms
# Reload globals to make sure we get the latest version
importlib.reload(globals)


def build_sparql(question, uri):
    examples = sh_code_utils.get_examples("build_sparql_1")
    if 'author' in uri:
        examples = sh_code_utils.get_examples("build_sparql_2")
    prompt = f"""Convert question -> sparql: question is the simple question. And the sparql contains commands and variables. uri is the identifier of the entity under question. Which sparql to use, please follow the demo examples.
        Please do not add other relation name in the sparql.
        For example:
        {examples}

        Given question: {question}
        uri: {uri}
        sparql:

    """
    sparql = llms.chatgpt(prompt, 3)
    if sparql:
        return sparql['sparql']
    else:
        return ""


def question_parser(question, q_type="kg_text"):
    example = sh_code_utils.get_examples("question_parser_1")
    prompt_kg_kg_bridge = f"""Convert question -> HQ-representation: question is the scholarly complex question. And the HQ-representation contains operators and elements. Each element is a natural question. Operator is from [JOIN, AND] and each of them is a binary operator, which means it contains two elements. JOIN(KGQA2(a) ; KGQA1(b)) operator is for linear-chain reasoning that question a contains the placeholder (e.g. Ans#1) of question b's answer. Placeholder is to represent the answer from previous question. AND(KGQA2(a) ; KGQA1(b)) operator is for intersection reasoning that question a and b can be processed parallel. 
            JOIN and AND can be composed, like JOIN(KGQA2(c), JOIN(KGQA2(b), KGQA1(a))), AND(KGQA2(c), JOIN(KGQA2(b), KGQA1(a))). Which composition to use, please follow the demo examples. 
            For example:
            {example}
            Given question: {question}, 
            HQ-representation:

    """
    example_2 = sh_code_utils.get_examples("question_parser_2")
    prompt_kg_text = f"""Convert question -> HQ-representation: question is the scholarly complex question. And the HQ-representation contains operators and elements. Each element is a natural question. Operator is from [JOIN, AND] and each of them is a binary operator, which means it contains two elements. JOIN(TextQA(a) ; KGQA1(b)) operator is for linear-chain reasoning that question a contains the placeholder (e.g. Ans#1) of question b's answer. Placeholder is to represent the answer from previous question. AND(TextQA(a) ; KGQA1(b)) operator is for intersection reasoning that question a and b can be processed parallel. 
                JOIN and AND can be composed, like JOIN(TextQA(c), JOIN(KGQA2(b), KGQA1(a))), AND(TextQA(c), JOIN(KGQA2(b), KGQA1(a))). Which composition to use, please follow the demo examples. 
                For example:
                {example_2}
                Given question: {question}, 
                HQ-representation:

        """
    example_3 = sh_code_utils.get_examples("question_parser_3")
    prompt_kg_kg_comparison = f"""Convert question -> HQ-representation: question is the scholarly complex question. And the HQ-representation contains operators and elements. Each element is a natural question. Operator is from [JOIN, AND, COMP_>, COMP_<, COMP_=, UNION] and each of them is a binary operator, which means it contains two elements. JOIN(KGQA2(a) ; KGQA1(b)) operator is for linear-chain reasoning that question a contains the placeholder (e.g. Ans#1) of question b's answer. Placeholder is to represent the answer from previous question. AND(KGQA2(a) ; KGQA1(b)) operator is for intersection reasoning that question a and b can be processed parallel. COMP_>((a), (b)) operator is for comparison reasoning that compares a is greater than b. COMP_<((a), (b)) operator is for comparison reasoning that compares a is less than b. COMP_=((a), (b)) operator is for comparison reasoning that compares a is equal to b. 
                COMP_>, COMP_<, COMP_= and JOIN can be composed, like COMP_>(JOIN((KGQA2(b), KGQA2(a))), COMP_<(JOIN((KGQA2(b), KGQA2(a))), COMP_=(JOIN((KGQA2(b), KGQA2(a))), COMP_>(JOIN(KGQA2(b), KGQA1(a)), JOIN(KGQA2(d), KGQA1(c))), COMP_<(JOIN(KGQA2(b), KGQA1(a)), JOIN(KGQA2(d), KGQA1(c))), COMP_=(JOIN(KGQA2(b), KGQA1(a)), JOIN(KGQA2(d), KGQA1(c))), COMP_>(JOIN(KGQA2(c), JOIN(KGQA2(b), KGQA1(a))), JOIN(KGQA2(f), JOIN(KGQA2(e), KGQA1(d)))), COMP_<(JOIN(KGQA2(c), JOIN(KGQA2(b), KGQA1(a))), JOIN(KGQA2(f), JOIN(KGQA2(e), KGQA1(d)))), COMP_=(JOIN(KGQA2(c), JOIN(KGQA2(b), KGQA1(a))), JOIN(KGQA2(f), JOIN(KGQA2(e), KGQA1(d)))). Which composition to use, please follow the demo examples. 
                For example:
                {example_3}
                
                Given question: {question}, 
                HQ-representation:

            """
    prompt = prompt_kg_text
    prompt_mapping = {
        "kg_kg_bridge": prompt_kg_kg_bridge,
        "kg_kg_comparison": prompt_kg_kg_comparison
    }
    prompt = prompt_mapping.get(q_type, prompt)
    hq_representation = llms.chatgpt(prompt, 9)
    return hq_representation


def get_name(result):
    if 'uri' in result:
        uri = result['uri']
        uri = uri.strip('<>')
        uri = f"<{uri}>"
        endpoint = "https://semoa.skynet.coypu.org/sparql"
        sparql = """PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                        SELECT ?answer WHERE { 
                        %s foaf:name ?answer .}
                    """
        query_result = sh_code_utils.run_sparql_query(endpoint, sparql, uri, True)
        if query_result and len(query_result) > 0:
            return query_result[0]["answer"]
    return None