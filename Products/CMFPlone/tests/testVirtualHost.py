# -*- coding: utf-8 -*-
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import setRoles
from plone.testing.z2 import Browser
from plone.app.textfield.interfaces import ITransformer
from plone.app.textfield.value import RichTextValue
from Products.CMFPlone.testing import PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING
from Products.CMFPlone.utils import _createObjectByType
from plone.subrequest import subrequest
import transaction
import unittest


def just_text(context):
    """Just return the text."""
    # return context.text.output
    value = context.text
    transformer = ITransformer(context, None)
    if transformer is None:
        raise ValueError("ITransformer not found.")
    output = transformer(value, "text/x-html-safe")
    # print("")
    # print(output)
    # print("")
    return output


def with_sub(context):
    """With sub request."""
    target_url = context.link.absolute_url()
    # target_url above is always the plain url without virtualhost...
    # base_url = "http://nohost/VirtualHostBase/http/nohost:80/VirtualHostRoot/plone/"
    # target_url = base_url + "link"
    response = subrequest(target_url)
    return response.getBody()


class TestPloneTextFieldTransform(unittest.TestCase):
    """Test plone.app.textfield with transform, subrequest and VirtualHosting.
    """

    layer = PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        # Create a target/destination for a link.
        self.target = _createObjectByType("Document", self.portal, "target")
        uid = self.target.UID()

        # Create a page with a link:
        link = _createObjectByType("Document", self.portal, "link")
        text = """<p><a class="internal-link" href="resolveuid/{0}" target="_self" title="">link</a>.</p><p>And some ünicode.</p>""".format(
            uid
        )
        value = RichTextValue(
            raw=text, mimeType="text/html", outputMimeType="text/x-html-safe"
        )
        link.text = value
        # Let the view of the link return only the text.
        link.__class__.just_text = just_text
        link._setProperty("layout", "just_text")
        self.link = link

        # Create a page that does a sub request.
        sub = _createObjectByType("Document", self.portal, "sub")
        sub.__class__.with_sub = with_sub
        sub._setProperty("layout", "with_sub")
        self.sub = sub

        transaction.commit()
        self.browser = Browser(self.layer["app"])
        self.browser.handleErrors = False
        self.browser.addHeader(
            "Authorization", "Basic %s:%s" % (TEST_USER_NAME, TEST_USER_PASSWORD)
        )

    def testNormalRequest(self):
        base_url = "http://nohost/plone/"

        # Render the page with the link:
        self.browser.open(base_url + "link")
        body = self.browser.contents.decode("utf8")
        self.assertIn(self.target.absolute_url(), body)

        # Render the page that uses a sub request to render the page with the link:
        self.browser.open(base_url + "sub")
        body = self.browser.contents.decode("utf8")
        self.assertIn(self.target.absolute_url(), body)

    def testVirtualHostRequest(self):
        base_url = "http://nohost/VirtualHostBase/http/nohost:80/VirtualHostRoot/plone/"

        # Failed try with different url as base for browser.
        # app = self.layer["app"]
        # browser = Browser(app, url=base_url)
        # browser.handleErrors = False
        # browser.addHeader(
        #     "Authorization", "Basic %s:%s" % (TEST_USER_NAME, TEST_USER_PASSWORD)
        # )

        # Render the page with the link:
        self.browser.open(base_url + "link")
        body = self.browser.contents.decode("utf8")
        self.assertIn(self.target.absolute_url(), body)

        # Render the page that uses a sub request to render the page with the link:
        self.browser.open(base_url + "sub")
        body = self.browser.contents.decode("utf8")
        self.assertIn(self.target.absolute_url(), body)
