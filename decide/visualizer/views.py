from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404

from base import mods


class VisualizerView(TemplateView):
    template_name = 'visualizer/visualizer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})
            context['voting'] = r[0]
            
            #v = mods.get('store/stats', params={'voting_id': vid}) Este metodo es el que sustituira al json de prueba, falta que el equipo de store lo suba.
            v = {"numero_personas_censo": 23 , "numero_personas_votado": 20, "porcentaje_participacion": 98 ,"rango_menor_20": 5,"rango_entre_20_40": 10,"rango_entre_40_60": 3,"rango_mayor_60": 2,"edad_media": 43,"porcentaje_rango_menor_20": 23,"porcentaje_rango_entre_20_40": 48,"porcentaje_rango_entre_40_60": 11,"porcentaje_rango_mayor_60": 18,"numero_hombres": 12 ,"numero_mujeres": 13,"porcentaje_votos_hombres": 48,"porcentaje_votos_mujeres": 52}
            
            context['store'] = v

        except:
            raise Http404

        return context
