import json
import requests
import time


def search(pattern, cql_enable=True, board=None, year_from=None, year_to=None, number=20, wordsaroundhit=0, chunk_size=500, get_meta=False):
    """Wrapper function to query BlackLab API

    Parameters
    ----------
    pattern : str, 
        Pattern to search for
    cql_enable : bool, optional
        Whether `pattern` is written in CQL, by default True
    board : str, optional
        Limit search to a particular board, by default None
    year_from : int, optional
        Limit search to dates after `yyyy-01-01`, where yyyy equals `year_from`, by default None
    year_to : int, optional
        Limit search to dates before `yyyy-12-31`, where yyyy equals `year_from`, by default None
    number : int, optional
        Number of results to return, by default 20.
        If None, returns all matching results found in the corpus (BE CAREFUL, this place a heavy load
        on the BlackLab server if there is a large number of matching results).
    wordsaroundhit : int, optional
        The number of tokens around the keywords to return, by default 0
    chunk_size : int, optional
        Number of results to return for each iteration of query, by default 500
    get_meta : bool, optional
        Whether to return meta data, by default False

    Returns
    -------
    tuple
        If get_meta is False, returns a tuple of length two: (hits, requested_urls).
        If get_meta is True, returns a tuple of length three: (hits, metadata, requested_urls).
    """
    PTT_BLACKLAB_API = "http://140.112.147.132:8999/blacklab-server"
    
    filters = []
    filter_string = ""

    if not isinstance(pattern, str): 
        raise ValueError("pattern must be given in type <string>!")

    if type(year_from) != type(year_to):
        raise ValueError("year_from and year_to must be in type <string>!")

    if not cql_enable:
        pattern = f"[word=\"{pattern}\"]"

    if board is not None:
        filters.append(f'board:("{board}")')

    if year_from is not None and year_to is not None:
        filters.append(f'year:[{year_from} TO {year_to}]')

    if len(filters) != 0:
        filter_string = " AND ".join(filters) + "&"
    
    params = {
            'outputformat': 'json',
            'filter': filter_string,
            'waitfortotal': 'yes',
            'wordsaroundhit': wordsaroundhit,
            'patt': pattern,
            'first': 0,
            'number': 0
        }

    # Get meta
    response = requests.get(f'{PTT_BLACKLAB_API}/indexes/hits/', params=params)
    text = json.loads(response.text)
    num_of_results_found = text.get("summary").get("numberOfHits")
    print(f'Found {num_of_results_found} results')
    params['number'] = chunk_size
    # Pagination
    if number is None:
        number = num_of_results_found
    num_of_pages = int(number // chunk_size + 0.01) + 1

    requested_urls = []
    hits = []
    for i in range(num_of_pages):
        # Last page
        if i == num_of_pages - 1:
            params['number'] = number % chunk_size
           
        response = requests.get(f'{PTT_BLACKLAB_API}/indexes/hits/', params=params)
        requested_urls.append(response.url)
        text = json.loads(response.text)
        if num_of_results_found <= len(hits): break
        if text.get("hits") is None: break
        hits += text.get("hits")
        params['first'] += chunk_size

    if get_meta:
        return hits, text.get("summary"), requested_urls
    return hits, requested_urls


def get_capture_groups(hit, pos_tags=False):
    """Get CQL labeled groups from a search result

    Parameters
    ----------
    hit : dict
        The returned data of the BlackLab api, see search().
    pos_tags : bool, optional
        Whether to include PoS tags in the returned data, by default False,
        which only includes word forms.

    Returns
    -------
    dict
        A dictionary with keys matching the CQL labeled group name and 
        values the corresponding captured keywords captured in a CQL named group.
    """
    s_idx = hit['start']
    
    fullcntx_words = hit['left']['word'] + hit['match']['word'] + hit['right']['word']
    fullcntx_tags = hit['left']['pos'] + hit['match']['pos'] + hit['right']['pos']
    
    groups = {}
    for g in hit['captureGroups']:
        start, end = g['start'] - s_idx, g['end'] - s_idx
        
        tokens = fullcntx_words[start:end]
        if pos_tags:
            tags = fullcntx_tags[start:end]
            tokens = [(tokens[i], tags[i]) for i in range(len(tokens))]
        
        groups[g['name']] = tokens
    
    return groups


def top_n(freq_table: dict, n=25):
    return sorted(freq_table.items(), key=lambda x: x[1], reverse=True)[:n]
