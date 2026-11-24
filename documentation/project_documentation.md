# Accounts Payable Automation with OCR

## 1. Project Overview

Accounts Payable Automation with OCR is a web-based application designed to simplify and automate the accounts payable process in an organization.

Accounts Payable (AP) refers to the money a company owes to its vendors or suppliers for goods and services received.

Traditionally, invoice processing involves manually entering invoice details, checking purchase orders, verifying goods received, obtaining approvals, and tracking payments. This process can be time-consuming and prone to human errors.

This application automates important steps using Optical Character Recognition (OCR), invoice validation, purchase order matching, goods receipt matching, approval workflows, and payment tracking.

## 2. Project Objectives

- Automate vendor invoice processing.
- Extract invoice information using OCR.
- Validate invoice details and identify duplicate invoices.
- Match invoices with purchase orders and goods receipt notes.
- Manage multi-level invoice approval workflows.
- Track payment status.
- Generate reports and maintain audit records.
- Reduce manual effort and improve processing accuracy.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Backend web framework |
| Django REST Framework | REST API development |
| React | Frontend development |
| Vite | Frontend development and build tool |
| PostgreSQL | Database |
| PyMuPDF | Extracting text from PDF invoices |
| Tesseract OCR | Extracting text from scanned documents and images |
| HTML, CSS, JavaScript | Frontend structure and styling |
| Git and GitHub | Version control and source code management |
| Render | Backend deployment |
| Vercel | Frontend deployment |

## 4. System Architecture

The application follows a frontend-backend architecture.

### Frontend
React provides the user interface. Users can log in, manage vendors, upload invoices, view extracted information, perform matching, manage approvals, track payments, and access reports.

### Backend
Django and Django REST Framework handle business logic, authentication, permissions, invoice processing, OCR integration, validation, matching, approvals, payments, and reports.

### Database
PostgreSQL stores application information, including user accounts, vendor details, invoices, purchase orders, goods receipt notes, approval records, payment records, and audit logs.

### OCR Processing
PyMuPDF is used to extract text from PDF documents. Tesseract OCR is used as a fallback for scanned PDFs and image-based invoices. Rule-based extraction identifies relevant invoice information from the extracted text.

### Application Flow

User → React Frontend → Django REST API → Business Logic and OCR → PostgreSQL Database → API Response → React Frontend

## 5. Main Modules

### 5.1 User Authentication and Role-Based Access

The application provides user authentication and role-based access control.

Different roles are supported, including:

- Admin
- AP Clerk
- Approver
- Finance
- Vendor Manager
- Manager

Access to application operations is controlled based on user permissions.

### 5.2 Vendor Management

This module manages vendor information.

It supports:
- Registering new vendors.
- Storing vendor name and contact information.
- Recording GST identification details.
- Maintaining vendor bank details.
- Managing vendor information and active status.

Vendor information is used during invoice validation and processing.

### 5.3 Invoice Upload and OCR Extraction

Users can upload vendor invoices in supported PDF and image formats.

The OCR processing workflow:
1. Accepts an uploaded invoice.
2. Extracts text from PDF documents using PyMuPDF.
3. Uses Tesseract OCR for scanned documents and images.
4. Applies rule-based extraction to identify invoice details.
5. Returns the extracted information for further processing.

Information extracted includes:
- Invoice number
- Invoice date
- Due date
- GST number
- Total amount
- Line item descriptions
- Quantities and amounts

### 5.4 Invoice Validation

The validation module checks whether invoice information is valid before further processing.

It checks:
- Whether the vendor exists and is active.
- Whether the invoice number is available.
- Whether the invoice is a duplicate for the same vendor.
- Whether the GST number follows the expected format.
- Whether invoice dates are valid.
- Whether the total amount is positive.
- Whether the due date is not earlier than the invoice date.
- Whether the uploaded file has a supported extension.

Validation results help identify incorrect or incomplete invoices.

### 5.5 Purchase Order Matching

Purchase Order (PO) matching compares invoice information with the corresponding purchase order.

The application checks:
- Whether the vendor matches.
- Whether invoice and purchase order amounts match within the configured tolerance.
- Whether line item descriptions match.
- Whether quantities and amounts are consistent.

This helps identify discrepancies before invoice approval.

### 5.6 Goods Receipt Note Matching

A Goods Receipt Note (GRN) confirms that goods or services have been received.

The application supports three-way matching between:

1. Invoice
2. Purchase Order
3. Goods Receipt Note

The matching process checks vendor details, amounts, line items, and received quantities.

If the required information matches, the invoice can pass the matching process.

### 5.7 Approval Workflow

This module manages invoice approvals.

It supports:
- Configurable approval rules.
- Approval levels.
- Role-based approver permissions.
- Approval and rejection actions.
- Multiple approval stages.
- Escalation settings and escalation handling.

Invoices are processed through the configured approval workflow before payment processing.

### 5.8 Payment Processing

The payment module supports payment record creation and payment status tracking.

It allows users to manage payment information and update payment status.

**Note:** Payment processing in this project is simulated. The application does not directly connect to a real bank or execute actual bank transfers.

### 5.9 Dashboard and Reports

The dashboard provides an overview of invoice processing activities.

The reports module provides information such as:
- Invoice status reports.
- Accounts payable aging reports.
- Overdue invoice reports.
- Invoice exception reports.
- Audit log reports.
- GST and tax reports.

Supported reports can be exported for further analysis.

### 5.10 Audit Logs

The application maintains audit records of important activities.

These records help track actions performed within the system and support accountability and traceability.

## 6. Database Design

PostgreSQL is used as the relational database.

The database stores information related to the following entities:

| Entity | Purpose |
|---|---|
| User | Stores user account and role information |
| Vendor | Stores vendor details, GST information, and bank details |
| Invoice | Stores uploaded invoice information and processing status |
| Purchase Order | Stores purchase order details |
| POLineItem | Stores purchase order line items |
| GRN | Stores goods receipt information |
| GRNLineItem | Stores received item and quantity details |
| ApprovalRule | Stores configurable approval conditions |
| ApprovalRequest | Stores invoice approval records |
| Payment | Stores payment tracking information |
| AuditLog | Stores activity and audit records |

Relationships between these entities support invoice processing, matching, approval, and payment tracking.

Vendor bank details are maintained as part of the Vendor information in this implementation.

## 7. Invoice Processing Workflow

The complete workflow is:

1. A vendor is registered in the system.
2. A purchase order is created for the vendor.
3. Goods receipt information is recorded through a GRN.
4. The vendor invoice is uploaded.
5. OCR extracts invoice information.
6. Invoice validation checks the extracted information.
7. Two-way matching compares the invoice with the purchase order.
8. Three-way matching additionally checks the GRN.
9. The invoice is sent through the configured approval workflow.
10. The authorized approver approves or rejects the invoice.
11. Payment information is created and its status is tracked.
12. Reports and audit records are available for monitoring.

## 8. Testing and Verification

The application was tested using a sample vendor and invoice.

The tested workflow included:

- Successful application login.
- Vendor registration.
- Invoice upload.
- OCR extraction of invoice information.
- Invoice validation.
- Purchase order creation and matching.
- GRN creation and matching.
- Successful three-way matching.
- Invoice approval.
- Payment record creation and payment status update.
- Dashboard and report verification.

The matching test confirmed that the vendor, invoice amount, line items, and received quantities matched the corresponding purchase order and GRN.

## 9. Challenges and Solutions

### Challenge 1: Extracting Invoice Information

Invoices can contain different layouts and formats.

**Solution:** Used PyMuPDF for PDF text extraction and Tesseract OCR as a fallback for scanned documents and images. Rule-based extraction was implemented to identify important invoice fields.

### Challenge 2: Handling Invoice Validation

Incorrect information and duplicate invoices can cause processing errors.

**Solution:** Implemented validation checks for vendor details, invoice numbers, GST numbers, dates, amounts, and supported file formats.

### Challenge 3: Matching Invoice, PO, and GRN

Differences in descriptions, quantities, and amounts can affect matching.

**Solution:** Implemented matching logic to compare vendor information, amounts, line items, and received quantities.

### Challenge 4: Managing Invoice Approvals

Different invoices may require different approval levels and authorized users.

**Solution:** Implemented configurable approval rules and role-based approval permissions.

### Challenge 5: Deployment

The application required separate frontend and backend deployment with database connectivity.

**Solution:** Deployed the React frontend using Vercel and the Django backend using Render, with PostgreSQL as the database.

## 10. Deployment

The application is deployed and accessible online.

- Frontend: Vercel
- Backend: Render
- Database: PostgreSQL

**Live Application:**  
https://accounts-payable-automation-nu.vercel.app

**GitHub Repository:**  
https://github.com/harshitha-s-14/AccountsPayableAutomation

## 11. Future Enhancements

The application can be extended with:
- Advanced AI-based invoice data extraction.
- Integration with real banking and payment systems.
- Automated email notifications.
- Additional financial analytics and reporting.
- Integration with ERP and accounting platforms.

These are possible future improvements and are not claimed as existing features.

## 12. Conclusion

Accounts Payable Automation with OCR provides a structured approach to managing vendor invoices and accounts payable activities.

By combining OCR-based extraction, invoice validation, purchase order matching, GRN matching, approval workflows, payment tracking, and reporting, the application reduces manual processing effort and improves visibility into invoice operations.

The project demonstrates the practical use of Python, Django REST Framework, React, PostgreSQL, and OCR technologies to develop and deploy a full-stack business application.