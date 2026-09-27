from django.urls import path
from api import views

urlpatterns = [
    path("", views.home),
    path("api/products", views.products),
    path("api/search", views.search),
    path("api/options", views.options),
    path("api/track", views.track),
    path("api/untrack", views.untrack),
    path("api/history", views.history),
    path("api/scrape-now", views.scrape_now),
    path("api/export.csv", views.export_csv),
]
