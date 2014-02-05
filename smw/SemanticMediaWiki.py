"""
Semantic MediaWiki wrapper

2013-08-12: first package relase
"""

import mwclient
import string
import base64
import rdflib
import urllib2

from bs4 import BeautifulSoup


class WikiHTTPPool(mwclient.http.HTTPPool):
    header_auth = {}

    def __init__(self, http_login, http_pass):
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


class SemanticMediaWiki(object):

    site = None  # mwclient.Site
    conn = None
    rdf_store = None
    rdf_session = None

    def __init__(self, host, path="/",
                 http_login=None, http_pass=None,
                 wiki_login=None, wiki_pass=None):

        self.site = mwclient.Site(host, path,
                                  pool=WikiHTTPPool(http_login, http_pass))
        self.site.login(wiki_login, wiki_pass)

        # print self.site.connection
        # print self.site.connection.__class__.__name__

        self.conn = self.site.connection.find_connection(host)
        # print self.conn
        # print self.conn.__class__.__name__
        #assert isinstance(self.conn, HTTPPersistentConnection)

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

    def get_data(self, ask_query):
        """
        ask_query is a SMW ask query in one of the data export format.

        In SMW 1.7, they are json, csv, dsv, rss, rdf, kml, icalendar, bibtex
        and vcard.

        A link will be generated from the query. This function parse the link
        and read the content of the link
        """
        try:
            result = self.parse(ask_query)
            html = result['text']['*']
            soup = BeautifulSoup(html)
            path = soup.find('a').get('href')
            # print path
            data = self.get(path)
            return data, path
        except Exception as e:
            print e

        return None

    def getRDF(self, page):
        #page = self.site.Pages['Special:ExportRDF/'+page]
        # return page.get_expanded()

        # this is just a hack. some sites may not have "index.php".
        path = self.site.path + 'index.php/Special:ExportRDF/' + page
        # print path
        rdf = self.get(path)
        return rdf

    def unescapeSMW(self, url):
        url = url.replace("-", "%")
        return urllib2.unquote(url)

    def getJSON(self, page):
        # print page

        # percent-encode url name
        qPage = urllib2.quote(page.encode('utf-8'), safe='')
        rdf = self.getRDF(qPage)
        # print rdf

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
