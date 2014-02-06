#!/usr/bin/env python

import sys
sys.path.insert(0, '../')

import json
import rdflib
import unittest

from SemanticMediaWiki import SemanticMediaWiki, smw_error

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

TEST_PAGE_NAME = 'Semantic MediaWiki Python Binding Test Page'
TEST_PAGE_CONTENT = '[[SMW_PYTHON_TEST::test]]'


class TestSemanticMediaWiki(unittest.TestCase):

    @staticmethod
    def _test_connection():
        assert wiki.wiki_status != smw_error.DOMAIN
        assert wiki.wiki_status != smw_error.PATH
        assert wiki.wiki_status != smw_error.HTTP_AUTH
        assert wiki.wiki_status != smw_error.HTTP_UNKNOWN
        assert wiki.wiki_status != smw_error.MW_API
        assert wiki.wiki_status != smw_error.WIKI_AUTH
        assert wiki.wiki_status != smw_error.NO_SMW
        assert wiki.wiki_status == smw_error.NONE

    @staticmethod
    def _init_test_page():
        page = wiki.site.Pages[TEST_PAGE_NAME]
        text = page.edit()
        if text != TEST_PAGE_CONTENT:
            page.save(
                TEST_PAGE_CONTENT, summary='SMW Python test edit in test_add_page')

    @staticmethod
    def __dump(json_data):
        print json.dumps(json_data, indent=4)

    @staticmethod
    def __versiontuple(v):
        return tuple(map(int, (v.split("."))))

    def test_parse(self):
        result = wiki.parse("'''Hello'''")
        assert 'text' in result
        assert '*' in result['text']
        assert '<b>Hello</b>' in result['text']['*']
        result =  wiki.parse_clean("'''Hello'''")
        result_html = u''.join(result.encode_contents().splitlines())
        assert '<html><body><p><b>Hello</b></p></body></html>' == result_html

    def test_get_data_ver_1_8(self):
        """
        test query if the SMW >= 1.8

        there is a result format change 1.7 -> 1.8
        """
        version = wiki.get_smw_version()
        assert version
        if self.__versiontuple(version) < self.__versiontuple("1.8.0"):
            return

        bad_query = r"""{{#ask_not_exsist_q1w2e3r4:foobar}}"""
        query = r"""
        {{#ask:
            [[SMW_PYTHON_TEST::+]]
        |?SMW_PYTHON_TEST
        |format = json
        }}
        """
        res = wiki.get_data(bad_query, format='json')
        assert not res
        res = wiki.get_data(query, format='json')
        assert res
        [query_result, query_path] = res
        # self.__dump(query_result)
        assert query_result
        assert query_result['rows'] == 1
        assert TEST_PAGE_NAME in query_result['results']

        # print wiki.unescapeSMW(query_path)

    def test_get_smw_version(self):
        "if fail, SMW may not be installed"
        assert wiki.get_smw_version()

    def test_getRDF(self):
        page_name = TEST_PAGE_NAME.replace(' ', '_')
        rdf = wiki.getRDF(page_name)
        g = rdflib.Graph()
        g.parse(data=rdf, format="application/rdf+xml")
        nsg = g.namespace_manager
        triples = []
        for s, p, o in g:
            s, p, o = map(nsg.normalizeUri, [s, p, o])
            triples.append("{} {} {}".format(s, p, o))
        assert 'wiki:{} wiki:Property-3ASMW_PYTHON_TEST wiki:Test'.format(
            page_name) in triples

    def test_getJSON(self):
        page_name = TEST_PAGE_NAME.replace(' ', '_')
        json_data = wiki.getJSON(page_name)
        # self.__dump(json_data)
        assert json_data['rdfs_label'] == TEST_PAGE_NAME
        assert json_data['SMW_PYTHON_TEST'] == 'Test'

    def test_list(self):
        assert wiki.list(prefix=TEST_PAGE_NAME)


if __name__ == "__main__":
    print "test with following config"
    print config
    TestSemanticMediaWiki._test_connection()
    TestSemanticMediaWiki._init_test_page()
    unittest.main()
