import logging

logger = logging.getLogger('authentif')

class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log the request method and path
        logger.debug(f'Incoming request: {request.method} {request.path}')
        
        # Log headers (be careful with sensitive data)
        # logger.debug(f'Headers: {request.headers}')

        # Log the CSRF token being checked
        # logger.debug(f'Cookie: {request.COOKIES}')
        # logger.debug(f'CSRF token from header: {request.headers.get("X-CSRFToken")}')

        # if request.method == 'POST':
        #     logger.debug(f'Body: {request.body}')

        response = self.get_response(request)
        return response
