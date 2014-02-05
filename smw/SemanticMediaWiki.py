"""
Semantic MediaWiki wrapper

2013-08-12: first package internal release
2014-02-04: 0.1 release
"""

import string
import base64
import urllib2
import traceback
import socket
import json

import rdflib
import mwclient
from bs4 import BeautifulSoup, Comment
from enum import Enum


class WikiHTTPPool(mwclient.http.HTTPPool):
    header_auth = {}

    def __init__(self, http_login, http_pass):
        if http_login and http_pass:
            token = http_login + ':' + http_pass
            auth = 'Basic ' + string.strip(base64.encodestring(token))
            self.header_auth['Authorization'] = auth

        super(WikiHTTPPool, self).__init__()

    def updateHeader(self,  headers=None):
        if headers:
            headers.update(self.header_auth)
        else:
            headers = self.header_auth
        return headers

    def get(self, host, path, headers=None):
        return super(WikiHTTPPool, self).get(host, path,
                                             self.updateHeader(headers))

    def post(self, host, path, headers=None, data=None):
        return super(WikiHTTPPool, self).post(host, path,
                                              self.updateHeader(headers), data)

    def head(self, host, path, headers=None, auto_redirect=False):
        return super(WikiHTTPPool, self).head(host, path,
                                              self.updateHeader(headers), auto_redirect)

    def request(self, method, host, path, headers, data, raise_on_not_ok, auto_redirect):
        return super(WikiHTTPPool, self).request(method, host, path,
                                                 self.updateHeader(headers), data, raise_on_not_ok, auto_redirect)


smw_error = Enum(
    'NONE',
    'HTTP_UNKNOWN',
    'DOMAIN',
    'PATH',
    'HTTP_AUTH',
    'WIKI_AUTH',
    'MW_API',
    'NO_SMW'
)


class SemanticMediaWiki(object):
    site = None  # mwclient.Site
    conn = None
    rdf_store = None
    rdf_session = None
    wiki_status = smw_error.NONE

    def __init__(self, host, path="/",
                 http_login=None, http_pass=None,
                 wiki_login=None, wiki_pass=None):

        try:
            self.site = mwclient.Site(host, path,
                                      pool=WikiHTTPPool(http_login, http_pass))
            self.conn = self.site.connection.find_connection(host)
            # print self.site.connection
            # print self.site.connection.__class__.__name__
            assert isinstance(
                self.conn, mwclient.http.HTTPPersistentConnection)
        except socket.error as e:
            # print "domain error: {}".format(host),  e
            self.wiki_status = smw_error.DOMAIN
            return
        except mwclient.errors.HTTPStatusError as e:
            status, res = e  # int, httplib.HTTPResponse
            # print res.msg
            # print res.reason
            if status == 404:
                # print "wiki url error: {}{}".format(host,path),  res.reason
                self.wiki_status = smw_error.PATH
            elif status == 401:
                # print "http user/password wrong"
                self.wiki_status = smw_error.HTTP_AUTH
            else:
                # print e
                self.wiki_status = smw_error.HTTP_UNKNOWN
            return
        except ValueError as e:
            # traceback.print_exc()
            self.wiki_status = smw_error.MW_API
            return

        try:
            self.site.login(wiki_login, wiki_pass)
            if not self.site.credentials:
                print "wiki login or password wrong"
                self.wiki_status = smw_error.WIKI_AUTH
        except mwclient.errors.LoginError as e:
            self.wiki_status = smw_error.WIKI_AUTH
            return

        smw_version = self.get_smw_version()
        if not smw_version:
            self.wiki_status = smw_error.NO_SMW

    def get(self, path):
        """
        take a relative path of the wiki, and return html of the path
        """

        # httplib.HTTPResponse
        response = self.conn.get(self.site.host, path,
                                 headers=self.site.connection.header_auth)
        return response.read()

    def parse(self, wiki_text):
        return self.site.parse(wiki_text)

    def parse_clean(self, wiki_text):
        result = self.parse(wiki_text)
        html_raw = result['text']['*']
        soup = BeautifulSoup(html_raw)
        comments = soup.findAll(text=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
        return soup
        # print soup.encode_contents()
        # return unicode.join(u'',map(unicode,soup))

    def get_data(self, ask_query, format=None):
        """
        ask_query is a SMW ask query in one of the data export format.

        In SMW 1.7, they are json, csv, dsv, rss, rdf, kml, icalendar, bibtex
        and vcard.

        A link will be generated from the query. This function parse the link
        and read the content of the link

        format is 'json' or None (default return as string)
        """
        try:
            # result = self.parse(ask_query)
            # html = result['text']['*']
            # soup = BeautifulSoup(html)
            soup = self.parse_clean(ask_query)
            path = soup.find('a').get('href')
            # print path
            data = self.get(path)
            if format == 'json':
                data = json.loads(data)
            return data, path
        except Exception as e:
            # traceback.print_exc()
            print

        return None

    def getRDF(self, page):
        """
        get metadata of a page in RDF
        """

        # page = self.site.Pages['Special:ExportRDF/'+page]
        # return page.get_expanded()

        # this is just a hack. some sites may not have "index.php".
        path = self.site.path + 'index.php/Special:ExportRDF/' + page
        # print path
        rdf = self.get(path)
        return rdf

    def unescapeSMW(self, url):
        url = url.replace("-", "%")
        return urllib2.unquote(url)

    def get_smw_version(self):
        if self.site:
            results = self.site.api(action='query',
                                    meta='siteinfo',
                                    siprop='extensions',
                                    format='json')
            extensions = results['query']['extensions']
            for ext in extensions:
                if ext['name'] == 'Semantic MediaWiki':
                    return ext['version']

        return None

    def getJSON(self, page):
        """
        get metadata of a page in JSON
        """

        # percent-encode url name
        qPage = urllib2.quote(page.encode('utf-8'), safe='')
        rdf = self.getRDF(qPage)

        g = rdflib.Graph()
        g.parse(data=rdf, format="application/rdf+xml")

        # find the domain name for "wiki"
        nsg = g.namespace_manager
        ns = g.namespaces()
        uri = "wiki:"
        for prefix, uri in ns:
            if prefix == "wiki":
                # print uri
                break

        subject = rdflib.URIRef(uri + qPage.replace("-", "-2D"))
        # print subject
        # print nsg.normalizeUri(subject)

        json_object = {}
        for p, o in g.predicate_objects(subject):
            # print p, "==", o
            property = nsg.normalizeUri(p)
            property = self.unescapeSMW(property)
            if property.startswith("wiki:Property:"):
                property = property.replace("wiki:Property:", "", 1)
            if isinstance(o,  rdflib.URIRef):
                if property in ["swivt:page", "rdfs:isDefinedBy"]:
                    object = o
                else:
                    object = self.unescapeSMW(nsg.normalizeUri(o))
                    if object.startswith("wiki:"):
                        object = object.replace("wiki:", "", 1)
            else:
                object = o

            if property.startswith("swivt:specialProperty"):
                continue
            if (property == "rdf:type") and (object == "swivt:Subject"):
                continue
            property = property.replace(":", "_")
            json_object[property] = object
            # print property, " == ",  object
            # print "===================="

        # @TODO: handle internal objects

        return json_object
