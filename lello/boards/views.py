import datetime
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import Http404

from boards.models import Board, List, Card, Label
from boards.serializers import BoardSerializer, ListSerializer, CardSerializer, LabelSerializer
from users.permissions import APIPermissionClassFactory
from audits.models import Audit
from calendars.models import Event


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='BoardPermission',
            permission_configuration={
                'base': {
                    'create': True,
                    'list': True,
                },
                'instance': {
                    'retrieve': True,
                    'update': True,
                    'partial_update': True,
                    'destroy': True,
                    'lists': True,
                }
            }
        ),
    )

    def create(self, request):
        # print(request.data)
        Audit.objects.create(
            httpMethod = request.method,
            url = '/boards/',
            user = request.user
        )
        return super().create(request)

    # def perform_create(self, serializer):
    #     user = self.request.user
    #     team = serializer.validated_data['team']
    #     print(serializer)
    #     board = serializer.save()

    #     return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            Audit.objects.create(
                httpMethod = request.method,
                url = '/boards/{}'.format(kwargs['pk']),
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

class ListViewSet(viewsets.ModelViewSet):
    queryset = List.objects.all()
    serializer_class = ListSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='ListPermission',
            permission_configuration={
                'base': {
                    'create': True,
                    'list': True,
                },
                'instance': {
                    'retrieve': True,
                    'update': True,
                    'partial_update': True,
                    'destroy': True,
                    'cards': True,
                }
            }
        ),
    )

    def create(self, request):
        Audit.objects.create(
            httpMethod = request.method,
            url = '/lists/',
            user = request.user
        )
        return super().create(request)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            Audit.objects.create(
                httpMethod = request.method,
                url = '/lists/{}'.format(kwargs['pk']),
                user = request.user
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
                    'create': True,
                    'list': True,
                },
                'instance': {
                    'retrieve': True,
                    'update': True,
                    'partial_update': True,
                    'destroy': True,
                }
            }
        ),
    )

    def create(self, request):
        lista = List.objects.get(pk = request.data["lista"])
        # tablero = Board.objects.select_related('board').get(lista.id)
        tablero = lista.board
        # tablero = lista.board_set.all()[0]
        calendario = tablero.calendar_set.all()[0]
        print(calendario)
        Audit.objects.create(
            httpMethod = request.method,
            url = '/cards/',
            user = request.user
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
                url = '/cards/{}'.format(kwargs['pk']),
                user = request.user
            )
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = (
        APIPermissionClassFactory(
            name='LabelPermission',
            permission_configuration={
                'base': {
                    'create': True,
                    'list': True,
                },
                'instance': {
                    'retrieve': True,
                    'update': True,
                    'partial_update': True,
                    'destroy': True,
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
                url = '/labels/{}'.format(kwargs['pk']),
                user = request.user
            )
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)
