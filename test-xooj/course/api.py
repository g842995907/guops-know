from common_framework.utils.cache import CacheProduct, cache_wrapper
from common_framework.utils.constant import Status

from course import models as course_models
_cache_instance = CacheProduct("course")

@cache_wrapper(_cache_instance, cache_age=20)
def get_lesson(course_id):
    return course_models.Lesson.objects.filter(course__id=course_id, status=Status.NORMAL)