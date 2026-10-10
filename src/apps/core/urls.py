from django.urls import path
from . import views, demo_views

app_name = 'core'

urlpatterns = [
    path('demo/', demo_views.demo, name='demo'),
    path('api/demo/analyze/', demo_views.analyze, name='demo_analyze'),
    path('api/demo/report/', demo_views.report, name='demo_report'),
    path('api/health/', demo_views.health, name='health'),
    path('',        views.index,          name='index'),
    path('contact/', views.contact_submit, name='contact_submit'),
]
