import threading

_thread_locals = threading.local()

class GlobalRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response

def get_current_request():
    return getattr(_thread_locals, 'request', None)


def error_message(msg="no error message set"):
    from django.contrib import messages
    request = get_current_request()
    if request:
        return messages.warning(request, msg)
    return None