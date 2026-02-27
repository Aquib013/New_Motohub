from django.urls import path
from svc.views.job.job import JobCreateView, JobListView, JobDetailView, JobUpdateView, generate_invoice, JobDeleteView, \
    search_customers, get_customer_details, create_customer
from svc.views.job.job_item import JobItemEditView, get_item_details
from svc.views.services import ServiceUpdateView, ServiceDeleteView
from svc.views.job.job_item import search_items, add_job_item_ajax, delete_job_item_ajax
from svc.views.services import add_service_ajax, delete_service_ajax

job_url_patterns = [
    path("jobs/create-job/", JobCreateView.as_view(), name="create_job"),
    path('search-customers/', search_customers, name='search_customers'),
    path('get-customer-details/', get_customer_details, name='get_customer_details'),
    path('create-customer/', create_customer, name='create_customer'),
    path("jobs/", JobListView.as_view(), name="jobs"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="job_detail"),
    path('service/<int:pk>/edit/', ServiceUpdateView.as_view(), name='edit_service'),
    path('service/<int:pk>/delete/', ServiceDeleteView.as_view(), name='delete_service'),
    path('job/item/<int:pk>/edit/', JobItemEditView.as_view(), name='edit-job-item'),
    path("jobs/<int:pk>/edit/", JobUpdateView.as_view(), name="job_edit"),
    path("jobs/<int:pk>/delete/", JobDeleteView.as_view(), name="job_delete"),
    path('jobs/<int:job_id>/invoice/', generate_invoice, name='generate_invoice'),
    path('api/item-details/', get_item_details, name='get_item_details'),

    path('api/search-items/', search_items, name='search_items'),
    path('api/job/<int:pk>/add-item/', add_job_item_ajax, name='add_job_item_ajax'),
    path('api/job-item/<int:pk>/delete/', delete_job_item_ajax, name='delete_job_item_ajax'),

    path('api/job/<int:pk>/add-service/', add_service_ajax, name='add_service_ajax'),
    path('api/service/<int:pk>/delete/', delete_service_ajax, name='delete_service_ajax'),
]
