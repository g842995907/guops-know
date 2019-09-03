from rest_framework import response, status

from common_framework.utils.rest.validators import Validator

def to_error(code, message):
    return {
        'error_code': code,
        'error_message': message
    }

ILLEGAL_REQUEST_PARAMETERS = to_error(0x0010, 'illegal request parameters')

def list_view(request, queryset, serializer):
    validator = Validator(request.query_params)
    validator.validate('offset', required=True, isdigit=True, min=0)
    validator.validate('limit', required=True, isdigit=True, min=0)
    if not validator.is_valid:
        return response.Response(ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)

    offset = int(request.query_params['offset'])
    limit = int(request.query_params['limit'])

    total = len(queryset)
    queryset = queryset[offset:offset + limit]

    rows = [serializer(row).data for row in queryset]

    return response.Response({'total': total, 'rows': rows}, status=status.HTTP_200_OK)