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