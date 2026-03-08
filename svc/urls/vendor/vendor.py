from django.urls import path
from svc.views.vendor import (
    VendorListView,
    VendorCreateView,
    VendorUpdateView,
    VendorDeleteView,
    VendorHistoryView,
    VendorAddPaymentView,
    VendorEditPaymentView,
    VendorDeletePaymentView,
)

vendor_url_patterns = [
    path("vendors", VendorListView.as_view(), name="vendors"),
    path("vendors/add", VendorCreateView.as_view(), name="add_vendor"),
    path("vendor/edit/<int:pk>", VendorUpdateView.as_view(), name="edit_vendor"),
    path("vendor/delete/<int:pk>", VendorDeleteView.as_view(), name="delete_vendor"),
    path("vendors/<int:pk>/history/", VendorHistoryView.as_view(), name="vendor_history"),
    path("vendors/<int:pk>/payment/add/", VendorAddPaymentView.as_view(), name="vendor_add_payment"),
    path("vendors/<int:pk>/payment/<int:payment_pk>/edit/", VendorEditPaymentView.as_view(),
         name="vendor_edit_payment"),
    path("vendors/<int:pk>/payment/<int:payment_pk>/delete/", VendorDeletePaymentView.as_view(),
         name="vendor_delete_payment"),
]
