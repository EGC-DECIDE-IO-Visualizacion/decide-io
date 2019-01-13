from django.test import TestCase

# import random
# import itertools
# from django.utils import timezone
# from django.conf import settings
# from django.contrib.auth.models import User
# from django.test import TestCase
# from rest_framework.test import APIClient
# from rest_framework.test import APITestCase

# from base import mods
# from base.tests import BaseTestCase
# from census.models import Census
# from mixnet.mixcrypt import ElGamal
# from mixnet.mixcrypt import MixCrypt
# from mixnet.models import Auth
# from voting.models import Voting, Question, QuestionOption
# from visualizer.views import VisualizerView

# # Create your tests here.

# class ArrangeVotesTestCase(BaseTestCase):

#     def test_arrange_votes(self):
#         #primero creamos una votacion

#         q = Question(desc='test question')
#         q.save()
#         for i in range(3):
#             opt = QuestionOption(question=q, option='option {}'.format(i+1))
#             opt.save()
#         v = Voting(name='test voting', question=q)
#         v.save()

#         a, _ = Auth.objects.get_or_create(url=settings.BASEURL, defaults={'me': True, 'name': 'test auth'})
#         a.save()
#         v.auths.add(a)

#         #pasamos el voting a "modo diccionario"

#         kwargs = {'voting_id' : v.id}

#         context = super().get_context_data(**kwargs)
#         vid = kwargs.get('voting_id', 0)

#         r = mods.get('voting', params={'id': vid})
#         context['voting'] = r[0]

#         #suponemos que la votacion es de tipo 'prioridad' y que 
#         #para sus opciones se han votado 4 veces unas prioridades aleatorias
#         context['voting']['type_of_voting']='priority'

#         for option in context['voting']['options']:
#             option['priotities'] = [random.randint(1,4), random.randint(1,4), random.randint(1,4), random.randint(1,4)]
        
#         #print antes de ordenarlos
#         print('----ANTES----')
#         print(context['voting']['options'])

#         #probamos el metodo arrange_votes

#         VisualizerView.arrange_votes(v)
#         #print despues de ordenarlos
#         print('----DESPUES----')
#         print(context['voting']['options'])
    

class MoreStatsAPIVotingTestCase(BaseTestCase):

    def test_create_voting(self):

        #primero creamos una votacion
        q = Question(desc='test question')
        q.save()
        for i in range(3):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        v = Voting(name='test voting', question=q)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL, defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)
        return v

    def test_API_store_And_visualizer(self):
        voting = self.test_create_voting()
        # Inicializamos la votacion
        voting.create_pubkey()
        voting.start_date = timezone.now()
        voting.save()

        #Comprobamos que la llamada a la API de store funciona
        response = self.client.get('/store/stats/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
       
        #Comprobamos que el visualizer recibe el json que se optione al realizar la llamada a la API
        response = self.client.get('/visualizer/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response.json(), 'store')

# class UpdateVotingTestCase(BaseTestCase):

#     def test_create_voting(self):
#
#         #primero creamos una votacion

#         q = Question(desc='test question')
#         q.save()
#         for i in range(3):
#             opt = QuestionOption(question=q, option='option {}'.format(i+1))
#             opt.save()
#         v = Voting(name='test voting', question=q)
#         v.save()

#         a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
#                                            defaults={'me': True, 'name': 'test auth'})
#         a.save()
#         v.auths.add(a)

#         return v
#
#     def test_Update_voting(self):
#         voting = self.test_create_voting()
#         # Inicializamos la votacion
#
#         voting.create_pubkey()
#         voting.start_date = timezone.now()
#         voting.save()
#
#         #Comprobamos que el visualizer se muestra correctamente despues de updatear la votacion
#         #El visualizer deberia mostrar la tabla de resultados todo a 0 en y no vacia
#         response = self.client.get('/visualizer/{}/'.format(voting.pk), data, format='json')
#         self.assertEqual(response.status_code, 200)
#         
#         #Compruebo que el voting esta actualizado
#         jsonfile =  response.json()
#         votingJson = jsonfile['voting']
#         self.assertEqual(votingJson['postproc'][0]['votes'], 0)       
