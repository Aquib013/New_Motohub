from django.urls import path
from svc.views.job.job import JobCreateView, JobListView, JobDetailView, JobUpdateView, generate_invoice, JobDeleteView, \
    get_customers
from svc.views.job.job_item import JobItemAddView, JobItemEditView, JobItemDeleteView
from svc.views.services import ServiceCreateView, ServiceUpdateView, ServiceDeleteView

job_url_patterns = [
    path("jobs/create-job/", JobCreateView.as_view(), name="create_job"),
    path('get-customers/', get_customers, name='get-customers'),
    path('job/<int:pk>/add-service/', ServiceCreateView.as_view(), name='add_service'),
    path("jobs/", JobListView.as_view(), name="jobs"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="job_detail"),
    path('service/<int:pk>/edit/', ServiceUpdateView.as_view(), name='edit_service'),
    path('service/<int:pk>/delete/', ServiceDeleteView.as_view(), name='delete_service'),
    path('job/<int:pk>/item-add/', JobItemAddView.as_view(), name='add-job-item'),
    path('job/item/<int:pk>/edit/', JobItemEditView.as_view(), name='edit-job-item'),
    path('job/item/<int:pk>/delete/', JobItemDeleteView.as_view(), name='delete-job-item'),
    path("jobs/<int:pk>/edit/", JobUpdateView.as_view(), name="job_edit"),
    path("jobs/<int:pk>/delete/", JobDeleteView.as_view(), name="job_delete"),
    path('jobs/<int:job_id>/invoice/', generate_invoice, name='generate_invoice'),
]
