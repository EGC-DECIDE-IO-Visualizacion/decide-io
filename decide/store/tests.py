import datetime
import random
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from .models import Vote
from .serializers import VoteSerializer
from base import mods
from base.models import Auth
from base.tests import BaseTestCase
from census.models import Census
from mixnet.models import Key
from voting.models import Question
from voting.models import Voting

from store.models import Profile
import json

class StoreTextCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.question = Question(desc='qwerty')
        self.question.save()
        self.voting = Voting(pk=5001,
                             name='voting example',
                             question=self.question,
                             start_date=timezone.now(),
        )
        self.voting.save()

    def tearDown(self):
        super().tearDown()

    def gen_voting(self, pk):
        voting = Voting(pk=pk, name='v1', question=self.question, start_date=timezone.now(),
                end_date=timezone.now() + datetime.timedelta(days=1))
        voting.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def gen_votes(self):
        votings = [random.randint(1, 5000) for i in range(10)]
        users = [random.randint(3, 5002) for i in range(50)]
        for v in votings:
            a = random.randint(2, 500)
            b = random.randint(2, 500)
            self.gen_voting(v)
            random_user = random.choice(users)
            user = self.get_or_create_user(random_user)
            self.login(user=user.username)
            census = Census(voting_id=v, voter_id=random_user)
            census.save()
            data = {
                "voting": v,
                "voter": random_user,
                "vote": { "a": a, "b": b }
            }
            response = self.client.post('/store/', data, format='json')
            self.assertEqual(response.status_code, 200)

        self.logout()
        return votings, users

    def test_gen_vote_invalid(self):
        data = {
            "voting": 1,
            "voter": 1,
            "vote": { "a": 1, "b": 1 }
        }
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_store_vote(self):
        VOTING_PK = 345
        CTE_A = 96
        CTE_B = 184
        census = Census(voting_id=VOTING_PK, voter_id=1)
        census.save()
        self.gen_voting(VOTING_PK)
        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "vote": { "a": CTE_A, "b": CTE_B }
        }
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, VOTING_PK)
        self.assertEqual(Vote.objects.first().voter_id, 1)
        self.assertEqual(Vote.objects.first().a, CTE_A)
        self.assertEqual(Vote.objects.first().b, CTE_B)

    def test_vote(self):
        self.gen_votes()
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/', format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.count())
        self.assertEqual(votes[0], VoteSerializer(Vote.objects.all().first()).data)

    def test_filter(self):
        votings, voters = self.gen_votes()
        v = votings[0]

        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voting_id=v).count())

        v = voters[0]
        response = self.client.get('/store/?voter_id={}'.format(v), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), Vote.objects.filter(voter_id=v).count())

    def test_hasvote(self):
        votings, voters = self.gen_votes()
        vo = Vote.objects.first()
        v = vo.voting_id
        u = vo.voter_id

        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 401)

        self.login(user='noadmin')
        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 403)

        self.login()
        response = self.client.get('/store/?voting_id={}&voter_id={}'.format(v, u), format='json')
        self.assertEqual(response.status_code, 200)
        votes = response.json()

        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["voting_id"], v)
        self.assertEqual(votes[0]["voter_id"], u)

    def test_voting_status(self):
        data = {
            "voting": 5001,
            "voter": 1,
            "vote": { "a": 30, "b": 55 }
        }
        census = Census(voting_id=5001, voter_id=1)
        census.save()
        # not opened
        self.voting.start_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # not closed
        self.voting.start_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        self.voting.end_date = timezone.now() + datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        # closed
        self.voting.end_date = timezone.now() - datetime.timedelta(days=1)
        self.voting.save()
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 401)
    
    def test_stats(self):
        #Creating Profiles
        user1 = self.get_or_create_user(1)
        user2 = self.get_or_create_user(2)
        user3 = self.get_or_create_user(3)
        user4 = self.get_or_create_user(4)
        user5 = self.get_or_create_user(5)

        user1.profile.sexo = "F"
        user2.profile.sexo = "M"
        user3.profile.sexo = "M"
        user4.profile.sexo = "F"
        user5.profile.sexo = "F"

        user1.profile.lugar = "Sevilla"
        user2.profile.lugar = "Sevilla"
        user3.profile.lugar = "Madrid"
        user4.profile.lugar = "Barcelona"
        user5.profile.lugar = "Barcelona"

        user1.profile.fecha_nacimiento = datetime.datetime(1997, 4, 7)
        user2.profile.fecha_nacimiento = datetime.datetime(1985, 4, 7)
        user3.profile.fecha_nacimiento = datetime.datetime(1930, 4, 7)
        user4.profile.fecha_nacimiento = datetime.datetime(1992, 4, 7)
        user5.profile.fecha_nacimiento = datetime.datetime(1992, 4, 7)

        user1.save()
        user2.save()
        user3.save()
        user4.save()
        user5.save()

        users = [user1, user2, user3, user4]

        #Voting + Votes
        VOTING_PK = 345
        CTE_A = 96
        CTE_B = 184

        self.gen_voting(VOTING_PK)
        
        for user in users:
            census = Census(voting_id=VOTING_PK, voter_id=user.pk)
            census.save()

            data = {
                "voting": VOTING_PK,
                "voter": user.pk,
                "vote": { "a": CTE_A, "b": CTE_B }
            }

            self.login(user=user.username)
            response = self.client.post('/store/', data, format='json')
            self.assertEqual(response.status_code, 200)

        census = Census(voting_id=VOTING_PK, voter_id=user5.pk)
        census.save()

        #Testing API
        response = self.client.get('/store/stats/{}/'.format(VOTING_PK), format='json')
        self.assertEqual(response.status_code, 200)

        stats = json.loads(response.content)
        
        self.assertEqual(stats['numero_personas_censo'], 5)
        self.assertEqual(stats['numero_personas_votado'], 4)
        self.assertEqual(stats['porcentaje_participacion'], 0.8)
        self.assertEqual(stats['rango_menor_20'], 0)
        self.assertEqual(stats['rango_entre_20_40'], 4)
        self.assertEqual(stats['rango_entre_40_60'], 0)
        self.assertEqual(stats['rango_mayor_60'], 1)
        self.assertEqual(stats['edad_media'], 38.8)
        self.assertEqual(stats['porcentaje_rango_menor_20'], 0)
        self.assertEqual(stats['porcentaje_rango_entre_20_40'], 0.75)
        self.assertEqual(stats['porcentaje_rango_entre_40_60'], 0)
        self.assertEqual(stats['porcentaje_rango_mayor_60'], 1.0)
        self.assertEqual(stats['numero_hombres'], 2)
        self.assertEqual(stats['numero_mujeres'], 3)
        self.assertEqual(stats['porcentaje_votos_hombres'], 1.0)
        self.assertEqual(stats['porcentaje_votos_mujeres'], 2/3)
        self.assertEqual(stats['census_users_lugares_dict']['Sevilla'], 2)
        self.assertEqual(stats['census_users_lugares_dict']['Madrid'], 1)
        self.assertEqual(stats['census_users_lugares_dict']['Barcelona'], 2)
        self.assertEqual(stats['porcentaje_votes_users_lugares_dict']['Sevilla'], 1.0)
        self.assertEqual(stats['porcentaje_votes_users_lugares_dict']['Madrid'], 1.0)
        self.assertEqual(stats['porcentaje_votes_users_lugares_dict']['Barcelona'], 0.5)

        self.logout()

    def test_modify_vote(self):
        VOTING_PK = 603
        CTE_A1 = 20
        CTE_B1 = 50
        CTE_A2 = 40
        CTE_B2 = 90
        census = Census(voting_id=VOTING_PK, voter_id=1)
        census.save()
        self.gen_voting(VOTING_PK)
        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "vote": { "a": CTE_A1, "b": CTE_B1 }
        }
        user = self.get_or_create_user(1)
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, VOTING_PK)
        self.assertEqual(Vote.objects.first().voter_id, 1)
        self.assertEqual(Vote.objects.first().a, CTE_A1)
        self.assertEqual(Vote.objects.first().b, CTE_B1)

        self.logout()
        data = {
            "voting": VOTING_PK,
            "voter": 1,
            "vote": { "a": CTE_A2, "b": CTE_B2 }
        }
        self.login(user=user.username)
        response = self.client.post('/store/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 1)
        self.assertEqual(Vote.objects.first().voting_id, VOTING_PK)
        self.assertEqual(Vote.objects.first().voter_id, 1)
        self.assertEqual(Vote.objects.first().a, CTE_A2)
        self.assertEqual(Vote.objects.first().b, CTE_B2)

