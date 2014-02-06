## Semantic MediaWiki


Sematic MediaWiki python binding

This depends on mwclient 0.7 development version

>https://github.com/mwclient/mwclient.git
 
To install

>pip install smw
 
Or install from github
> pip install git+git://github.com/baojie/smw.git

Usage example

```python
# change this to your wiki's config
config = {
    "host": "www.foo.com",
    "path": "/wiki/",
    "http_login": None,
    "http_pass": None,
    "wiki_login": None,
    "wiki_pass": None,
}

wiki = SemanticMediaWiki(
    host=config["host"],
    path=config["path"],
    http_login=config["http_login"],
    http_pass=config["http_pass"],
    wiki_login=config["wiki_login"],
    wiki_pass=config["wiki_pass"])

query = r"""
{{#ask:
    [[SMW_PYTHON_TEST::+]]
|?SMW_PYTHON_TEST
|format = json
}}
"""

res = wiki.get_data(query, format='json')
[query_result, query_path] = res
# process query results from SMW >= 1.8.0
items = query_result['results']
for page in query_result['results']:
    print items[page]
```
