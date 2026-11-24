\# Accounts Payable Automation

\## Database Design Document



\### 1. Technology Stack

\- Frontend: React.js

\- Backend: Django

\- API: Django REST Framework

\- Database: PostgreSQL

\- OCR: Tesseract OCR

\- Document Processing: PyMuPDF and Pillow



\### 2. Database Tables



\#### A. Vendor Management

1\. Vendor

&#x20;  - id (Primary Key)

&#x20;  - vendor\_name

&#x20;  - email

&#x20;  - phone

&#x20;  - address

&#x20;  - gst\_number

&#x20;  - tax\_identification\_number

&#x20;  - status

&#x20;  - created\_at



2\. VendorBankDetail

&#x20;  - id (Primary Key)

&#x20;  - vendor\_id (Foreign Key)

&#x20;  - account\_holder\_name

&#x20;  - account\_number

&#x20;  - ifsc\_code

&#x20;  - bank\_name



\#### B. Invoice Capture

3\. Invoice

&#x20;  - id (Primary Key)

&#x20;  - vendor\_id (Foreign Key)

&#x20;  - invoice\_number

&#x20;  - invoice\_date

&#x20;  - due\_date

&#x20;  - total\_amount

&#x20;  - tax\_amount

&#x20;  - currency

&#x20;  - source

&#x20;  - document

&#x20;  - status

&#x20;  - uploaded\_at



4\. InvoiceLineItem

&#x20;  - id (Primary Key)

&#x20;  - invoice\_id (Foreign Key)

&#x20;  - description

&#x20;  - quantity

&#x20;  - unit\_price

&#x20;  - tax\_percentage

&#x20;  - line\_total



\#### C. OCR and AI Extraction

5\. OCRExtraction

&#x20;  - id (Primary Key)

&#x20;  - invoice\_id (Foreign Key)

&#x20;  - extracted\_data

&#x20;  - confidence\_score

&#x20;  - processing\_status

&#x20;  - extracted\_at



\#### D. Purchase Order Matching

6\. PurchaseOrder

&#x20;  - id (Primary Key)

&#x20;  - vendor\_id (Foreign Key)

&#x20;  - po\_number

&#x20;  - order\_date

&#x20;  - total\_amount

&#x20;  - status



7\. PurchaseOrderLineItem

&#x20;  - id (Primary Key)

&#x20;  - purchase\_order\_id (Foreign Key)

&#x20;  - description

&#x20;  - quantity

&#x20;  - unit\_price



8\. GoodsReceiptNote

&#x20;  - id (Primary Key)

&#x20;  - purchase\_order\_id (Foreign Key)

&#x20;  - grn\_number

&#x20;  - received\_date

&#x20;  - status



9\. GRNLineItem

&#x20;  - id (Primary Key)

&#x20;  - grn\_id (Foreign Key

