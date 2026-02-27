from django.urls import path
from svc.views.customer import (CustomerCreateView,
                                CustomerDeleteView,
                                CustomerListView,
                                CustomerUpdateView, CustomerJobsView, CustomerJobDetailView,
                                )

customer_url_patterns = [
    path("customers", CustomerListView.as_view(), name="customers"),
    path("customers/add", CustomerCreateView.as_view(), name="add-customer"),
    path("edit/<int:pk>", CustomerUpdateView.as_view(), name="edit-customer"),
    path("delete/<int:pk>", CustomerDeleteView.as_view(), name="delete-customer"),
    path('customer/<int:pk>/jobs/', CustomerJobsView.as_view(), name='customer_jobs'),
    path('customer/<int:customer_pk>/job/<int:job_pk>', CustomerJobDetailView.as_view(), name="customer-job-detail"),

]
