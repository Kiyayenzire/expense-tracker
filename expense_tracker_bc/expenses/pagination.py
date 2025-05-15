from rest_framework.pagination import LimitOffsetPagination

class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    # max_limit = None  # remove upper limit so users can get full list
    max_limit = 101  # remove upper limit so users can get full list
