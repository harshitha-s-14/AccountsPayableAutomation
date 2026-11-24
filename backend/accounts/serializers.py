import re
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import (
    Invoice, Vendor, Payment, ApprovalRequest, InvoiceLineItem,
    PurchaseOrder, PurchaseOrderLineItem,
    GoodsReceiptNote, GRNLineItem, ApprovalRule
)

class InvoiceLineItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceLineItem
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):

    line_items = InvoiceLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'

    def validate(self, attrs):

        vendor = attrs.get(
            'vendor',
            self.instance.vendor if self.instance else None
        )

        invoice_number = attrs.get(
            'invoice_number',
            self.instance.invoice_number if self.instance else None
        )

        invoice_date = attrs.get(
            'invoice_date',
            self.instance.invoice_date if self.instance else None
        )

        due_date = attrs.get(
            'due_date',
            self.instance.due_date if self.instance else None
        )

        total_amount = attrs.get(
            'total_amount',
            self.instance.total_amount if self.instance else None
        )

        # 1. Vendor validation
        if not vendor:
            raise serializers.ValidationError({
                'vendor': 'Vendor is required.'
            })

        if vendor.status != 'ACTIVE':
            raise serializers.ValidationError({
                'vendor': 'Invoice cannot be uploaded for an inactive or pending vendor.'
            })

        # 2. Invoice number validation
        if not invoice_number or not invoice_number.strip():
            raise serializers.ValidationError({
                'invoice_number': 'A valid invoice number is required.'
            })

        # 3. Duplicate invoice validation
        existing_invoice = Invoice.objects.filter(
            vendor=vendor,
            invoice_number=invoice_number.strip()
        )

        if self.instance:
            existing_invoice = existing_invoice.exclude(
                pk=self.instance.pk
            )

        if existing_invoice.exists():
            raise serializers.ValidationError({
                'invoice_number': 'Duplicate invoice number for this vendor.'
            })

        # 4. GSTIN validation
        if vendor.gst_number:
            gst_pattern = (
                r'^[0-9]{2}[A-Z]{5}[0-9]{4}'
                r'[A-Z][A-Z0-9]Z[A-Z0-9]$'
            )

            if not re.match(gst_pattern, vendor.gst_number):
                raise serializers.ValidationError({
                    'vendor': 'Vendor GSTIN format is invalid.'
                })

        # 5. Mandatory invoice date validation
        if not invoice_date:
            raise serializers.ValidationError({
                'invoice_date': 'Invoice date is required.'
            })

        # 6. Mandatory amount validation
        if total_amount is None:
            raise serializers.ValidationError({
                'total_amount': 'Invoice amount is required.'
            })

        if total_amount <= 0:
            raise serializers.ValidationError({
                'total_amount': 'Invoice amount must be greater than zero.'
            })

        # 7. Due date validation
        if due_date and due_date < invoice_date:
            raise serializers.ValidationError({
                'due_date': 'Due date cannot be earlier than invoice date.'
            })

        return attrs

    def validate_invoice_file(self, value):

        allowed_extensions = [
            'pdf',
            'jpg',
            'jpeg',
            'png',
            'tiff'
        ]

        extension = value.name.rsplit('.', 1)[-1].lower()

        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                'Only PDF, JPG, JPEG, PNG and TIFF files are allowed.'
            )

        return value

class VendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = '__all__'

    def validate(self, attrs):

        status_value = attrs.get(
            'status',
            self.instance.status if self.instance else 'PENDING'
        )

        if status_value == 'ACTIVE':

            required_fields = [
                'bank_account_name',
                'bank_account_number',
                'bank_name',
                'ifsc_code'
            ]

            for field in required_fields:

                value = attrs.get(
                    field,
                    getattr(self.instance, field, '') if self.instance else ''
                )

                if not value or not value.strip():
                    raise serializers.ValidationError({
                        field: 'This field is required to activate a vendor.'
                    })

            if not re.match(
                r'^[A-Z]{4}0[A-Z0-9]{6}$',
                attrs.get(
                    'ifsc_code',
                    self.instance.ifsc_code if self.instance else ''
                ).upper()
            ):
                raise serializers.ValidationError({
                    'ifsc_code': 'Enter a valid IFSC code.'
                })

        return attrs


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['payment_reference', 'created_at']


class ApprovalRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApprovalRequest
        fields = '__all__'

class PurchaseOrderLineItemSerializer(serializers.ModelSerializer):
    class Meta:
     model = PurchaseOrderLineItem
     fields = '__all__'
     read_only_fields = ['purchase_order']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    line_items = PurchaseOrderLineItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def create(self, validated_data):
        items = validated_data.pop('line_items', [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)

        for item in items:
            PurchaseOrderLineItem.objects.create(
                purchase_order=purchase_order,
                **item
            )

        return purchase_order


class GRNLineItemSerializer(serializers.ModelSerializer):
    class Meta:
     model = GRNLineItem
     fields = '__all__'
     read_only_fields = ['grn']


class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    line_items = GRNLineItemSerializer(many=True)

    class Meta:
        model = GoodsReceiptNote
        fields = '__all__'

    def create(self, validated_data):
        items = validated_data.pop('line_items', [])
        grn = GoodsReceiptNote.objects.create(**validated_data)

        for item in items:
            GRNLineItem.objects.create(
                grn=grn,
                **item
            )

        return grn

class ApprovalRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApprovalRule
        fields = '__all__'

    def validate(self, attrs):
        minimum = attrs.get('minimum_amount', 0)
        maximum = attrs.get('maximum_amount')

        if minimum < 0:
            raise serializers.ValidationError({
                'minimum_amount': 'Minimum amount cannot be negative.'
            })

        if maximum is not None and maximum <= minimum:
            raise serializers.ValidationError({
                'maximum_amount': 'Maximum amount must be greater than minimum amount.'
            })

        return attrs

class EmployeeUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8
    )
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'role',
            'password',
            'role_name'
        ]

    def get_role_name(self, obj):
        return obj.groups.values_list(
            'name', flat=True
        ).first() or 'Unassigned'

    def validate_role(self, value):
        allowed_roles = [
            'AP_Clerk',
            'Approver',
            'Finance',
            'Vendor_Manager',
            'MANAGER'
        ]

        if value not in allowed_roles:
            raise serializers.ValidationError(
                'Invalid employee role.'
            )

        return value

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password', None)

        if not password:
            raise serializers.ValidationError({
                'password': 'Password is required.'
            })

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        group = Group.objects.get(name=role)
        user.groups.add(group)

        return user

    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)
        password = validated_data.pop('password', None)

        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)

        if password:
            instance.set_password(password)

        instance.save()

        if role:
            group = Group.objects.get(name=role)
            instance.groups.clear()
            instance.groups.add(group)

        return instance