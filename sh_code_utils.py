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
    title = llms.chatgpt(prompt, 2)
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


def resolve_author(question, author_dblp_uri, q_type='bridge'):
    title = identify_title(question)
    if title == '':
        return '', {}
    entity = entity_linking(title)
    if q_type == 'bridge':
        if entity:
            for entity_item in entity:
                if 'orcid' in entity_item:
                    if urlparse(entity_item['author']) == urlparse(author_dblp_uri):
                        globals.global_orcid = entity_item['orcid']
                        globals.global_author_wiki_uri = entity_item['wikipedia']
                        return entity_item['primarycreatorname'], {"orcid": entity_item['orcid'], "author_wikipedia": entity_item['wikipedia']}

        return search_author(author_dblp_uri)
    else:
        author_uris = [value.strip('<>') for item in author_dblp_uri for value in item.values()]
        if entity:
            for entity_item in entity:
                if 'orcid' in entity_item:
                    if entity_item['author'] in author_uris:
                        if entity_item['author'] not in globals.global_visited_author_uri:
                            globals.global_visited_author_uri.append(entity_item['author'])
                            return entity_item['primarycreatorname'], {"orcid": entity_item['orcid'],
                                                                       "author_wikipedia": entity_item['wikipedia']}
        if len(author_uris) > 1:
            if author_uris[0] not in globals.global_visited_author_uri:
                globals.global_visited_author_uri.append(author_uris[0])
                return search_author(author_uris[0])
            if author_uris[1] not in globals.global_visited_author_uri:
                globals.global_visited_author_uri.append(author_uris[1])
                return search_author(author_uris[1])


def search_semoa_author(author_dblp_orcid):
    sparql_endpoint = "http://localhost:3030/sopena/sparql"
    orcid_query = """PREFIX ns2: <https://semopenalex.org/ontology/>
               PREFIX ns3: <http://purl.org/spar/bido/>
               PREFIX ns4: <https://dbpedia.org/ontology/>
               PREFIX ns5: <https://dbpedia.org/property/>

               SELECT * WHERE
               {
               GRAPH <https://semopenalex.org/authors/context> {
                 {
                   OPTIONAL {?author_uri ns2:orcidId ?orcid . }
                   OPTIONAL {?author_uri ns3:orcidId ?orcid . }
                   OPTIONAL { ?author_uri ns4:orcidId ?orcid . }
                   OPTIONAL { ?author_uri ns5:orcidId ?orcid . }
                   FILTER (?orcid = "%s")
                   }
                   }
               } 
           """
    orcid_query_result = query_sparql_endpoint(sparql_endpoint, orcid_query, author_dblp_orcid)
    if orcid_query_result:
        author_semoa_uri = orcid_query_result[0]['author_uri']
        return author_semoa_uri
    else:
        return None


def extract_text_from_wikipedia(url):
    try:
        decoded_url = urllib.parse.unquote(url)
        wikipedia_url = decoded_url.replace(" ", "_")
        encoded_url = quote(wikipedia_url, safe=':/')
        source = urlopen(encoded_url).read()
        soup = BeautifulSoup(source, 'lxml')
        title = soup.title.string.strip()
        title = title.rstrip('- Wikipedia')
        text = ''
        for paragraph in soup.find(id="bodyContent").find_all('p'):
            text += paragraph.text
        pattern = r'\[\d+\]'
        cleaned_wikipedia_text = re.sub(pattern, '', text)
        cleaned_wikipedia_text = cleaned_wikipedia_text.strip()
        return cleaned_wikipedia_text
    except Exception as e:
        print(f"General Exception: {e}")
        print(f"Failed to retrieve: {url}")
        return None