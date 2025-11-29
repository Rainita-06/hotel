from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware to add cache control headers to prevent browser caching
    of authenticated pages.
    """
    
    def process_response(self, request, response):
        # Add cache control headers to authenticated responses
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Prevent caching of authenticated pages
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        elif request.path.startswith('/dashboard/') and response.status_code == 200:
            # Also prevent caching of dashboard pages even if not authenticated
            # This ensures sensitive pages are never cached
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response
    
