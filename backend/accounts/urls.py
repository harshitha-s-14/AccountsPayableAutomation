from django.urls import path

from .views import (
    LoginView, LogoutView, CurrentUserView,
    InvoiceUploadView,
    InvoiceListView,
    InvoiceOCRView,
    POMatchingView,
    CreateApprovalView,
    ApprovalActionView,
    VendorListCreateView,
    CreatePaymentView,
    PaymentListView,
    PaymentStatusUpdateView,
    DashboardSummaryView,
    ReportsView,
    ApprovalListView,
    BulkInvoiceUploadView,
    EmailInvoiceIngestionView,
    PurchaseOrderListCreateView,
    GoodsReceiptNoteListCreateView,
    ApprovalRuleListCreateView,
    ApprovalRuleDetailView,
    EmployeeUserListCreateView,
    EmployeeUserDetailView,
    ApprovalHistoryView,
    PaymentAdviceView,
    InvoiceTaxValidationView,
    VendorDetailView,
)

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', CurrentUserView.as_view(), name='auth-me'),
    path('employees/', EmployeeUserListCreateView.as_view(), name='employee-list-create'),
    path('employees/<int:pk>/', EmployeeUserDetailView.as_view(), name='employee-detail'),
    path('upload/', InvoiceUploadView.as_view(), name='invoice-upload'),

    path('list/', InvoiceListView.as_view(), name='invoice-list'),

    path('<int:invoice_id>/ocr/', InvoiceOCRView.as_view(), name='invoice-ocr'),

    path('<int:invoice_id>/match-po/', POMatchingView.as_view(), name='po-matching'),

    path('<int:invoice_id>/approval/', CreateApprovalView.as_view(), name='create-approval'),

    path('approvals/<int:approval_id>/action/', ApprovalActionView.as_view(), name='approval-action'),

    path('vendors/', VendorListCreateView.as_view(), name='vendor-list-create'),

    path('<int:invoice_id>/payment/', CreatePaymentView.as_view(), name='create-payment'),

    path('payments/', PaymentListView.as_view(), name='payment-list'),

    path('payments/<int:payment_id>/status/', PaymentStatusUpdateView.as_view(), name='payment-status-update'),

    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard-summary'),

    path('reports/', ReportsView.as_view(), name='reports'),

    path('approvals/', ApprovalListView.as_view(), name='approval-list'),

    path('bulk-upload/', BulkInvoiceUploadView.as_view(), name='bulk-invoice-upload'),

    path('email-ingestion/', EmailInvoiceIngestionView.as_view(), name='email-invoice-ingestion'),

    path('purchase-orders/', PurchaseOrderListCreateView.as_view(), name='purchase-order-list-create'),
    path('grns/', GoodsReceiptNoteListCreateView.as_view(), name='grn-list-create'),

    path('approval-rules/', ApprovalRuleListCreateView.as_view(), name='approval-rule-list-create'),

    path('approval-rules/<int:pk>/', ApprovalRuleDetailView.as_view(), name='approval-rule-detail'),
    
    path('invoices/<int:invoice_id>/approval-history/',ApprovalHistoryView.as_view(),name='approval-history'),

    path('payments/<int:payment_id>/advice/',PaymentAdviceView.as_view(),name='payment-advice'),

    path( 'invoices/<int:invoice_id>/tax-validation/',InvoiceTaxValidationView.as_view(),name='invoice-tax-validation'),

    path('vendors/<int:pk>/',VendorDetailView.as_view(),name='vendor-detail'),
]