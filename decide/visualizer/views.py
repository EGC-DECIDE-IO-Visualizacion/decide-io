from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404

from base import mods
from datetime import datetime

# Se ha tenido que implementar un metodo de ejemplo, el equipo del modulo Voting, no ha podido realizar el metodo "tally", que actualiza el recuento de los votos 
def updateVotingExample(voting_id):
    text = "La votacion con el ID: %d se ha actualizado el {:%B %d, %Y}".format(datetime.now()) %voting_id

    return text
    
    

class VisualizerView(TemplateView):
    template_name = 'visualizer/visualizer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})
            update = updateVotingExample(vid)
            
            context['voting'] = r[0]
            context['voting']['type_of_voting']='normal' #<------ codigo temporal para evitar excepciones 
            
            v = mods.get('store/stats/{}'.format(vid))
            context['store'] = v

            context['update'] = update
        except:
            raise Http404
            
        #codigo temporal a la espera del modulo de voting
        if context['voting']['type_of_voting'] == 'priority':
            self.arrange_votes(context['voting'])
        

        return context

    #codigo temporal a la espera del modulo de voting
#metodo que ordena las opciones de una votacion segun la preferencia que se le ha dado

    def arrange_votes(self, voting):
    #(suponiendo que una option contiene una coleccion de prioridades que se le ha dado en cada votacion y una votacion tiene un atributo llamado 'type_of_voting' que indica que tipo de votacion es)
        question = voting['question']    #-pregunta de la votacion
        options = question['options']  #-opciones de la pregunta
        sum_priorities = []         #-lista donde se sumaran las prioridades que se les ha dado a cada opcion
        arranged_options = []       #-lista a devolver de las opciones ordenadas por prioridad

        for option in options:
            sum_priorities.append(sum(option['priorities']))       #-por cada opcion se le suma las prioridades y el resultado se añade a la lista sum_priorities
                                                                #-de este modo el indice de la opcion en options es el mismo que el de la suma de sus prioridades en sum_priorities
        
        for i in range(0,len(options)):                     #-desde 0 hasta el nº de opciones
            if sum_priorities[i] == min(sum_priorities):    #-si la suma de prioridades de la opción con indice i es el valor minimo (es la opcion mas prioritaria)
                options[i]['number'] == i+1                 #-cambiamos el atributo 'number' de la opcion para que coincidan con el orden en el que se van a ordenar
                arranged_options.append(options[i])         #-la opcion que comparte indice i con dicha suma se añade a arranged_options
                sum_priorities[i]=999999                    #-a dicha suma se le cambia el valor a 999999 para que en las 
                                                            #siguientes iteraciones no vuelva a salir que es el valor 
                                                            #minimo. No se elimina de la lista para no alterar los indices
                                                            #de las listas

        question['options'] = arranged_options     #la lista de opciones de question se reemplaza por la lista de las opciones ordenadas
        voting['question'] = question           #la pregunta correspondiente del voting se reemplaza por la que tiene las opciones ordenadas

