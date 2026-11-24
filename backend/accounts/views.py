from django.db import transaction

from django.utils import timezone
from .models import AuditLog, OCRExtraction


from django.db.models import Sum

import uuid
from .models import Payment
from .serializers import PaymentSerializer

from .models import Vendor
from .serializers import VendorSerializer

from .models import ApprovalRule, ApprovalRequest, ApprovalAction, AuditLog

from .models import PurchaseOrder, GoodsReceiptNote
from .matching_service import perform_po_matching

from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Invoice, InvoiceLineItem
from .serializers import (
    InvoiceSerializer,
    ApprovalRequestSerializer,
    PaymentSerializer,
    PurchaseOrderSerializer,
    GoodsReceiptNoteSerializer,
    ApprovalRuleSerializer,
    EmployeeUserSerializer
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import OCRExtraction
from .ocr_service import extract_text_from_invoice, extract_invoice_fields


from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import (
    IsAdmin,
    IsAPClerk,
    IsApprover,
    IsFinance,
    IsVendorManager,
    IsManager,
    IsAPClerkOrApprover,
    IsAPClerkOrFinance,
    IsAllEmployees,
)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'error': 'This account is inactive.'}, status=status.HTTP_403_FORBIDDEN)
        token, _ = Token.objects.get_or_create(user=user)
        groups = list(user.groups.values_list('name', flat=True))
        role = 'Admin' if user.is_superuser else (groups[0] if groups else 'Unassigned')
        return Response({
            'token': token.key,
            'user': {'id': user.id, 'username': user.username, 'email': user.email,
                     'first_name': user.first_name, 'last_name': user.last_name,
                     'role': role, 'is_staff': user.is_staff}
        })


class LogoutView(APIView):
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    def get(self, request):
        user = request.user
        groups = list(user.groups.values_list('name', flat=True))
        role = 'Admin' if user.is_superuser else (groups[0] if groups else 'Unassigned')
        return Response({'id': user.id, 'username': user.username, 'email': user.email,
                         'first_name': user.first_name, 'last_name': user.last_name,
                         'role': role, 'is_staff': user.is_staff})




class InvoiceUploadView(generics.CreateAPIView):

    permission_classes = [IsAPClerk]

    queryset = Invoice.objects.all()

    serializer_class = InvoiceSerializer

    parser_classes = [MultiPartParser, FormParser]
class InvoiceListView(generics.ListAPIView):
     
    permission_classes = [IsAllEmployees]

    queryset = Invoice.objects.all().order_by('-uploaded_at')

    serializer_class = InvoiceSerializer

class InvoiceOCRView(APIView):

    permission_classes = [IsAPClerk]

    def post(self, request, invoice_id):

        try:
            invoice = Invoice.objects.get(id=invoice_id)

            if not invoice.invoice_file:
                return Response(
                    {'error': 'Invoice file is missing.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_path = invoice.invoice_file.path

            extracted_text = extract_text_from_invoice(file_path)

            if not extracted_text.strip():
                return Response(
                    {'error': 'No readable text found in invoice.'},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

            extracted_data = extract_invoice_fields(extracted_text)

            line_items = extracted_data.get('line_items', [])
            warnings = extracted_data.get('extraction_warnings', [])

            extraction_status = (
                'COMPLETED' if not warnings else 'REVIEW_REQUIRED'
            )

            new_line_items = []

            for item in line_items:

                new_line_items.append(
                    InvoiceLineItem(
                        invoice=invoice,
                        description=item['description'][:255],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        amount=item['amount']
                    )
                )

            # Save all OCR results together.
            # Existing line items are preserved if OCR finds none.

            with transaction.atomic():

                OCRExtraction.objects.update_or_create(
                    invoice=invoice,
                    defaults={
                        'extracted_text': extracted_text,
                        'extracted_data': extracted_data,
                        'extraction_status': extraction_status
                    }
                )

                if new_line_items:

                    InvoiceLineItem.objects.filter(
                        invoice=invoice
                    ).delete()

                    InvoiceLineItem.objects.bulk_create(
                        new_line_items
                    )

                AuditLog.objects.create(
                    invoice=invoice,
                    action='OCR_EXTRACTION',
                    description=(
                        f'OCR extraction completed. '
                        f'{len(new_line_items)} line items detected. '
                        f'Status: {extraction_status}'
                    ),
                    performed_by=request.user.username
                )

            return Response({
                'message': 'OCR processing completed.',
                'invoice_id': invoice.id,
                'extraction_status': extraction_status,
                'extracted_data': extracted_data,
                'line_items_detected': len(line_items),
                'line_items_saved': len(new_line_items),
                'warnings': warnings,
                'review_required': bool(warnings),
                'extracted_text': extracted_text
            }, status=status.HTTP_200_OK)

        except Invoice.DoesNotExist:

            return Response(
                {'error': 'Invoice not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:

            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class POMatchingView(APIView):
    permission_classes = [IsAPClerk]
    def post(self, request, invoice_id):

        try:
            invoice = Invoice.objects.get(id=invoice_id)

            po_id = request.data.get('po_id')
            grn_id = request.data.get('grn_id')

            purchase_order = PurchaseOrder.objects.get(id=po_id)

            grn = None

            if grn_id:
                grn = GoodsReceiptNote.objects.get(
                    id=grn_id,
                    purchase_order=purchase_order
                )

            result = perform_po_matching(
                invoice,
                purchase_order,
                grn
            )

            return Response(result, status=status.HTTP_200_OK)

        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except PurchaseOrder.DoesNotExist:
            return Response(
                {'error': 'Purchase Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except GoodsReceiptNote.DoesNotExist:
            return Response(
                {'error': 'GRN not found for this Purchase Order'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
class ApprovalListView(generics.ListAPIView):
    permission_classes = [IsAllEmployees]
    serializer_class = ApprovalRequestSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return ApprovalRequest.objects.all().order_by('-created_at')

        roles = user.groups.values_list('name', flat=True)

        return ApprovalRequest.objects.filter(
            approver_role__in=roles
        ).order_by('-created_at')
class CreateApprovalView(APIView):
    permission_classes = [IsAPClerk]

    def post(self, request, invoice_id):

        try:
            invoice = Invoice.objects.get(id=invoice_id)

            if not invoice.total_amount or invoice.total_amount <= 0:
                return Response({
                    'error': 'Invoice must have a valid amount.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if Payment.objects.filter(
                invoice=invoice,
                payment_status='PAID'
            ).exists():
                return Response({
                    'error': 'Already paid invoices cannot be sent for approval.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if ApprovalRequest.objects.filter(invoice=invoice).exists():
                return Response({
                    'error': 'Approval requests already exist for this invoice.'
                }, status=status.HTTP_400_BAD_REQUEST)

            rules = ApprovalRule.objects.filter(
                is_active=True,
                minimum_amount__lte=invoice.total_amount
            )

            matching_rules = list(
                rules.filter(
                    maximum_amount__gte=invoice.total_amount
                )
            ) + list(
                rules.filter(maximum_amount__isnull=True)
            )

            matching_rules.sort(
                key=lambda rule: rule.approval_level
            )

            if not matching_rules:
                return Response({
                    'error': 'No approval rule found for this invoice amount.'
                }, status=status.HTTP_400_BAD_REQUEST)

            created_approvals = []

            for rule in matching_rules:

                approval = ApprovalRequest.objects.create(
                    invoice=invoice,
                    approval_rule=rule,
                    approver_role=rule.approver_role
                )

                created_approvals.append({
                    'approval_id': approval.id,
                    'approval_level': rule.approval_level,
                    'approver_role': rule.approver_role,
                    'status': approval.status
                })

                AuditLog.objects.create(
                    invoice=invoice,
                    action='Approval Requested',
                    description=(
                        f'Level {rule.approval_level} approval '
                        f'assigned to {rule.approver_role}'
                    ),
                    performed_by=request.user.username
                )

            invoice.status = 'PROCESSING'
            invoice.save()

            return Response({
                'message': 'Multi-level approval requests created successfully.',
                'invoice_number': invoice.invoice_number,
                'approval_count': len(created_approvals),
                'approvals': created_approvals
            }, status=status.HTTP_201_CREATED)

        except Invoice.DoesNotExist:
            return Response({
                'error': 'Invoice not found.'
            }, status=status.HTTP_404_NOT_FOUND)

class ApprovalActionView(APIView):
    permission_classes = [IsAllEmployees]

    def post(self, request, approval_id):

        try:
            approval = ApprovalRequest.objects.select_related(
                'invoice', 'approval_rule'
            ).get(id=approval_id)

            invoice = approval.invoice

            allowed_roles = {
                name.casefold()
                for name in request.user.groups.values_list(
                    'name', flat=True
                )
            }

            required_role = approval.approver_role.casefold()

            if not (
                request.user.is_superuser
                or required_role in allowed_roles
            ):
                return Response({
                    'error': 'You are not assigned to this approval.'
                }, status=status.HTTP_403_FORBIDDEN)

            if approval.status != 'PENDING':
                return Response({
                    'error': 'This approval has already been processed.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if invoice.status == 'FAILED':
                return Response({
                    'error': 'This invoice has been rejected.'
                }, status=status.HTTP_400_BAD_REQUEST)

            current_level = (
                approval.approval_rule.approval_level
                if approval.approval_rule else 1
            )

            # Prevent higher-level approval before lower levels
            earlier_pending = invoice.approval_requests.filter(
                status='PENDING',
                approval_rule__approval_level__lt=current_level
            ).exists()

            earlier_approved = invoice.approval_requests.filter(
                status='APPROVED',
                approval_rule__approval_level__lt=current_level
            )

            if earlier_pending:
                return Response({
                    'error': 'Previous approval levels must be completed first.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Reject action validation
            action = request.data.get('action')
            comments = request.data.get('comments', '')

            if action not in ['APPROVED', 'REJECTED']:
                return Response({
                    'error': 'Action must be APPROVED or REJECTED.'
                }, status=status.HTTP_400_BAD_REQUEST)

            approval.status = action
            approval.comments = comments
            approval.save()

            ApprovalAction.objects.create(
                approval_request=approval,
                action=action,
                comments=comments
            )

            if action == 'REJECTED':

                invoice.status = 'FAILED'

            else:

                remaining_approvals = invoice.approval_requests.filter(
                    status='PENDING'
                ).exists()

                if remaining_approvals:
                    invoice.status = 'PROCESSING'
                else:
                    invoice.status = 'PROCESSED'

            invoice.save()

            AuditLog.objects.create(
                invoice=invoice,
                action=action,
                description=(
                    f'Level {current_level} approval '
                    f'{action.lower()}. {comments}'
                ),
                performed_by=request.user.username
            )

            return Response({
                'message': f'Approval {action.lower()} successfully.',
                'approval_id': approval.id,
                'approval_level': current_level,
                'invoice_status': invoice.status,
                'status': approval.status
            }, status=status.HTTP_200_OK)

        except ApprovalRequest.DoesNotExist:
            return Response({
                'error': 'Approval request not found.'
            }, status=status.HTTP_404_NOT_FOUND)

class VendorListCreateView(generics.ListCreateAPIView):
    queryset = Vendor.objects.all().order_by('-created_at')
    serializer_class = VendorSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAllEmployees]
        else:
            permission_classes = [IsVendorManager]

        return [permission() for permission in permission_classes]

class CreatePaymentView(APIView):
    permission_classes = [IsFinance]

    def post(self, request, invoice_id):

        try:
            invoice = Invoice.objects.get(id=invoice_id)

            if invoice.status != 'PROCESSED':
                return Response({
                    'error': 'Only approved and processed invoices can be sent for payment.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if invoice.total_amount is None or invoice.total_amount <= 0:
                return Response({
                    'error': 'Invoice must have a valid amount.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if Payment.objects.filter(invoice=invoice).exists():
                return Response({
                    'error': 'Payment request already exists for this invoice.'
                }, status=status.HTTP_400_BAD_REQUEST)

            payment = Payment.objects.create(
                invoice=invoice,
                payment_reference='PAY-' + uuid.uuid4().hex[:10].upper(),
                amount=invoice.total_amount
            )

            AuditLog.objects.create(
                invoice=invoice,
                action='Payment Requested',
                description=f'Payment request created: {payment.payment_reference}'
            )

            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )

        except Invoice.DoesNotExist:
            return Response({
                'error': 'Invoice not found.'
            }, status=status.HTTP_404_NOT_FOUND)

class PaymentListView(generics.ListAPIView):
    permission_classes = [IsFinance]
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer

class PaymentStatusUpdateView(APIView):
    permission_classes = [IsFinance]

    def patch(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)

            new_status = request.data.get('payment_status')
            bank_reference = request.data.get('bank_reference', '')

            allowed_statuses = ['PROCESSING', 'PAID', 'FAILED']

            if new_status not in allowed_statuses:
                return Response({
                    'error': 'Invalid payment status.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if payment.payment_status in ['PAID', 'FAILED']:
                return Response({
                    'error': 'This payment has already been finalized.'
                }, status=status.HTTP_400_BAD_REQUEST)

            old_status = payment.payment_status

            payment.payment_status = new_status

            if bank_reference:
                payment.bank_reference = bank_reference

            if new_status == 'PAID':
                payment.payment_date = timezone.now().date()

            payment.save()

            AuditLog.objects.create(
                invoice=payment.invoice,
                action='Payment Status Updated',
                description=(
                    f'Payment {payment.payment_reference} '
                    f'changed from {old_status} to {new_status}. '
                    f'Bank reference: {bank_reference or "Not provided"}'
                ),
                performed_by=request.user.username
            )

            return Response({
                'message': 'Payment status updated successfully.',
                'payment': PaymentSerializer(payment).data
            })

        except Payment.DoesNotExist:
            return Response({
                'error': 'Payment not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class DashboardSummaryView(APIView):
    permission_classes = [IsAllEmployees]

    def get(self, request):

        today = timezone.now().date()

        invoices = Invoice.objects.select_related('vendor').all()

        # Basic dashboard statistics
        total_invoices = invoices.count()

        pending_approvals = ApprovalRequest.objects.filter(
            status='PENDING'
        ).count()

        total_vendors = Vendor.objects.count()

        active_vendors = Vendor.objects.filter(
            status='ACTIVE'
        ).count()

        total_payments = Payment.objects.count()

        paid_payments = Payment.objects.filter(
            payment_status='PAID'
        ).count()

        total_paid_amount = Payment.objects.filter(
            payment_status='PAID'
        ).aggregate(total=Sum('amount'))['total'] or 0

        pending_payments = Payment.objects.filter(
            payment_status__in=['REQUESTED', 'PROCESSING']
        ).count()

        # Invoice aging analytics
        aging = {
            'not_due': 0,
            '1_30_days': 0,
            '31_60_days': 0,
            '61_90_days': 0,
            'above_90_days': 0
        }

        overdue_count = 0

        for invoice in invoices:

            if not invoice.due_date:
                continue

            payment = getattr(invoice, 'payment', None)

            if payment and payment.payment_status == 'PAID':
                continue

            days_overdue = (today - invoice.due_date).days

            if days_overdue <= 0:
                aging['not_due'] += 1
            elif days_overdue <= 30:
                aging['1_30_days'] += 1
                overdue_count += 1
            elif days_overdue <= 60:
                aging['31_60_days'] += 1
                overdue_count += 1
            elif days_overdue <= 90:
                aging['61_90_days'] += 1
                overdue_count += 1
            else:
                aging['above_90_days'] += 1
                overdue_count += 1

        # OCR processing statistics
        ocr_records = OCRExtraction.objects.all()

        total_ocr = ocr_records.count()

        successful_ocr = ocr_records.filter(
            extraction_status='COMPLETED'
        ).count()

        failed_ocr = ocr_records.filter(
            extraction_status='FAILED'
        ).count()

        ocr_success_rate = (
            round((successful_ocr / total_ocr) * 100, 2)
            if total_ocr else 0
        )

        # Average processing turnaround time
        processing_times = []

        for record in ocr_records.select_related('invoice'):

            if record.processed_at and record.invoice.uploaded_at:

                duration = (
                    record.processed_at - record.invoice.uploaded_at
                ).total_seconds()

                if duration >= 0:
                    processing_times.append(duration)

        average_turnaround_seconds = (
            round(sum(processing_times) / len(processing_times), 2)
            if processing_times else 0
        )

        # Vendor analytics
        vendor_analytics = []

        for vendor in Vendor.objects.all():

            vendor_invoices = invoices.filter(vendor=vendor)

            vendor_analytics.append({
                'vendor_name': vendor.vendor_name,
                'vendor_status': vendor.status,
                'invoice_count': vendor_invoices.count(),
                'total_invoice_amount': float(
                    vendor_invoices.aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0
                )
            })

        return Response({

            'total_invoices': total_invoices,

            'pending_approvals': pending_approvals,

            'total_vendors': total_vendors,

            'active_vendors': active_vendors,

            'total_payments': total_payments,

            'paid_payments': paid_payments,

            'pending_payments': pending_payments,

            'total_paid_amount': total_paid_amount,

            'invoice_aging': aging,

            'overdue_invoice_count': overdue_count,

            'total_ocr_processed': total_ocr,

            'successful_ocr': successful_ocr,

            'failed_ocr': failed_ocr,

            'ocr_success_rate_percent': ocr_success_rate,

            'average_turnaround_seconds':
                average_turnaround_seconds,

            'vendor_analytics': vendor_analytics
        })


class ReportsView(APIView):
    permission_classes = [IsAllEmployees]

    def get(self, request):

        today = timezone.now().date()

        invoices = Invoice.objects.select_related('vendor').all()

        # Invoice status report
        invoice_status = {
            'total': invoices.count(),
            'uploaded': invoices.filter(status='UPLOADED').count(),
            'processing': invoices.filter(status='PROCESSING').count(),
            'processed': invoices.filter(status='PROCESSED').count(),
            'failed': invoices.filter(status='FAILED').count()
        }

        # Accounts payable aging report
        aging = {
            'not_due': 0,
            '1_30_days': 0,
            '31_60_days': 0,
            '61_90_days': 0,
            'above_90_days': 0
        }

        overdue_invoices = []

        for invoice in invoices:
            if not invoice.due_date:
                continue

            payment = getattr(invoice, 'payment', None)

            if payment and payment.payment_status == 'PAID':
                continue

            days_overdue = (today - invoice.due_date).days
            amount = float(invoice.total_amount or 0)

            if days_overdue <= 0:
                aging['not_due'] += amount
            elif days_overdue <= 30:
                aging['1_30_days'] += amount
            elif days_overdue <= 60:
                aging['31_60_days'] += amount
            elif days_overdue <= 90:
                aging['61_90_days'] += amount
            else:
                aging['above_90_days'] += amount

            if days_overdue > 0:
                overdue_invoices.append({
                    'invoice_number': invoice.invoice_number,
                    'vendor': invoice.vendor.vendor_name,
                    'amount': amount,
                    'days_overdue': days_overdue
                })

        # Exception report
        failed_ocr_ids = OCRExtraction.objects.filter(
            extraction_status='FAILED'
        ).values_list('invoice_id', flat=True)

        exceptions = invoices.filter(
            status='FAILED'
        ) | invoices.filter(id__in=failed_ocr_ids)

        exception_report = [
            {
                'invoice_number': invoice.invoice_number,
                'status': invoice.status
            }
            for invoice in exceptions.distinct()
        ]

        # Audit log report
        audit_logs = AuditLog.objects.all().order_by('-created_at')[:50]

        audit_report = [
            {
                'action': log.action,
                'description': log.description,
                'performed_by': log.performed_by,
                'created_at': log.created_at
            }
            for log in audit_logs
        ]

        # Vendor and GST report
        gst_report = [
            {
                'vendor': vendor.vendor_name,
                'gst_number': vendor.gst_number,
                'total_invoice_amount': float(
                    invoices.filter(vendor=vendor).aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0
                )
            }
            for vendor in Vendor.objects.all()
        ]

        return Response({
            'invoice_status_report': invoice_status,
            'ap_aging_report': aging,
            'overdue_invoices': overdue_invoices,
            'exception_report': exception_report,
            'audit_log_report': audit_report,
            'gst_tax_report': gst_report
        })


class BulkInvoiceUploadView(APIView):
    permission_classes = [IsAPClerk]

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        import json

        files = request.FILES.getlist('invoice_files')
        invoice_data = request.data.get('invoice_data')

        if not files:
            return Response({
                'error': 'Please select invoice files.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not invoice_data:
            return Response({
                'error': 'Invoice details are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice_details = json.loads(invoice_data)
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid invoice details format.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(invoice_details, list):
            return Response({
                'error': 'Invoice details must be a list.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(files) != len(invoice_details):
            return Response({
                'error': 'Each invoice file must have matching invoice details.'
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []

        for index, invoice_file in enumerate(files):

            data = invoice_details[index].copy()
            data['invoice_file'] = invoice_file

            serializer = InvoiceSerializer(data=data)

            if serializer.is_valid():
                invoice = serializer.save()

                results.append({
                    'file': invoice_file.name,
                    'status': 'SUCCESS',
                    'invoice_id': invoice.id,
                    'message': 'Invoice uploaded successfully.'
                })

            else:
                results.append({
                    'file': invoice_file.name,
                    'status': 'FAILED',
                    'errors': serializer.errors
                })

        successful = sum(
            1 for result in results
            if result['status'] == 'SUCCESS'
        )

        failed = len(results) - successful

        return Response({
            'message': 'Bulk invoice upload completed.',
            'total_files': len(files),
            'successful_uploads': successful,
            'failed_uploads': failed,
            'results': results
        }, status=status.HTTP_200_OK)

class EmailInvoiceIngestionView(APIView):
    permission_classes = [IsAPClerk]

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        source_email = request.data.get('source_email')
        vendor = request.data.get('vendor')
        invoice_number = request.data.get('invoice_number')
        attachment = request.FILES.get('attachment')

        if not source_email:
            return Response({
                'error': 'Source email address is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not vendor or not invoice_number or not attachment:
            return Response({
                'error': 'Vendor, invoice number and attachment are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        invoice_data = {
            'source_email': source_email,
            'vendor': vendor,
            'invoice_number': invoice_number,
            'invoice_date': request.data.get('invoice_date'),
            'invoice_file': attachment,
            'total_amount': request.data.get('total_amount'),
        }

        serializer = InvoiceSerializer(data=invoice_data)

        if serializer.is_valid():

            invoice = serializer.save()

            AuditLog.objects.create(
                invoice=invoice,
                action='Email Invoice Received',
                description=f'Invoice received from {source_email}'
            )

            return Response({
                'message': 'Email invoice ingested successfully.',
                'invoice_id': invoice.id,
                'source_email': source_email,
                'invoice': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
class PurchaseOrderListCreateView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all().prefetch_related('line_items')
    serializer_class = PurchaseOrderSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAllEmployees]
        else:
            permission_classes = [IsAPClerk]

        return [permission() for permission in permission_classes]

class GoodsReceiptNoteListCreateView(generics.ListCreateAPIView):
    queryset = GoodsReceiptNote.objects.all().prefetch_related('line_items')
    serializer_class = GoodsReceiptNoteSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAllEmployees]
        else:
            permission_classes = [IsAPClerk]

        return [permission() for permission in permission_classes]

class ApprovalRuleListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    def get_permissions(self):
        from rest_framework.permissions import IsAdminUser
        return [IsAdminUser()]

    queryset = ApprovalRule.objects.all().order_by('minimum_amount')
    serializer_class = ApprovalRuleSerializer


class ApprovalRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdmin]
    def get_permissions(self):
        from rest_framework.permissions import IsAdminUser
        return [IsAdminUser()]

    queryset = ApprovalRule.objects.all()
    serializer_class = ApprovalRuleSerializer

class EmployeeUserListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeUserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return User.objects.filter(
            is_superuser=False
        ).order_by('username')


class EmployeeUserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployeeUserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return User.objects.filter(
            is_superuser=False
        )

class ApprovalHistoryView(APIView):
    permission_classes = [IsAllEmployees]

    def get(self, request, invoice_id):
        try:
            invoice = Invoice.objects.get(id=invoice_id)

            approvals = invoice.approval_requests.select_related(
                'approval_rule'
            ).prefetch_related('actions').order_by(
                'approval_rule__approval_level', 'created_at'
            )

            history = []

            for approval in approvals:
                history.append({
                    'approval_id': approval.id,
                    'approval_level': (
                        approval.approval_rule.approval_level
                        if approval.approval_rule else 1
                    ),
                    'approver_role': approval.approver_role,
                    'status': approval.status,
                    'comments': approval.comments,
                    'created_at': approval.created_at,
                    'is_escalated': approval.is_escalated,
                    'escalated_at': approval.escalated_at,
                    'actions': [
                        {
                            'action': action.action,
                            'comments': action.comments,
                            'action_date': action.action_date
                        }
                        for action in approval.actions.all()
                    ]
                })

            return Response({
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'approval_history': history
            })

        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found.'},
                status=404
            )

class PaymentAdviceView(APIView):
    permission_classes = [IsFinance]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.select_related(
                'invoice',
                'invoice__vendor'
            ).get(id=payment_id)

            invoice = payment.invoice
            vendor = invoice.vendor

            return Response({
                'payment_advice': {
                    'payment_reference': payment.payment_reference,
                    'payment_status': payment.payment_status,
                    'payment_date': payment.payment_date,
                    'amount': str(payment.amount),
                    'payment_method': payment.payment_method,
                    'bank_reference': payment.bank_reference or 'Pending',
                },
                'invoice_details': {
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date,
                },
                'vendor_details': {
                    'vendor_name': vendor.vendor_name,
                    'bank_account_name': vendor.bank_account_name,
                    'bank_account_number': vendor.bank_account_number,
                    'bank_name': vendor.bank_name,
                    'ifsc_code': vendor.ifsc_code,
                }
            })

        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

class InvoiceTaxValidationView(APIView):
    permission_classes = [IsAPClerkOrApprover]

    def get(self, request, invoice_id):
        try:
            invoice = Invoice.objects.select_related('vendor').get(
                id=invoice_id
            )

            extraction = OCRExtraction.objects.filter(
                invoice=invoice
            ).first()

            errors = []
            warnings = []

            if not invoice.vendor.gst_number:
                warnings.append('Vendor GSTIN is not available in vendor master.')

            if extraction:
                data = extraction.extracted_data or {}

                extracted_gstin = data.get('gst_number') or data.get('gstin')

                if extracted_gstin and invoice.vendor.gst_number:
                    if extracted_gstin.strip().upper() != invoice.vendor.gst_number.strip().upper():
                        errors.append('Invoice GSTIN does not match vendor master GSTIN.')

                extracted_total = data.get('total_amount')

                if extracted_total:
                    try:
                        if abs(float(extracted_total) - float(invoice.total_amount)) > 0.01:
                            errors.append('OCR-extracted total does not match saved invoice amount.')
                    except (ValueError, TypeError):
                        warnings.append('OCR total amount could not be compared.')
                else:
                    warnings.append('Invoice total was not extracted by OCR.')

                if not extracted_gstin:
                    warnings.append('GSTIN was not extracted by OCR.')

            else:
                warnings.append('OCR extraction is not available.')

            return Response({
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number,
                'vendor': invoice.vendor.vendor_name,
                'validation_status': 'FAILED' if errors else 'PASSED_WITH_WARNINGS' if warnings else 'PASSED',
                'errors': errors,
                'warnings': warnings,
                'note': 'This check validates GSTIN and invoice totals. It does not independently calculate GST tax liability.'
            })

        except Invoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

class VendorDetailView(generics.RetrieveUpdateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAllEmployees]
        else:
            permission_classes = [IsVendorManager]

        return [permission() for permission in permission_classes]