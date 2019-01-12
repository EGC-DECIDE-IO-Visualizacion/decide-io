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
            context['update'] = update
        except:
            raise Http404

        return context
