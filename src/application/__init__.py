from .application import app, builder

# FIXME:
# modules imports sequence: app -> handlers -> pooling
# otherwise, if handlers module won't included in uploaded modules, app won't have any handlers at all
#
__all__ = ['app', 'builder']
