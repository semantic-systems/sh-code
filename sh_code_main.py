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