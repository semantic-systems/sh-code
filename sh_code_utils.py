from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import urlparse
from bs4 import BeautifulSoup, SoupStrainer
import urllib
from urllib.request import urlopen
from urllib.parse import quote
import json
import re
import importlib
import llms
import globals

importlib.reload(globals)

def load_json_data(file_name):
    try:
        with open(file_name, 'r') as json_file:
            data = json.load(json_file)
        return data['data']
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
        return []


def write_to_json(result, out_file_path):
    with open(out_file_path, "w", encoding="utf-8") as f:
        json.dump({"data": result}, f, indent=4)
    print("Successfully written to file!")



def query_sparql_endpoint(endpoint_url, sparql_query, search_key, flag=False):
    sparql = SPARQLWrapper(endpoint_url)
    if flag:
        sparql.setQuery(sparql_query % (search_key, search_key, search_key.strip("<>").strip()))
    else:
        sparql.setQuery(sparql_query % search_key)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return_result = []
    for result in results["results"]["bindings"]:
        converted_result = {}
        for key, value_info in result.items():
            value = value_info.get('value')
            if value:
                converted_result[key] = value
        return_result.append(converted_result)
    return return_result


def run_sparql_query(sparql_endpoint, sparql_query, param='', flag=False):
    if flag:
        sparql_query = sparql_query % param
    try:
        sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        query_results = sparql.query().convert()
        search_result = []
        if query_results:
            for result in query_results["results"]["bindings"]:
                temp = {}
                for key, value_info in result.items():
                    temp[key] = value_info.get('value')
                search_result.append(temp)
        return search_result
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def get_examples(key, file_path="./examples.json"):
    with open(file_path, 'r', encoding='utf-8') as file:
        examples = json.load(file)
    return examples.get(key, None)

def identify_title(question):
    example = get_examples("identify_title")
    prompt = f"""Task: Your task is extracting a publication title from the given phrase. 
                    Example
                        {example}                    
                    Do not add anything else.
                    Please provide your result in JSON format only. Please do not include the Example in your response.

                    phrase: {question}
                """
    title = llms.chatgpt(prompt, 6)
    if 'title' in title:
        if title['title']:
            return title['title'][0]
    else:
        return ''


def entity_linking(entity='', flag=True):
    sparql_end_point = "https://dblp-april24.skynet.coypu.org/sparql"
    if flag:
        if entity == '':
            return None
        entity = entity.rstrip("'")
        entity = entity.lstrip("'")
        entity = entity.rstrip('"')
        entity = entity.lstrip('"')
        if not entity.endswith('.'):
            entity += '.'
        query = """PREFIX dblp: <https://dblp.org/rdf/schema#>
                SELECT *
                  WHERE {
                  ?paper dblp:title "%s" .
                  ?author ^dblp:authoredBy ?paper ;
                          dblp:primaryCreatorName ?primarycreatorname ;
                          dblp:orcid ?orcid ;
                          dblp:wikipedia ?wikipedia .
                  FILTER (CONTAINS(STR(?wikipedia), "en.wikipedia.org"))
                }"""
    else:
        entity = entity.strip("<>")
        entity = f"<{entity}>"
        query = """PREFIX dblp: <https://dblp.org/rdf/schema#>
                SELECT *
                  WHERE {
                  %s dblp:primaryCreatorName ?primarycreatorname ;
                     dblp:orcid ?orcid ;
                     dblp:wikipedia ?wikipedia .
                  FILTER (CONTAINS(STR(?wikipedia), "en.wikipedia.org"))
                }"""

    sparql_result = run_sparql_query(sparql_end_point, query, entity, True)
    # print(search_result)
    return sparql_result


def search_author(author_dblp_uri):
    result = entity_linking(f"<{author_dblp_uri}>", False)
    if result:
        for r in result:
            if 'orcid' in r:
                globals.global_orcid = r['orcid']
                globals.global_author_wiki_uri = r['wikipedia']
                return r['primarycreatorname'], {"orcid": r['orcid'], "author_wikipedia": r['wikipedia']}