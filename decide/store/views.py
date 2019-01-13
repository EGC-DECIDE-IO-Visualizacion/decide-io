from django.utils import timezone
from django.utils.dateparse import parse_datetime
import django_filters.rest_framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics

from .models import Vote
from .serializers import VoteSerializer, VotingSerializer
from base import mods
from base.perms import UserIsStaff

from django.http import JsonResponse
from census.models import Census
from django.contrib.auth.models import User
from datetime import date


class StoreView(generics.ListAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('voting_id', 'voter_id')

    def get(self, request):
        self.permission_classes = (UserIsStaff,)
        self.check_permissions(request)
        return super().get(request)

    def post(self, request):
        """
         * voting: id
         * voter: id
         * vote: { "a": int, "b": int }
        """

        vid = request.data.get('voting')
        
        if not self.check_voting(vid):
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        uid = request.data.get('voter')
        vote = request.data.get('vote')

        if not vid or not uid or not vote:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        # validating voter
        token = request.auth.key
        if not self.check_voter(token, uid, vid):
            return Response({}, status=status.HTTP_401_UNAUTHORIZED)

        self.save_vote(vote, vid, uid)

        return  Response({})

    def check_voting(self, v_id):
        voting = mods.get('voting', params={'id': v_id})
        
        if not voting or not isinstance(voting, list):
            return False

        start_date = voting[0].get('start_date', None)
        end_date = voting[0].get('end_date', None)
        not_started = not start_date or timezone.now() < parse_datetime(start_date)
        is_closed = end_date and parse_datetime(end_date) < timezone.now()
        
        if not_started or is_closed:
            return False
        
        return True

    def check_voter(self, token, uid, vid):
        voter = mods.post('authentication', entry_point='/getuser/', json={'token': token})
        voter_id = voter.get('id', None)
        if not voter_id or voter_id != uid:
            return False

        # the user is in the census
        perms = mods.get('census/{}'.format(vid), params={'voter_id': uid}, response=True)
        if perms.status_code == 401:
            return False

        return True

    def save_vote(self, vote, vid, uid):
        a = vote.get("a")
        b = vote.get("b")

        defs = { "a": a, "b": b }
        v, _ = Vote.objects.get_or_create(voting_id=vid, voter_id=uid,
                                          defaults=defs)
        v.a = a
        v.b = b

        v.save()

        return  Response({})


class StatsView(generics.ListAPIView):
    serializer_class = VotingSerializer
    
    def get(self, request, voting_id):
        """
         * voting_id: id
        """

        census = Census.objects.filter(voting_id = voting_id)
        votes = Vote.objects.filter(voting_id = voting_id)

        census_users = User.objects.filter(id__in = census.values('voter_id')).select_related('profile')
        votes_users = User.objects.filter(id__in = votes.values('voter_id')).select_related('profile')

        # Numero de personas en el censo
        numero_personas_censo = len(census)

        # Numero de personas que ya han votado
        numero_personas_votado = len(votes)

        # Porcentaje de participacion
        porcentaje_participacion = numero_personas_votado/numero_personas_censo

        # Rango de edades del censo (<20, 20<40, 40<60, 60>)
        # Media de edad del censo
        # Porcentaje de votos por rangos de edad
        rango_menor_20 = 0
        rango_entre_20_40 = 0
        rango_entre_40_60 = 0
        rango_mayor_60 = 0
        numero_edad_nsnc = 0
        edad_total = 0
        
        # Numero de votantes por lugar
        census_users_lugares_dict = dict()

        # Numero de votantes masculinos
        numero_hombres = 0
        # Numero de votantes femeninos
        numero_mujeres = 0
        numero_sexo_nsnc = 0

        today = date.today()
        for census_user in census_users:
            if hasattr(census_user, 'profile'):
                fecha_nacimiento = census_user.profile.fecha_nacimiento
                if (fecha_nacimiento != None):
                    edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

                    edad_total += edad

                    if edad < 20:
                        rango_menor_20 += 1
                    elif edad >= 20 and edad < 40:
                        rango_entre_20_40 += 1
                    elif edad >= 40 and edad < 60:
                        rango_entre_40_60 += 1
                    elif edad >= 60:
                        rango_mayor_60 += 1

                else:
                    numero_edad_nsnc += 1

                if (census_user.profile.sexo != None and census_user.profile.sexo != ""):
                    if census_user.profile.sexo == 'M':
                        numero_hombres += 1
                    elif census_user.profile.sexo == 'F':
                        numero_mujeres += 1
                
                else:
                    numero_sexo_nsnc += 1

                lugar = census_user.profile.lugar
                if (lugar == None or lugar == ""):
                    lugar = 'NsNc'
                lugar_numero = 0
                if lugar in census_users_lugares_dict:
                    lugar_numero = census_users_lugares_dict[lugar]
                census_users_lugares_dict[lugar] = lugar_numero+1

            else:
                numero_edad_nsnc += 1
                numero_sexo_nsnc += 1
                lugar = 'NsNc'
                lugar_numero = 0
                if lugar in census_users_lugares_dict:
                    lugar_numero = census_users_lugares_dict[lugar]
                census_users_lugares_dict[lugar] = lugar_numero+1

        votado_rango_menor_20 = 0
        votado_rango_entre_20_40 = 0
        votado_rango_entre_40_60 = 0
        votado_rango_mayor_60 = 0
        votado_numero_edad_nsnc = 0

        # Porcentaje de participacion por lugar
        votes_users_lugares_dict = dict()

        # Porcentaje de participacion por sexo
        votes_hombres = 0
        votes_mujeres = 0
        votes_sexo_nsnc = 0

        for votes_user in votes_users:
            if hasattr(votes_user, 'profile'):
                fecha_nacimiento = votes_user.profile.fecha_nacimiento
                if (fecha_nacimiento != None):
                    edad = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

                    if edad < 20:
                        votado_rango_menor_20 += 1
                    elif edad >= 20 and edad < 40:
                        votado_rango_entre_20_40 += 1
                    elif edad >= 40 and edad < 60:
                        votado_rango_entre_40_60 += 1
                    elif edad >= 60:
                        votado_rango_mayor_60 += 1

                else:
                    votado_numero_edad_nsnc += 1

                if (votes_user.profile.sexo != None and votes_user.profile.sexo != ""):
                    if votes_user.profile.sexo == 'M':
                        votes_hombres += 1
                    elif votes_user.profile.sexo == 'F':
                        votes_mujeres += 1

                else:
                    votes_sexo_nsnc += 1

                lugar = votes_user.profile.lugar
                if (lugar == None or lugar == ""):
                    lugar = 'NsNc'
                lugar_numero = 0
                if lugar in votes_users_lugares_dict:
                    lugar_numero = votes_users_lugares_dict[lugar]
                votes_users_lugares_dict[lugar] = lugar_numero+1

            else:
                votado_numero_edad_nsnc += 1
                votes_sexo_nsnc += 1
                lugar = 'NsNc'
                lugar_numero = 0
                if lugar in votes_users_lugares_dict:
                    lugar_numero = votes_users_lugares_dict[lugar]
                votes_users_lugares_dict[lugar] = lugar_numero+1

        if (numero_personas_censo-numero_edad_nsnc != 0):
            edad_media = edad_total/(numero_personas_censo-numero_edad_nsnc)
        else:
            edad_media = 0

        if (rango_menor_20 > 0):
            porcentaje_rango_menor_20 = votado_rango_menor_20/rango_menor_20
        else:
            porcentaje_rango_menor_20 = 0
        if (rango_entre_20_40 > 0):
            porcentaje_rango_entre_20_40 = votado_rango_entre_20_40/rango_entre_20_40
        else:
            porcentaje_rango_entre_20_40 = 0
        if (rango_entre_40_60 > 0):
            porcentaje_rango_entre_40_60 = votado_rango_entre_40_60/rango_entre_40_60
        else:
            porcentaje_rango_entre_40_60 = 0
        if (rango_mayor_60 > 0):
            porcentaje_rango_mayor_60 = votado_rango_mayor_60/rango_mayor_60
        else:
            porcentaje_rango_mayor_60 = 0
        if (numero_edad_nsnc > 0):
            porcentaje_edad_nsnc = votado_numero_edad_nsnc/numero_edad_nsnc
        else:
            porcentaje_edad_nsnc = 0

        # Porcentaje votos sexo
        if (numero_hombres > 0):
            porcentaje_votos_hombres = votes_hombres/numero_hombres
        else:
            porcentaje_votos_hombres = 0
        if (numero_mujeres > 0):
            porcentaje_votos_mujeres = votes_mujeres/numero_mujeres
        else:
            porcentaje_votos_mujeres = 0
        if (numero_sexo_nsnc > 0):
            porcentaje_sexo_nsnc = votes_sexo_nsnc/numero_sexo_nsnc
        else:
            porcentaje_sexo_nsnc = 0   

        # Porcentaje de participacion por lugar
        porcentaje_votes_users_lugares_dict = dict()
        for key, value in census_users_lugares_dict.items():
            if key in votes_users_lugares_dict:
                porcentaje_votes_users_lugares_dict[key] = votes_users_lugares_dict[key]/value
            else:
                porcentaje_votes_users_lugares_dict[key] = 0

        jsonResponse = {
            "numero_personas_censo": numero_personas_censo,
            "numero_personas_votado": numero_personas_votado,
            "porcentaje_participacion": porcentaje_participacion,
            "rango_menor_20": rango_menor_20,
            "rango_entre_20_40": rango_entre_20_40,
            "rango_entre_40_60": rango_entre_40_60,
            "rango_mayor_60": rango_mayor_60,
            "numero_edad_nsnc": numero_edad_nsnc,
            "edad_media": edad_media,
            "porcentaje_rango_menor_20": porcentaje_rango_menor_20,
            "porcentaje_rango_entre_20_40": porcentaje_rango_entre_20_40,
            "porcentaje_rango_entre_40_60": porcentaje_rango_entre_40_60,
            "porcentaje_rango_mayor_60": porcentaje_rango_mayor_60,
            "porcentaje_edad_nsnc": porcentaje_edad_nsnc,
            "numero_hombres": numero_hombres,
            "numero_mujeres": numero_mujeres,
            "numero_sexo_nsnc": numero_sexo_nsnc,
            "porcentaje_votos_hombres": porcentaje_votos_hombres,
            "porcentaje_votos_mujeres": porcentaje_votos_mujeres,
            "porcentaje_sexo_nsnc": porcentaje_sexo_nsnc,
            "census_users_lugares_dict": census_users_lugares_dict,
            "porcentaje_votes_users_lugares_dict": porcentaje_votes_users_lugares_dict
        }

        return JsonResponse(jsonResponse)
