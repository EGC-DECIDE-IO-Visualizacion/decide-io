from django.contrib import admin

from .models import Vote
from .models import Profile


admin.site.register(Vote)
admin.site.register(Profile)