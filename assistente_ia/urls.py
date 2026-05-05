from django.urls import path
from .views import ConsultaIAView, demo_ia

app_name = 'assistente_ia'

urlpatterns = [
    # A sua API protegida
    path('consultar/', ConsultaIAView.as_view(), name='consultar_db'),
    
    # A interface de demonstração visual
    path('demo/', demo_ia, name='demo_ui'),
]