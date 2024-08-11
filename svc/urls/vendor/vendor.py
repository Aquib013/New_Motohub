from django.urls import path
from svc.views.vendor import (
    VendorListView,
    VendorCreateView, VendorUpdateView, VendorDeleteView, VendorPaymentHistoryView,
    VendorPurchaseOrdersView, VendorPurchaseOrderDetailView)

vendor_url_patterns = [
    path("vendors", VendorListView.as_view(), name="vendors"),
    path("vendors/add", VendorCreateView.as_view(), name="add_vendor"),
    path("vendor/edit/<int:pk>", VendorUpdateView.as_view(), name="edit_vendor"),
    path("vendor/delete/<int:pk>", VendorDeleteView.as_view(), name="delete_vendor"),
    path("vendor/<int:pk>/payments", VendorPaymentHistoryView.as_view(), name="vendor-payment-history"),
    path('vendor/<int:pk>/pos/', VendorPurchaseOrdersView.as_view(), name='vendor-purchase-orders'),
    path('vendor/<int:vendor_pk>/po/<int:po_pk>', VendorPurchaseOrderDetailView.as_view(),
         name='vendor-po-detail'),
]
