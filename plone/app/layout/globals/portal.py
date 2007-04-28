from zope.interface import implements
from zope.component import getUtility
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError

from plone.memoize.view import memoize, memoize_contextless

from Acquisition import aq_inner
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from plone.app.layout.navigation.root import getNavigationRoot

from interfaces import IPortalState

class PortalState(BrowserView):
    """Information about the state of the portal
    """
    
    implements(IPortalState)
    
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self._context = [context]

    @memoize_contextless
    def portal(self):
        return getUtility(ISiteRoot)
    
    @memoize_contextless
    def portal_title(self):
        return self.portal().Title()
        
    @memoize_contextless
    def portal_url(self):
        return self.portal().absolute_url()
        
    @memoize_contextless
    def navigation_root_path(self):
        return getNavigationRoot(aq_inner(self.context))
    
    @memoize_contextless
    def navigation_root_url(self):
        rootPath = self.navigation_root_path()
        return self.request.physicalPathToURL(rootPath)
    
    @memoize_contextless
    def default_language(self):
        site_properties = getToolByName(aq_inner(self.context), "portal_properties").site_properties
        return site_properties.getProperty('default_language', None)

    @memoize
    def language(self):
        return self.request.get('language', None) or \
                aq_inner(self.context).Language() or self.default_language

    @memoize_contextless
    def locale(self):
        # This code was adopted from zope.publisher.http.setupLocale
        envadapter = IUserPreferredLanguages(self.request, None)
        if envadapter is None:
            return None

        _locale = None
        langs = envadapter.getPreferredLanguages()
        for httplang in langs:
            parts = (httplang.split('-') + [None, None])[:3]
            try:
                _locale = locales.getLocale(*parts)
                break
            except LoadLocaleError:
                # Just try the next combination
                pass
        else:
            # No combination gave us an existing locale, so use the default,
            # which is guaranteed to exist
            _locale = locales.getLocale(None, None, None)

        return _locale

    @memoize_contextless
    def is_rtl(self):
        _locale = self.locale()
        if _locale is None:
            # We cannot determine the orientation
            return False

        char_orient = _locale.orientation.characters
        if char_orient == u'right-to-left':
            return True

        return False

    @memoize_contextless
    def member(self):
        tool = getToolByName(aq_inner(self.context), "portal_membership")
        return tool.getAuthenticatedMember()

    @memoize_contextless
    def anonymous(self):
        tool = getToolByName(aq_inner(self.context), "portal_membership")
        return bool(tool.isAnonymousUser())

    @memoize_contextless
    def friendly_types(self):
        site_properties = getToolByName(aq_inner(self.context), "portal_properties").site_properties
        not_searched = site_properties.getProperty('types_not_searched', [])

        types = getToolByName(aq_inner(self.context), "portal_types").listContentTypes()
        return [t for t in types if t not in not_searched]
