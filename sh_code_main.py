import importlib
import globals
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


def get_inst_uri(param):
    sparql_endpoint = "https://semoa.skynet.coypu.org/sparql"
    sparql = """
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               SELECT ?inst_wikipedia_url
               WHERE {
                   %s rdfs:seeAlso ?inst_wikipedia_url .
                  FILTER (CONTAINS(STR(?inst_wikipedia_url), "en.wikipedia.org"))
                }
               """
    param = param.strip("<>")
    query_result = sh_code_utils.run_sparql_query(sparql_endpoint, sparql, f"<{param}>", True)
    if query_result and len(query_result) > 0:
        return query_result[0]["inst_wikipedia_url"]


def KGQA1(question, author_dblp_uri):
    if isinstance(author_dblp_uri, list):
        return sh_code_utils.resolve_author(question, author_dblp_uri, "comparison")
    return sh_code_utils.resolve_author(question, author_dblp_uri)


def KGQA2(question, uris):
    sparql_endpoint = "https://semoa.skynet.coypu.org/sparql"
    prefix = """
    PREFIX soa: <https://semopenalex.org/ontology/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX ns3: <http://purl.org/spar/bido/>
    PREFIX org: <http://www.w3.org/ns/org#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    """

    def execute_query(uri, question):
        # print(uris)
        sparql = build_sparql(question, uri)
        final_sparql = prefix + sparql
        # print(f"Executing SPARQL Query:\n{final_sparql}")
        try:
            result = sh_code_utils.run_sparql_query(sparql_endpoint, final_sparql)
            if result and len(result) > 0:
                # print(f"SPARQL Result: {result}")
                answer = result[0]["answer"]
                uri_result = result[0].get("uri", uri)
                return answer, {"uri": uri_result}
            else:
                return None, uris  # Return None if no result found
        except Exception as e:
            print(f"SPARQL Query Execution Error: {e}")
            return None, uris

    if uris:
        if 'orcid' in uris:
            semoa_author_uri = sh_code_utils.search_semoa_author(uris["orcid"])
            if semoa_author_uri:
                return execute_query(semoa_author_uri, question)
        if 'uri' in uris:
            if uris['uri'].__contains__('institution'):
                globals.global_author_inst_wiki_uri = get_inst_uri(uris['uri'])
            return execute_query(uris['uri'], question)

        print("No valid ORCID or URI.")
    return None, uris


def textQA(question, uris):
    text = ''
    if "author_wikipedia" in uris:
        text = sh_code_utils.extract_text_from_wikipedia(uris["author_wikipedia"])
    if 'uri' in uris:
        # print(uris)
        if uris['uri'].__contains__('institution'):
            inst_uri = uris['uri']
            globals.global_author_inst_wiki_uri = inst_uri
            inst_uri = inst_uri.strip("<>")
            inst_wiki = get_inst_uri(f"<{inst_uri}>")
            # print(inst_wiki)
            text = sh_code_utils.extract_text_from_wikipedia(inst_wiki)
    if text:
        text = text.strip()
        answer, top_n_answers = sh_code_retriever_reader.run_retriever_reader(question, text, chunk_size=200, top_n=3)
        return answer, top_n_answers
    return None, uris


def run_parsing_based_answer_extractor(test_data_path, prediction_file_path):
    test_data = sh_code_utils.load_json_data(test_data_path)
    answer_predictions = sh_code_utils.load_json_data(prediction_file_path)
    for item in test_data:
        question = item["question"]
        author_dblp_uri = item["author_dblp_uri"]
        source_type = " ".join(item['source_types'])
        if source_type == 'KG KG':
            if item["type"] == 'bridge':
                hq_representation = question_parser(question, "kg_kg_bridge")
            else:
                hq_representation = question_parser(question, "kg_kg_comparison")
        else:
            hq_representation = question_parser(question)

        try:
            globals.global_visited_author_uri = []
            tree = sh_code_parser.parse_expression(hq_representation['hq_representation'])
            globals.global_author_uri = author_dblp_uri
            answer, context = sh_code_parser.evaluate_tree(tree, author_dblp_uri)  # in case of textQA uri will be set top-n chunks
            if item["type"] == 'comparison':
                answer = get_name(answer)
        except Exception as e:
            print(f"An error occurred: {e}")
            answer = None
            context = None
        answer_predictions.append({"author_dblp_uri": author_dblp_uri,
                                   "id": item["id"],
                                   "question": question,
                                   "answer": answer,
                                   "hq_representation": hq_representation['hq_representation'],
                                   "parse_tree": str(tree),
                                   "context": context,
                                   "type": item["type"],
                                   "source_type": source_type,
                                   "global_author_uri": globals.global_author_uri,
                                   "global_visited_author_uri": globals.global_visited_author_uri,
                                   "global_author_wiki_uri": globals.global_author_wiki_uri,
                                   "global_author_inst_wiki_uri": globals.global_author_inst_wiki_uri
                                   })
        sh_code_utils.write_to_json(answer_predictions, prediction_file_path)
