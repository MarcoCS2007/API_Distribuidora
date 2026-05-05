from django.urls import path
from .views import ConsultaIAView

app_name = 'assistente_ia'

urlpatterns = [
    path('consultar/', ConsultaIAView.as_view(), name='consultar_db'),
]