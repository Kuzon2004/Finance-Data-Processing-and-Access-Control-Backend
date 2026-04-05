from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

def global_error_interceptor(exc, context):
    """
    Standardizes all error responses intercepting unhandled Python crashes and 
    formatting standard DRF errors into identical predictable JSON shapes.
    """
    response = exception_handler(exc, context)

    # If DRF inherently understands the exception (e.g., 400 Validation, 401 Auth)
    if response is not None:
        return Response({
            'error': {
                'code': response.status_code,
                'type': exc.__class__.__name__,
                'message': response.data
            }
        }, status=response.status_code)

    # Trap unhandled Database Integrity collisions explicitly
    if isinstance(exc, IntegrityError):
        return Response({
            'error': {
                'code': 409,
                'type': 'ConflictError',
                'message': 'Database integrity violation detected.'
            }
        }, status=409)

    # Trap global missing instances to 404 implicitly
    if isinstance(exc, ObjectDoesNotExist):
        return Response({
            'error': {
                'code': 404,
                'type': 'NotFoundError',
                'message': 'The requested resource could not be found.'
            }
        }, status=404)

    # Fallback to absolute generic 500 error preventing stack trace leaks
    return Response({
        'error': {
            'code': 500,
            'type': 'InternalServerError',
            'message': 'An unexpected system failure occurred.'
        }
    }, status=500)
