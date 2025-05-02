# game/urls.py

from django.urls import path
from . import views # Importa las vistas desde el mismo directorio

app_name = 'game' # Namespace para evitar conflictos de nombres de URL

urlpatterns = [
    path('', views.index, name='index'), # Página principal (muestra formulario y/o juego)
    path('new/', views.create_game, name='create_game'), # Maneja la creación
    # path('<int:game_id>/', views.game_view, name='game_detail'), # Opcional, ya no es principal
    path('<int:game_id>/move/', views.make_move, name='make_move'), # Para los movimientos AJAX
    path('<int:game_id>/legal_moves/', views.get_legal_moves_view, name='get_legal_moves'),
]