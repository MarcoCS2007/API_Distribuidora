from .views import CadastrarUsuarioView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UsuarioBaseViewSet, PerfilGestorViewSet, PerfilRepresentanteViewSet, CadastrarUsuarioView

app_name = 'usuarios'

router = DefaultRouter()
router.register(r'usuarios', UsuarioBaseViewSet)
router.register(r'gestores', PerfilGestorViewSet)
router.register(r'representantes', PerfilRepresentanteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cadastro/', CadastrarUsuarioView.as_view(), name='cadastro'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='login_refresh'),
]