from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task, Benefactor, Charity
from charities.serializers import (
    TaskSerializer, CharitySerializer, BenefactorSerializer
)


class BenefactorRegistration(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BenefactorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CharityRegistration(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CharitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)

class TaskRequest(APIView):
    permission_classes = [IsAuthenticated, IsBenefactor]

    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)

        if task.state != 'P':
            return Response({'detail': 'This task is not pending.'}, status=status.HTTP_404_NOT_FOUND)

        task.state = 'W'
        task.assigned_benefactor = request.user.benefactor
        task.save()

        return Response({'detail': 'Request sent.'}, status=status.HTTP_200_OK)


class TaskResponse(APIView):
    permission_classes = (IsAuthenticated, IsCharityOwner)

    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        response = request.data.get('response')

        if response not in ['A', 'R']:
            msg = 'Required field ("A" for accepted / "R" for rejected)'
            return Response(data={'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

        if task.state != Task.TaskStatus.WAITING:
            msg = 'This task is not waiting.'
            return Response(data={'detail': msg}, status=status.HTTP_404_NOT_FOUND)

        task.response_to_benefactor_request(response)
        return Response(data={'detail': 'Response sent.'}, status=status.HTTP_200_OK)


class DoneTask(APIView):
    permission_classes = (IsAuthenticated, IsCharityOwner)

    def post(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)

        if task.state != Task.TaskStatus.ASSIGNED:
            msg = 'Task is not assigned yet.'
            return Response(data={'detail': msg}, status=status.HTTP_404_NOT_FOUND)

        task.state = Task.TaskStatus.DONE
        task.save()
        return Response(data={'detail': 'Task has been done successfully.'}, status=status.HTTP_200_OK)
