__all__ = []

try:
    from django.conf import settings
    if hasattr(settings, "PLUGIN_USE_PROXY") and \
            settings.PLUGIN_USE_PROXY == True:
        __all__.append("record_proxy_backend")

    if hasattr(settings, "PLUGIN_DIRECT_LINKS_WITH_LIMITED_ACCESS") and \
            settings.PLUGIN_DIRECT_LINKS_WITH_LIMITED_ACCESS == True:
        __all__.append("direct_links_limited_access")

except: pass


