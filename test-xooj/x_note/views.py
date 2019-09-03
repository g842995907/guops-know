from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from common_framework.utils.constant import Status
from common_framework.utils.rest.request import RequestData

from common_web.decorators import login_required

from x_note.models import Note
from x_note.serializers import NoteSerializer


class NoteView(generics.RetrieveAPIView):
    serializer_class = NoteSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        queryset = Note.objects.filter(user=self.request.user).filter(
                            status=Status.NORMAL)
        return queryset

    def get_object(self):
        data = RequestData(self.request, is_query=True)
        resource = data.get('resource')
        filter_kwargs = {"resource": resource}

        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, **filter_kwargs)
        return obj


@login_required
def save_note(request):
    resource = request.POST.get('hash')
    if not resource:
        resource = request.POST.get('report_hash')
    content = request.POST.get('content')
    curr_user = request.user

    notes = Note.objects.filter(user=curr_user).filter(
                    status=Status.NORMAL).filter(resource=resource)
    try:
        if notes:
            note = notes[0]
            note.content = content
            note.save()
        else:
            note = Note()
            note.user = curr_user
            note.resource = resource
            note.content = content
            note.save()
        cache.clear()
        return JsonResponse(NoteSerializer(note).data)
    except Exception, e:
        return HttpResponse(None, 401)

