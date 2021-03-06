import datetime
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import Http404
from django.core.mail import send_mail
from guardian.shortcuts import assign_perm
from django.core.exceptions import ObjectDoesNotExist

from boards.models import Board, List, Card, Label
from boards.serializers import BoardSerializer, ListSerializer, CardSerializer, LabelSerializer
from users.permissions import APIPermissionClassFactory
from audits.models import Audit
from audits.serializers import AuditSerializer
from notifications.models import Notification
from calendars.models import Event
from calendars.serializers import EventSerializer
from checklists.serializers import ElementSerializer


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='BoardPermission',
            permission_configuration={
                'base': {
                    'create': lambda user, req: user.is_authenticated,
                    'list': False,
                },
                'instance': {
                    'retrieve': lambda user, obj, req: user.is_authenticated,
                    'update': lambda user, obj, req: user.is_authenticated,
                    'partial_update': lambda user, obj, req: user.is_authenticated,
                    'destroy': 'boards.delete_board',
                    'lists': lambda user, obj, req: user.is_authenticated,
                    'audits': lambda user, obj, req: user.is_authenticated,
                    'calendar_events': lambda user, obj, req: user.is_authenticated,
                }
            }
        ),
    )

    def perform_create(self, serializer):
        user = self.request.user
        board = serializer.save()
        assign_perm('boards.delete_board', user, board)
        Audit.objects.create(
            httpMethod = self.request.method,
            url = '/boards/',
            user = user
        )
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            Audit.objects.create(
                httpMethod = request.method,
                url = '/boards/{}/'.format(kwargs['pk']),
                user = request.user
            )
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def lists(self, request, pk=None):
        board = self.get_object()
        lists = board.list_set.all()

        return Response(
            [ListSerializer(lista).data for lista in lists]
        )

    @action(detail=True, methods=['get'])
    def audits(self, request, pk=None):
        board = self.get_object()
        lists = board.list_set.all()

        audits = Audit.objects.filter(
            url = '/boards/{}/'.format(board.id)
        )

        for lista in lists:
            audits = audits.union(Audit.objects.filter(
                url = '/lists/{}/'.format(lista.id)
            ))

            for card in lista.card_set.all():
                audits = audits.union(Audit.objects.filter(
                    url = '/cards/{}/'.format(card.id)
                ))

        audits = audits.union(board.audit_set.all())
        print(audits)

        return Response(
            [AuditSerializer(audit).data for audit in audits]
        )

    @action(detail=True, url_path='calendar-events', methods=['get'])
    def calendar_events(self, request, pk=None):
        board = self.get_object()
        calendar = board.calendar
        events = calendar.event_set.all()
        
        return Response(
            [EventSerializer(event).data for event in events]
        )

class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='ListPermission',
            permission_configuration={
                'base': {
                    'create': lambda user, req: user.is_authenticated,
                    'list': False,
                },
                'instance': {
                    'retrieve': lambda user, obj, req: user.is_authenticated,
                    'update': lambda user, obj, req: user.is_authenticated,
                    'partial_update': lambda user, obj, req: user.is_authenticated,
                    'destroy': lambda user, obj, req: user.is_authenticated,
                    'cards': lambda user, obj, req: user.is_authenticated,
                }
            }
        ),
    )

    def create(self, request):
        board = Board.objects.get(pk = request.data['board'])
        Audit.objects.create(
            httpMethod = request.method,
            url = '/lists/',
            user = request.user,
            board = board
        )
        Notification.objects.create(
            title = "Nueva lista!",
            description = "Tu nueva lista se llama {}".format(request.data['name']),
            transmitter = request.user,
            receiver = board.owner
        )
        return super().create(request)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            board = instance.board
            self.perform_destroy(instance)
            Audit.objects.create(
                httpMethod = request.method,
                url = '/lists/{}/'.format(kwargs['pk']),
                user = request.user,
                board = board
            )
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def cards(self, request, pk=None):
        lista = self.get_object()
        cards = lista.card_set.all()

        return Response(
            [CardSerializer(card).data for card in cards]
        )

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='CardPermission',
            permission_configuration={
                'base': {
                    'create': lambda user, req: user.is_authenticated,
                    'list': False,
                },
                'instance': {
                    'retrieve': lambda user, obj, req: user.is_authenticated,
                    'update': lambda user, obj, req: user.is_authenticated,
                    'partial_update': lambda user, obj, req: user.is_authenticated,
                    'destroy': lambda user, obj, req: user.is_authenticated,
                    'checklist': lambda user, obj, req: user.is_authenticated,
                }
            }
        ),
    )

    def create(self, request):
        lista = List.objects.get(pk = request.data["lista"])
        # tablero = Board.objects.select_related('board').get(lista.id)
        tablero = lista.board
        # tablero = lista.board_set.all()[0]
        calendario = tablero.calendar
        Audit.objects.create(
            httpMethod = request.method,
            url = '/cards/',
            user = request.user,
            board = tablero
        )
        lista = List.objects.get(pk = request.data['lista'])
        board = Board.objects.get(pk = lista.board.id)
        Notification.objects.create(
            title = "Nueva Card!",
            description = "La nueva card se llama {}".format(request.data['title']),
            transmitter = request.user,
            receiver = board.owner
        )
        Event.objects.create(
            calendar = calendario,
            title = 'Nueva tarjeta: {}'.format(request.data["title"]),
            description = 'Tarjeta creada por: {}, {}, {}, {}'.format(request.user.username, lista.id, tablero.id, calendario.id),
            date = datetime.datetime.now()
        )
        return super().create(request)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            Audit.objects.create(
                httpMethod = request.method,
                url = '/cards/{}/'.format(kwargs['pk']),
                user = request.user
            )
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def checklist(self, request, pk=None):
        card = self.get_object()
        try:        
            checklist = card.checklist
            elements = checklist.element_set.all()
            return Response({
                'id': checklist.id,
                'name': checklist.name,
                'elements': [ElementSerializer(element).data for element in elements]
            })
        except ObjectDoesNotExist:
            return Response([])


class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='LabelPermission',
            permission_configuration={
                'base': {
                    'create': lambda user, req: user.is_authenticated,
                    'list': False,
                },
                'instance': {
                    'retrieve': lambda user, obj, req: user.is_authenticated,
                    'update': lambda user, obj, req: user.is_authenticated,
                    'partial_update': lambda user, obj, req: user.is_authenticated,
                    'destroy': lambda user, obj, req: user.is_authenticated,
                }
            }
        ),
    )

    def create(self, request):
        Audit.objects.create(
            httpMethod = request.method,
            url = '/labels/',
            user = request.user
        )
        return super().create(request)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            Audit.objects.create(
                httpMethod = request.method,
                url = '/labels/{}/'.format(kwargs['pk']),
                user = request.user
            )
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)
