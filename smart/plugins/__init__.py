__all__ = []

try:
    from django.conf import settings
    if hasattr(settings, 'PLUGIN_USE_PROXY') and \
            settings.PLUGIN_USE_PROXY == True:
        __all__.append("record_proxy_backend")
        
    if hasattr(settings, 'PLUGIN_USE_DIRECT') and \
            settings.PLUGIN_USE_DIRECT == True:
        __all__.append("direct_proxy_plugin")

except: pass


