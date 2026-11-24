import { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || API_BASE_URL + '';

function App() {
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('ap_auth_token') || '');
  const [currentUser, setCurrentUser] = useState(null);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  const apiFetch = (url, options = {}) => fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(localStorage.getItem('ap_auth_token') ? { Authorization: `Token ${localStorage.getItem('ap_auth_token')}` } : {})
    }
  });

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoginLoading(true);
    setLoginError('');
    try {
      const response = await fetch(API_BASE_URL + '/api/invoices/auth/login/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Login failed.');
      localStorage.setItem('ap_auth_token', data.token);
      setAuthToken(data.token);
      setCurrentUser(data.user);
    } catch (error) { setLoginError(error.message); }
    finally { setLoginLoading(false); }
  };

  const handleLogout = async () => {
    try { await apiFetch(API_BASE_URL + '/api/invoices/auth/logout/', { method: 'POST' }); } catch (_) {}
    localStorage.removeItem('ap_auth_token');
    setAuthToken(''); setCurrentUser(null);
  };
  // User roles
  const userRole = currentUser?.role;

  const isAdmin = userRole === 'Admin';
  const isAPClerk = userRole === 'AP_Clerk';
  const isApprover = userRole === 'Approver';
  const isFinance = userRole === 'Finance';
  const isVendorManager = userRole === 'Vendor_Manager';
  const isManager = userRole === 'MANAGER';

  // Section access
  const canViewDashboard = Boolean(userRole);
  const canUploadInvoices = isAdmin || isAPClerk;
  const canManageVendors = isAdmin || isVendorManager;
  const canManagePayments = isAdmin || isFinance;
  const canConfigureApprovalRules = isAdmin;
  const canProcessApprovals = isAdmin || isApprover || isManager;
  const canManageEmployees = isAdmin;
  const canViewReports = Boolean(userRole);
  const canManagePurchaseOrders = isAdmin || isAPClerk;
  const canViewPurchaseOrders = Boolean(userRole);

  const [formData, setFormData] = useState({
    vendor: '2',
    invoice_number: '',
    invoice_date: '',
    due_date: '',
    total_amount: '',
    status: 'UPLOADED'
  });

  const [invoiceFile, setInvoiceFile] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [invoices, setInvoices] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [vendors, setVendors] = useState([]);
  // Purchase Order states
const [purchaseOrders, setPurchaseOrders] = useState([]);

const [poFormData, setPoFormData] = useState({
  po_number: '',
  vendor: '',
  po_date: '',
  total_amount: '',
  status: 'OPEN',
  line_items: [
    {
      description: '',
      quantity: '1',
      unit_price: '',
      amount: ''
    }
  ]
});

// Goods Receipt Note states
const [grns, setGrns] = useState([]);
const [matchingResult, setMatchingResult] = useState(null);

const [grnFormData, setGrnFormData] = useState({
  grn_number: '',
  purchase_order: '',
  received_date: '',
  status: 'RECEIVED',
  line_items: [
    {
      description: '',
      quantity_received: '1'
    }
  ]
});
  const [payments, setPayments] = useState([]);
  const [approvals, setApprovals] = useState([]);
  // Approval Rule Management
const [approvalRules, setApprovalRules] = useState([]);

const [approvalRuleForm, setApprovalRuleForm] = useState({
  rule_name: '',
  approval_level: '1',
  minimum_amount: '',
  maximum_amount: '',
  approver_role: '',
  is_active: true
});
  const [reports, setReports] = useState(null);
// Employee User Management
const [employees, setEmployees] = useState([]);

const [employeeForm, setEmployeeForm] = useState({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  role: 'AP_Clerk',
  password: ''
});

const [employeeMessage, setEmployeeMessage] = useState('');
const [employeeLoading, setEmployeeLoading] = useState(false);
const [paymentLoading, setPaymentLoading] = useState(false);

const [vendorForm, setVendorForm] = useState({
  vendor_name: '',
  email: '',
  phone: '',
  address: '',
  gst_number: '',
  tax_identification_number: '',
  bank_account_name: '',
  bank_account_number: '',
  bank_name: '',
  ifsc_code: '',
  branch_name: '',
  status: 'ACTIVE'
});
  const [fetchError, setFetchError] = useState('');
  const [bulkFiles, setBulkFiles] = useState([]);
const [bulkDetails, setBulkDetails] = useState([]);
const [bulkMessage, setBulkMessage] = useState('');
const [bulkLoading, setBulkLoading] = useState(false);
const [emailFile, setEmailFile] = useState(null);
const [emailVendor, setEmailVendor] = useState('');
const [emailInvoiceNumber, setEmailInvoiceNumber] = useState('');
const [emailInvoiceDate, setEmailInvoiceDate] = useState('');
const [emailTotalAmount, setEmailTotalAmount] = useState('');
const [sourceEmail, setSourceEmail] = useState('');
const [emailMessage, setEmailMessage] = useState('');
const [emailLoading, setEmailLoading] = useState(false);
useEffect(() => {
  if (!authToken) return;
  apiFetch(API_BASE_URL + '/api/invoices/auth/me/').then(r => r.ok ? r.json() : Promise.reject()).then(setCurrentUser).catch(handleLogout);
  fetchInvoices();
  fetchDashboard();
  fetchVendors();
  fetchPayments();
  fetchApprovals();
  fetchApprovalRules();
  fetchReports();
  fetchPurchaseOrders();
  fetchGRNs();
}, [authToken]);
useEffect(() => {
  if (authToken && currentUser?.role === 'Admin') {
    fetchEmployees();
  }
}, [authToken, currentUser]);
const fetchInvoices = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/list/'
    );

    if (!response.ok) {
      throw new Error('Failed to fetch invoices');
    }

    const data = await response.json();

    setInvoices(data);

  } catch (error) {
    setFetchError(error.message);
  }
};

const fetchDashboard = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/dashboard/'
    );

    const data = await response.json();

    if (response.ok) {
      setDashboardData(data);
    }
  } catch (error) {
    console.error('Dashboard error:', error);
  }
};

const fetchVendors = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/vendors/'
    );

    const data = await response.json();

    if (response.ok) {
      setVendors(data);
    }
  } catch (error) {
    console.error('Vendor loading error:', error);
  }
};
const fetchPurchaseOrders = async () => {
  try {
    const response = await apiFetch(API_BASE_URL + '/api/invoices/purchase-orders/');
    const data = await response.json();
    setPurchaseOrders(data);
  } catch (error) {
    console.error('Error fetching purchase orders:', error);
  }
};

const fetchGRNs = async () => {
  try {
    const response = await apiFetch(API_BASE_URL + '/api/invoices/grns/');
    const data = await response.json();
    setGrns(data);
  } catch (error) {
    console.error('Error fetching GRNs:', error);
  }
};
// Purchase Order form handlers
const handlePoChange = (e) => {
  setPoFormData({
    ...poFormData,
    [e.target.name]: e.target.value
  });
};

const handlePoItemChange = (index, e) => {
  const updatedItems = [...poFormData.line_items];

  updatedItems[index][e.target.name] = e.target.value;

  const quantity = Number(updatedItems[index].quantity) || 0;
  const unitPrice = Number(updatedItems[index].unit_price) || 0;

  updatedItems[index].amount = (quantity * unitPrice).toFixed(2);

  setPoFormData({
    ...poFormData,
    line_items: updatedItems,
    total_amount: updatedItems.reduce(
      (sum, item) => sum + Number(item.amount || 0),
      0
    ).toFixed(2)
  });
};

const addPoItem = () => {
  setPoFormData({
    ...poFormData,
    line_items: [
      ...poFormData.line_items,
      {
        description: '',
        quantity: '1',
        unit_price: '',
        amount: ''
      }
    ]
  });
};

const submitPurchaseOrder = async (e) => {
  e.preventDefault();

  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/purchase-orders/',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(poFormData)
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(JSON.stringify(data));
      return;
    }

    alert('Purchase Order created successfully!');

    setPoFormData({
      po_number: '',
      vendor: '',
      po_date: '',
      total_amount: '',
      status: 'OPEN',
      line_items: [
        {
          description: '',
          quantity: '1',
          unit_price: '',
          amount: ''
        }
      ]
    });

    fetchPurchaseOrders();
  } catch (error) {
    alert('Error creating Purchase Order.');
    console.error(error);
  }
};


// GRN form handlers
const handleGrnChange = (e) => {
  setGrnFormData({
    ...grnFormData,
    [e.target.name]: e.target.value
  });
};

const handleGrnItemChange = (index, e) => {
  const updatedItems = [...grnFormData.line_items];

  updatedItems[index][e.target.name] = e.target.value;

  setGrnFormData({
    ...grnFormData,
    line_items: updatedItems
  });
};

const addGrnItem = () => {
  setGrnFormData({
    ...grnFormData,
    line_items: [
      ...grnFormData.line_items,
      {
        description: '',
        quantity_received: '1'
      }
    ]
  });
};

const submitGRN = async (e) => {
  e.preventDefault();

  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/grns/',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(grnFormData)
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(JSON.stringify(data));
      return;
    }

    alert('Goods Receipt Note created successfully!');

    setGrnFormData({
      grn_number: '',
      purchase_order: '',
      received_date: '',
      status: 'RECEIVED',
      line_items: [
        {
          description: '',
          quantity_received: '1'
        }
      ]
    });

    fetchGRNs();
  } catch (error) {
    alert('Error creating GRN.');
    console.error(error);
  }
};
const fetchPayments = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/payments/'
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error('Unable to load payments');
    }

    setPayments(data);
  } catch (error) {
    console.error('Payment loading error:', error);
  }
};
const fetchApprovals = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/approvals/'
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error('Unable to load approvals');
    }

    setApprovals(data);
  } catch (error) {
    console.error('Approval loading error:', error);
  }
};
const fetchApprovalRules = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/approval-rules/'
    );

    const data = await response.json();

    if (response.ok) {
      setApprovalRules(data);
    }
  } catch (error) {
    console.error('Error fetching approval rules:', error);
  }
};
// Approval Rule form handlers
const handleApprovalRuleChange = (e) => {
  const { name, value, type, checked } = e.target;

  setApprovalRuleForm({
    ...approvalRuleForm,
    [name]: type === 'checkbox' ? checked : value
  });
};

const submitApprovalRule = async (e) => {
  e.preventDefault();

  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/approval-rules/',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...approvalRuleForm,
          minimum_amount: Number(approvalRuleForm.minimum_amount),
          maximum_amount: approvalRuleForm.maximum_amount === ''
            ? null
            : Number(approvalRuleForm.maximum_amount)
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(JSON.stringify(data));
      return;
    }

    alert('Approval rule created successfully!');

    setApprovalRuleForm({
      rule_name: '',
      approval_level: '1',
      minimum_amount: '',
      maximum_amount: '',
      approver_role: '',
      is_active: true
    });

    fetchApprovalRules();

  } catch (error) {
    alert('Error creating approval rule.');
    console.error(error);
  }
};
const fetchReports = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/reports/'
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error('Unable to load reports');
    }

    setReports(data);
  } catch (error) {
    console.error('Reports loading error:', error);
  }
};
const fetchEmployees = async () => {
  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/employees/'
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Unable to load employees.');
    }

    setEmployees(data);
  } catch (error) {
    console.error('Employee loading error:', error);
    setEmployeeMessage(error.message);
  }
};
const handleEmployeeSubmit = async (event) => {
  event.preventDefault();
  setEmployeeLoading(true);
  setEmployeeMessage('');

  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/employees/',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(employeeForm)
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(JSON.stringify(data));
    }

    setEmployeeMessage('Employee account created successfully!');

    setEmployeeForm({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      role: 'AP_Clerk',
      password: ''
    });

    fetchEmployees();

  } catch (error) {
    setEmployeeMessage('Employee creation failed: ' + error.message);
  } finally {
    setEmployeeLoading(false);
  }
};

const updateEmployee = async (employeeId, updates) => {
  try {
    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/employees/${employeeId}/`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(JSON.stringify(data));
    }

    setEmployeeMessage('Employee account updated successfully.');
    fetchEmployees();

  } catch (error) {
    setEmployeeMessage('Update failed: ' + error.message);
  }
};

const toggleEmployeeStatus = (employee) => {
  updateEmployee(employee.id, {
    is_active: !employee.is_active
  });
};

const resetEmployeePassword = (employee) => {
  const newPassword = window.prompt(
    `Enter a new password for ${employee.username}:`
  );

  if (!newPassword) return;

  if (newPassword.length < 8) {
    setEmployeeMessage('Password must contain at least 8 characters.');
    return;
  }

  updateEmployee(employee.id, {
    password: newPassword
  });
};
const createApproval = async (invoiceId) => {
  try {
    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/${invoiceId}/approval/`,
      {
        method: 'POST',
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Unable to create approval.');
    }

    alert('Approval request created successfully!');

    fetchApprovals();
    fetchDashboard();

  } catch (error) {
    alert(error.message);
  }
};

const handleApprovalAction = async (approvalId, action) => {
  try {
    const comments = window.prompt('Enter approval comments:') || '';

    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/approvals/${approvalId}/action/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          comments,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Unable to process approval.');
    }

    alert(data.message);

    fetchApprovals();
    fetchDashboard();

  } catch (error) {
    alert(error.message);
  }
};
const createPayment = async (invoiceId) => {
  try {
    setPaymentLoading(true);

    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/${invoiceId}/payment/`,
      {
        method: 'POST'
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || JSON.stringify(data));
    }

    alert('Payment request created successfully!');

    fetchPayments();
    fetchDashboard();

  } catch (error) {
    alert('Payment Error: ' + error.message);
  } finally {
    setPaymentLoading(false);
  }
};
const matchPurchaseOrder = async (invoiceId) => {

  if (purchaseOrders.length === 0) {
    alert('Please create a Purchase Order first.');
    return;
  }

  const poOptions = purchaseOrders
    .map(po => `ID: ${po.id} | PO Number: ${po.po_number}`)
    .join('\n');

  const poId = window.prompt(
    `Select Purchase Order by entering its ID:\n\n${poOptions}`
  );

  if (!poId) return;

  const selectedPO = purchaseOrders.find(
    po => String(po.id) === poId.trim()
  );

  if (!selectedPO) {
    alert('Invalid Purchase Order ID.');
    return;
  }

  const grnOptions = grns.length > 0
    ? grns.map(grn =>
        `ID: ${grn.id} | GRN Number: ${grn.grn_number}`
      ).join('\n')
    : 'No GRNs available.';

  const grnId = window.prompt(
    `Enter GRN ID for 3-way matching.\nLeave blank for 2-way matching.\n\n${grnOptions}`
  );

  if (grnId === null) return;

  if (grnId.trim() && !grns.some(
    grn => String(grn.id) === grnId.trim()
  )) {
    alert('Invalid GRN ID.');
    return;
  }

  try {
    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/${invoiceId}/match-po/`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          po_id: poId.trim(),
          ...(grnId.trim() ? { grn_id: grnId.trim() } : {}),
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'PO matching failed.');
    }
    setMatchingResult(data);

    alert(
      `MATCHING COMPLETED\n\n` +
      `Invoice: ${data.invoice_number}\n` +
      `Purchase Order: ${data.po_number}\n` +
      `Matching Type: ${grnId.trim() ? '3-Way Matching' : '2-Way Matching'}\n` +
      `Overall Result: ${data.overall_status}\n\n` +
      JSON.stringify(data, null, 2)
    );

  } catch (error) {
    alert(error.message);
  }
};
const handleVendorSubmit = async (e) => {
  e.preventDefault();

  try {
    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/vendors/',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(vendorForm)
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(JSON.stringify(data));
    }

    alert('Vendor registered successfully!');

    setVendorForm({
  vendor_name: '',
  email: '',
  phone: '',
  address: '',
  gst_number: '',
  tax_identification_number: '',
  bank_account_name: '',
  bank_account_number: '',
  bank_name: '',
  ifsc_code: '',
  branch_name: '',
  status: 'ACTIVE'
});

    fetchVendors();

  } catch (error) {
    alert('Vendor registration failed: ' + error.message);
  }
};
const processOCR = async (invoiceId) => {
  try {
    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/${invoiceId}/ocr/`,
      {
        method: 'POST'
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || 'OCR processing failed');
    }

    alert(
      'OCR completed!\n\n' +
      JSON.stringify(result.extracted_data, null, 2)
    );

  } catch (error) {
    alert('OCR Error: ' + error.message);
  }
};

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

const handleSubmit = async (e) => {
  e.preventDefault();

  if (!invoiceFile) {
    setMessage('Please select an invoice file.');
    return;
  }

  const data = new FormData();

  Object.keys(formData).forEach((key) => {
    if (formData[key] !== '') {
      data.append(key, formData[key]);
    }
  });

  data.append('invoice_file', invoiceFile);

  try {
    setLoading(true);
    setMessage('');

    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/upload/',
      {
        method: 'POST',
        body: data
      }
    );

    const result = await response.json();

    if (!response.ok) {
      const errorMessages = Object.entries(result)
        .map(([field, errors]) => {
          const message = Array.isArray(errors)
            ? errors.join(', ')
            : typeof errors === 'object'
              ? JSON.stringify(errors)
              : errors;

          return `${field}: ${message}`;
        })
        .join(' | ');

      throw new Error(errorMessages || 'Invoice validation failed.');
    }

    setMessage('Invoice uploaded successfully!');

    fetchInvoices();
    fetchDashboard();

    setFormData({
      vendor: '2',
      invoice_number: '',
      invoice_date: '',
      due_date: '',
      total_amount: '',
      status: 'UPLOADED'
    });

    setInvoiceFile(null);
    e.target.reset();

  } catch (error) {
    setMessage('Upload failed: ' + error.message);
  } finally {
    setLoading(false);
  }
};
const updatePaymentStatus = async (paymentId, newStatus) => {
  try {
    const response = await apiFetch(
      `${API_BASE_URL}/api/invoices/payments/${paymentId}/status/`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          payment_status: newStatus,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Unable to update payment status.');
    }

    alert('Payment status updated successfully.');
    fetchPayments();

    fetchDashboard();
  } catch (error) {
    alert(error.message);
  }
};

const handleBulkFileChange = (e) => {
  const files = Array.from(e.target.files);

  setBulkFiles(files);

  setBulkDetails(
    files.map((file) => ({
      invoice_number: file.name.replace(/\.[^/.]+$/, '').slice(0, 100),
      invoice_date: '',
      due_date: '',
      total_amount: '',
      status: 'UPLOADED'
    }))
  );

  setBulkMessage('');
};

const handleBulkDetailChange = (index, field, value) => {
  setBulkDetails((previous) =>
    previous.map((detail, i) =>
      i === index ? { ...detail, [field]: value } : detail
    )
  );
};

const handleBulkUpload = async () => {
  if (bulkFiles.length === 0) {
    setBulkMessage('Please select invoice files.');
    return;
  }

  if (
    bulkDetails.some(
      (detail) =>
        !detail.invoice_number ||
        !detail.invoice_date ||
        !detail.total_amount ||
        Number(detail.total_amount) <= 0
    )
  ) {
    setBulkMessage('Enter invoice number, date and a valid amount for every file.');
    return;
  }

  const data = new FormData();

  bulkFiles.forEach((file) => {
    data.append('invoice_files', file);
  });

  const detailsWithVendor = bulkDetails.map((detail) => ({
    ...detail,
    vendor: formData.vendor
  }));

  data.append('invoice_data', JSON.stringify(detailsWithVendor));

  try {
    setBulkLoading(true);
    setBulkMessage('Uploading invoices...');

    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/bulk-upload/',
      {
        method: 'POST',
        body: data
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(JSON.stringify(result));
    }

    const resultMessage =
      `Bulk upload completed: ${result.successful_uploads} successful, ` +
      `${result.failed_uploads} failed.`;

    setBulkMessage(
      resultMessage + '\n' +
      result.results.map((item) =>
        `${item.file}: ${item.status}` +
        (item.errors ? ` - ${JSON.stringify(item.errors)}` : '')
      ).join('\n')
    );

    setBulkFiles([]);
    setBulkDetails([]);

    fetchInvoices();
    fetchDashboard();

  } catch (error) {
    setBulkMessage('Bulk upload failed: ' + error.message);
  } finally {
    setBulkLoading(false);
  }
};
const handleEmailIngestion = async (e) => {
  e.preventDefault();

  if (!emailFile || !emailVendor || !emailInvoiceNumber.trim()) {
    setEmailMessage('Please provide vendor, invoice number and invoice attachment.');
    return;
  }

  const data = new FormData();
  data.append('source_email', sourceEmail);
  data.append('vendor', emailVendor);
  data.append('invoice_number', emailInvoiceNumber);
  data.append('invoice_date', emailInvoiceDate);
  data.append('total_amount', emailTotalAmount);
  data.append('attachment', emailFile);

  try {
    setEmailLoading(true);
    setEmailMessage('Processing email invoice...');

    const response = await apiFetch(
      API_BASE_URL + '/api/invoices/email-ingestion/',
      {
        method: 'POST',
        body: data
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(JSON.stringify(result));
    }

    setEmailMessage('Email invoice ingested successfully!');
    setEmailFile(null);
    setSourceEmail('');
    setEmailVendor('');
    setEmailInvoiceNumber('');
    setEmailInvoiceDate('');
    setEmailTotalAmount('');

    fetchInvoices();
    fetchDashboard();

  } catch (error) {
    setEmailMessage('Email ingestion failed: ' + error.message);
  } finally {
    setEmailLoading(false);
  }
};
const exportReportCSV = (filename, data) => {
  if (!data || (Array.isArray(data) && data.length === 0)) {
    alert('No data available to export.');
    return;
  }

  const rows = Array.isArray(data)
    ? data
    : typeof data === 'object'
      ? Object.entries(data).map(([key, value]) => ({
          category: key,
          value: value
        }))
      : [{ value: data }];

  const headers = [...new Set(rows.flatMap(row => Object.keys(row)))];

  const csv = [
    headers.join(','),
    ...rows.map(row =>
      headers.map(header => {
        const value = row[header] ?? '';
        return `"${String(
          typeof value === 'object' ? JSON.stringify(value) : value
        ).replace(/"/g, '""')}"`;
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob([csv], {
    type: 'text/csv;charset=utf-8;'
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
};

  if (!authToken) {
    return (
      <div className="auth-screen">
        <form className="auth-card" onSubmit={handleLogin}>
          <h1>Accounts Payable Automation</h1>
          <p>Sign in to access the AP workspace.</p>
          <label>Username</label>
          <input autoComplete="username" value={loginForm.username} onChange={e => setLoginForm({...loginForm, username: e.target.value})} required />
          <label>Password</label>
          <input type="password" autoComplete="current-password" value={loginForm.password} onChange={e => setLoginForm({...loginForm, password: e.target.value})} required />
          {loginError && <p className="auth-error">{loginError}</p>}
          <button type="submit" disabled={loginLoading}>{loginLoading ? 'Signing in...' : 'Sign in'}</button>
        </form>
      </div>
    );
  }

  return (
    <div className="app">

      <aside className="sidebar">
        <h2>AP Automation</h2>

        <nav>
          <p className="active">Dashboard</p>
          <p>Invoice Capture</p>
          <p>OCR & Extraction</p>
          <p>Validation</p>
          <p>PO Matching</p>
          <p>Approvals</p>
          <p>Vendors</p>
          <p>Payments</p>
          <p>Reports</p>
        </nav>
      </aside>

      <main className="main-content">

       <header style={{
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '15px',
  flexWrap: 'wrap'
}}>
  <div>
    <h1>Accounts Payable Dashboard</h1>
    <p>Manage and process your invoices efficiently.</p>
    <p>Logged in as: {currentUser?.username || 'Admin'}</p>
  </div>

  <button
    type="button"
    onClick={handleLogout}
    style={{
      backgroundColor: '#dc3545',
      color: 'white',
      padding: '10px 20px',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      fontWeight: 'bold'
    }}
  >
    Logout
  </button>
</header>
<section className="cards">

  <div className="card">
    <h3>Total Invoices</h3>
    <h2>{dashboardData?.total_invoices ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Pending Approvals</h3>
    <h2>{dashboardData?.pending_approvals ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Total Vendors</h3>
    <h2>{dashboardData?.total_vendors ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Active Vendors</h3>
    <h2>{dashboardData?.active_vendors ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Total Payments</h3>
    <h2>{dashboardData?.total_payments ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Paid Payments</h3>
    <h2>{dashboardData?.paid_payments ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Pending Payments</h3>
    <h2>{dashboardData?.pending_payments ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Total Paid Amount</h3>
    <h2>₹{Number(dashboardData?.total_paid_amount ?? 0).toLocaleString('en-IN')}</h2>
  </div>

  <div className="card">
    <h3>OCR Success Rate</h3>
    <h2>{dashboardData?.ocr_success_rate_percent ?? 0}%</h2>
  </div>

  <div className="card">
    <h3>OCR Processed</h3>
    <h2>{dashboardData?.total_ocr_processed ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Overdue Invoices</h3>
    <h2>{dashboardData?.overdue_invoice_count ?? 0}</h2>
  </div>

  <div className="card">
    <h3>Average Processing Time</h3>
    <h2>{dashboardData?.average_turnaround_seconds ?? 0} sec</h2>
  </div>

</section>
{canViewDashboard && (
<section className="upload-section invoice-list">
  <h2>Vendor Analytics</h2>
  <p>View invoice activity and spending by vendor.</p>

  <div className="table-container">
    <table>
      <thead>
        <tr>
          <th>Vendor Name</th>
          <th>Status</th>
          <th>Invoice Count</th>
          <th>Total Invoice Amount</th>
        </tr>
      </thead>

      <tbody>
        {dashboardData?.vendor_analytics?.length > 0 ? (
          dashboardData.vendor_analytics.map((vendor, index) => (
            <tr key={index}>
              <td>{vendor.vendor_name}</td>
              <td>{vendor.vendor_status}</td>
              <td>{vendor.invoice_count}</td>
              <td>
                ₹{Number(vendor.total_invoice_amount).toLocaleString('en-IN')}
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="4">No vendor analytics available.</td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
</section>
)}
{/* PURCHASE ORDER MANAGEMENT */}
<section className="upload-section">
  <h2>Purchase Order Management</h2>
  <p>Create and manage purchase orders.</p>

  {canManagePurchaseOrders && (
<form onSubmit={submitPurchaseOrder} className="vendor-form">

    <input
      type="text"
      name="po_number"
      placeholder="PO Number"
      value={poFormData.po_number}
      onChange={handlePoChange}
      required
    />

    <select
      name="vendor"
      value={poFormData.vendor}
      onChange={handlePoChange}
      required
    >
      <option value="">Select Vendor</option>
      {vendors.filter(v => v.status === 'ACTIVE').map(v => (
        <option key={v.id} value={v.id}>{v.vendor_name}</option>
      ))}
    </select>

    <input
      type="date"
      name="po_date"
      value={poFormData.po_date}
      onChange={handlePoChange}
      required
    />

    <h3>PO Line Items</h3>

    {poFormData.line_items.map((item, index) => (
      <div key={index} className="form-row">

        <input
          type="text"
          name="description"
          placeholder="Item Description"
          value={item.description}
          onChange={(e) => handlePoItemChange(index, e)}
          required
        />

        <input
          type="number"
          name="quantity"
          placeholder="Quantity"
          min="0.01"
          step="0.01"
          value={item.quantity}
          onChange={(e) => handlePoItemChange(index, e)}
          required
        />

        <input
          type="number"
          name="unit_price"
          placeholder="Unit Price"
          min="0.01"
          step="0.01"
          value={item.unit_price}
          onChange={(e) => handlePoItemChange(index, e)}
          required
        />

        <input
          type="number"
          placeholder="Item Amount"
          value={item.amount}
          readOnly
        />

      </div>
    ))}

    <button type="button" onClick={addPoItem}>
      + Add PO Item
    </button>

    <h3>PO Total: ₹{poFormData.total_amount || '0.00'}</h3>

    <button type="submit">Create Purchase Order</button>
  </form>
)}

  <h3>Saved Purchase Orders</h3>

  <div className="table-container">
    <table>
      <thead>
        <tr>
          <th>PO Number</th>
          <th>Vendor ID</th>
          <th>Date</th>
          <th>Total Amount</th>
        </tr>
      </thead>
      <tbody>
        {purchaseOrders.map(po => (
          <tr key={po.id}>
            <td>{po.po_number}</td>
            <td>{po.vendor}</td>
            <td>{po.po_date}</td>
            <td>₹{po.total_amount}</td>
          </tr>
        ))}
        {purchaseOrders.length === 0 && (
          <tr><td colSpan="4">No purchase orders created yet.</td></tr>
        )}
      </tbody>
    </table>
  </div>
</section>


{/* GOODS RECEIPT NOTE MANAGEMENT */}
<section className="upload-section">
  <h2>Goods Receipt Note (GRN)</h2>
  <p>Record goods received against a purchase order.</p>

  {canManagePurchaseOrders && (
<form onSubmit={submitGRN} className="vendor-form">

    <input
      type="text"
      name="grn_number"
      placeholder="GRN Number"
      value={grnFormData.grn_number}
      onChange={handleGrnChange}
      required
    />

    <select
      name="purchase_order"
      value={grnFormData.purchase_order}
      onChange={handleGrnChange}
      required
    >
      <option value="">Select Purchase Order</option>
      {purchaseOrders.map(po => (
        <option key={po.id} value={po.id}>
          {po.po_number}
        </option>
      ))}
    </select>

    <input
      type="date"
      name="received_date"
      value={grnFormData.received_date}
      onChange={handleGrnChange}
      required
    />

    <h3>Received Items</h3>

    {grnFormData.line_items.map((item, index) => (
      <div key={index} className="form-row">

        <input
          type="text"
          name="description"
          placeholder="Item Description"
          value={item.description}
          onChange={(e) => handleGrnItemChange(index, e)}
          required
        />

        <input
          type="number"
          name="quantity_received"
          placeholder="Quantity Received"
          min="0.01"
          step="0.01"
          value={item.quantity_received}
          onChange={(e) => handleGrnItemChange(index, e)}
          required
        />

      </div>
    ))}

    <button type="button" onClick={addGrnItem}>
      + Add Received Item
    </button>

    <button type="submit">Create GRN</button>
  </form>
)}

  <h3>Saved Goods Receipt Notes</h3>

  <div className="table-container">
    <table>
      <thead>
        <tr>
          <th>GRN Number</th>
          <th>Purchase Order ID</th>
          <th>Received Date</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {grns.map(grn => (
          <tr key={grn.id}>
            <td>{grn.grn_number}</td>
            <td>{grn.purchase_order}</td>
            <td>{grn.received_date}</td>
            <td>{grn.status}</td>
          </tr>
        ))}
        {grns.length === 0 && (
          <tr><td colSpan="4">No GRNs created yet.</td></tr>
        )}
      </tbody>
    </table>
  </div>
</section>
{/* PO MATCHING RESULTS */}
{matchingResult && (
  <section className="upload-section">
    <h2>Invoice Matching Results</h2>

    <div className="card">
      <h3>Invoice Number: {matchingResult.invoice_number}</h3>
      <p>Purchase Order: {matchingResult.po_number}</p>

      <h3>
        Overall Status:
        <span className="status-badge">
          {matchingResult.overall_status}
        </span>
      </h3>
    </div>

    <h3>2-Way Matching Results</h3>

    <pre>
      {JSON.stringify(
        matchingResult.two_way_matching,
        null,
        2
      )}
    </pre>

    {Object.keys(matchingResult.three_way_matching || {}).length > 0 && (
      <>
        <h3>3-Way Matching Results</h3>
        <pre>
          {JSON.stringify(
            matchingResult.three_way_matching,
            null,
            2
          )}
        </pre>
      </>
    )}
  </section>
)}
<section className="vendor-section">
  <h2>Vendor Management</h2>

  {canManageVendors && (
<form onSubmit={handleVendorSubmit} className="vendor-form">

    <h3>Basic Information</h3>

    <input
      type="text"
      placeholder="Vendor Name"
      value={vendorForm.vendor_name}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        vendor_name: e.target.value
      })}
      required
    />

    <input
      type="email"
      placeholder="Email"
      value={vendorForm.email}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        email: e.target.value
      })}
      required
    />

    <input
      type="text"
      placeholder="Phone"
      value={vendorForm.phone}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        phone: e.target.value
      })}
    />

    <input
      type="text"
      placeholder="Address"
      value={vendorForm.address}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        address: e.target.value
      })}
    />

    <input
      type="text"
      placeholder="GST Number"
      value={vendorForm.gst_number}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        gst_number: e.target.value.toUpperCase()
      })}
    />

    <input
      type="text"
      placeholder="Tax Identification Number"
      value={vendorForm.tax_identification_number}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        tax_identification_number: e.target.value
      })}
    />

    <h3>Bank Account Details</h3>

    <input
      type="text"
      placeholder="Bank Account Name"
      value={vendorForm.bank_account_name}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        bank_account_name: e.target.value
      })}
      required
    />

    <input
      type="text"
      placeholder="Bank Account Number"
      value={vendorForm.bank_account_number}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        bank_account_number: e.target.value
      })}
      required
    />

    <input
      type="text"
      placeholder="Bank Name"
      value={vendorForm.bank_name}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        bank_name: e.target.value
      })}
      required
    />

    <input
      type="text"
      placeholder="IFSC Code"
      value={vendorForm.ifsc_code}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        ifsc_code: e.target.value.toUpperCase()
      })}
      required
    />

    <input
      type="text"
      placeholder="Branch Name"
      value={vendorForm.branch_name}
      onChange={(e) => setVendorForm({
        ...vendorForm,
        branch_name: e.target.value
      })}
      required
    />

    <button type="submit">Register Vendor</button>

  </form>
)}

  <h3>Registered Vendors</h3>

  <button type="button" onClick={fetchVendors}>
    Refresh Vendors
  </button>

  <div className="vendor-list">
    {vendors.map((vendor) => (
      <div className="vendor-item" key={vendor.id}>
        <div>
          <strong>{vendor.vendor_name}</strong>
          <p>{vendor.email}</p>
        </div>
        <span>{vendor.status}</span>
      </div>
    ))}
  </div>

</section>

        <section className="upload-section">
                  {canUploadInvoices && (
          <section className="bulk-upload-section">
  <h2>Bulk Invoice Upload</h2>
  <p>Select multiple invoices and enter details for each file.</p>

<div
  className="bulk-drop-zone"
  onDragOver={(e) => e.preventDefault()}
  onDrop={(e) => {
    e.preventDefault();

    const files = Array.from(e.dataTransfer.files).filter((file) =>
      /\.(pdf|jpg|jpeg|png|tiff)$/i.test(file.name)
    );

    setBulkFiles(files);

    setBulkDetails(
      files.map((file) => ({
        invoice_number: file.name.replace(/\.[^/.]+$/, '').slice(0, 100),
        invoice_date: '',
        due_date: '',
        total_amount: '',
        status: 'UPLOADED'
      }))
    );

    setBulkMessage('');
  }}
>
  <p>Drag and drop invoice files here</p>
  <p>or</p>
  <input
    type="file"
    multiple
    accept=".pdf,.jpg,.jpeg,.png,.tiff"
    onChange={handleBulkFileChange}
  />
</div>

  {bulkFiles.map((file, index) => (
    <div className="bulk-file-item" key={index}>
      <h4>{file.name}</h4>

      <input
        type="text"
        placeholder="Invoice Number"
        value={bulkDetails[index]?.invoice_number || ''}
        onChange={(e) =>
          handleBulkDetailChange(index, 'invoice_number', e.target.value)
        }
      />

      <input
        type="date"
        value={bulkDetails[index]?.invoice_date || ''}
        onChange={(e) =>
          handleBulkDetailChange(index, 'invoice_date', e.target.value)
        }
      />

      <input
        type="date"
        placeholder="Due Date"
        value={bulkDetails[index]?.due_date || ''}
        onChange={(e) =>
          handleBulkDetailChange(index, 'due_date', e.target.value)
        }
      />

      <input
        type="number"
        placeholder="Total Amount"
        value={bulkDetails[index]?.total_amount || ''}
        onChange={(e) =>
          handleBulkDetailChange(index, 'total_amount', e.target.value)
        }
      />
    </div>
  ))}

  <button
    type="button"
    onClick={handleBulkUpload}
    disabled={bulkLoading}
  >
    {bulkLoading ? 'Uploading...' : 'Upload All Invoices'}
  </button>

  {bulkMessage && (
    <pre className="bulk-upload-message">{bulkMessage}</pre>
  )}
</section>
)}
</section>
{canUploadInvoices && (
<section className="upload-section">

  <h2>Email Invoice Ingestion</h2>

  <p>Upload invoice attachments received through email.</p>

  <form onSubmit={handleEmailIngestion}>

    <input
      type="email"
      placeholder="Source Email Address"
      value={sourceEmail}
      onChange={(e) => setSourceEmail(e.target.value)}
      required
    />

    <input
  type="text"
  placeholder="Invoice Number"
  value={emailInvoiceNumber}
  onChange={(e) => setEmailInvoiceNumber(e.target.value)}
  required
/>

<input
  type="date"
  value={emailInvoiceDate}
  onChange={(e) => setEmailInvoiceDate(e.target.value)}
  required
/>
<input
  type="number"
  placeholder="Total Invoice Amount"
  value={emailTotalAmount}
  onChange={(e) => setEmailTotalAmount(e.target.value)}
  min="0.01"
  step="0.01"
  required
/>

<select
  value={emailVendor}
  onChange={(e) => setEmailVendor(e.target.value)}
  required
>
  <option value="">Select Vendor</option>
  {vendors
    .filter(vendor => vendor.status === 'ACTIVE')
    .map(vendor => (
      <option key={vendor.id} value={vendor.id}>
        {vendor.vendor_name}
      </option>
    ))}
</select>

    <input
      type="file"
      accept=".pdf,.jpg,.jpeg,.png,.tiff"
      onChange={(e) => setEmailFile(e.target.files[0])}
      required
    />

    <button type="submit" disabled={emailLoading}>
      {emailLoading ? 'Processing...' : 'Ingest Email Invoice'}
    </button>

  </form>

  {emailMessage && (
    <p>{emailMessage}</p>
  )}

</section>
)}

          {canUploadInvoices && (
<section className="upload-section">
  <h2>Invoice Capture</h2>

          <p>Upload your vendor invoices for processing.</p>

          <form onSubmit={handleSubmit}>

            <div className="form-grid">

             <div className="form-group">
  <label>Select Vendor</label>
  <select
    name="vendor"
    value={formData.vendor}
    onChange={handleChange}
    required
  >
    <option value="">Select a vendor</option>

    {vendors
      .filter((vendor) => vendor.status === 'ACTIVE')
      .map((vendor) => (
        <option key={vendor.id} value={vendor.id}>
          {vendor.vendor_name}
        </option>
      ))}
  </select>
</div>

              <div className="form-group">
                <label>Invoice Number</label>
                <input
                  type="text"
                  name="invoice_number"
                  value={formData.invoice_number}
                  onChange={handleChange}
                  placeholder="Enter invoice number"
                  required
                />
              </div>

              <div className="form-group">
                <label>Invoice Date</label>
                <input
                  type="date"
                  name="invoice_date"
                  value={formData.invoice_date}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>Due Date</label>
                <input
                  type="date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label>Total Amount</label>
                <input
                  type="number"
                  step="0.01"
                  name="total_amount"
                  value={formData.total_amount}
                  onChange={handleChange}
                  placeholder="Enter amount"
                />
              </div>

              <div className="form-group">
                <label>Status</label>
                <select
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                >
                  <option value="UPLOADED">Uploaded</option>
                  <option value="PROCESSING">Processing</option>
                  <option value="PROCESSED">Processed</option>
                  <option value="FAILED">Failed</option>
                </select>
              </div>

            </div>

            <div className="form-group file-input">
              <label>Select Invoice (PDF / JPG / PNG / TIFF)</label>

              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.tiff"
                onChange={(e) => setInvoiceFile(e.target.files[0])}
                required
              />
            </div>

            <button type="submit" disabled={loading}>
              {loading ? 'Uploading...' : 'Upload Invoice'}
            </button>

            {message && (
              <p className="message">{message}</p>
            )}

          </form>

        </section>
)}
                {/* Invoice List */}

        <section className="upload-section invoice-list">

          <h2>Recent Invoices</h2>

          <p>View all invoices uploaded to the system.</p>

          {fetchError && (
            <p className="message">
              {fetchError}
            </p>
          )}

          <div className="table-container">

            <table>

              <thead>
                <tr>
                  <th>Invoice Number</th>
                  <th>Vendor ID</th>
                  <th>Invoice Date</th>
                  <th>Due Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Document</th>
                </tr>
              </thead>

              <tbody>

                {invoices.length > 0 ? (

                  invoices.map((invoice) => (

                    <tr key={invoice.id}>

                      <td>{invoice.invoice_number}</td>

                      <td>{invoice.vendor}</td>

                      <td>{invoice.invoice_date || '-'}</td>

                      <td>{invoice.due_date || '-'}</td>

                      <td>
                        ₹{invoice.total_amount || '0.00'}
                      </td>

                      <td>
                        <span className="status-badge">
                          {invoice.status}
                        </span>
                      </td>
                      <td>
  <a
    href={invoice.invoice_file}
    target="_blank"
    rel="noopener noreferrer"
  >
    View File
  </a>

  <br />

  {canUploadInvoices && (
  <button
    type="button"
    onClick={() => processOCR(invoice.id)}
  >
    Process OCR
  </button>
)}
 {canManagePayments && (
  <button
    onClick={() => createPayment(invoice.id)}
    disabled={paymentLoading}
  >
    {paymentLoading ? 'Processing...' : 'Create Payment'}
  </button>
)}

<br />

{canUploadInvoices && (
  <button
    type="button"
    onClick={() => createApproval(invoice.id)}
  >
    Create Approval
  </button>
)}
<br />

{canManagePurchaseOrders && (
  <button
    type="button"
    onClick={() => matchPurchaseOrder(invoice.id)}
  >
    Match Purchase Order
  </button>
)}
</td>
   

                    </tr>

                  ))

                ) : (

                  <tr>
                    <td colSpan="7">
                      No invoices available.
                    </td>
                  </tr>

                )}

              </tbody>

            </table>

          </div>

        </section>
             {/* Payment Management */}

{canManagePayments && (
<section className="upload-section invoice-list">

          <h2>Payment Management</h2>

          <p>Track and manage invoice payment requests.</p>

          <button type="button" onClick={fetchPayments}>
            Refresh Payments
          </button>

          <div className="table-container">

            <table>
              <thead>
                <tr>
                  <th>Payment Reference</th>
                  <th>Invoice ID</th>
                  <th>Amount</th>
                  <th>Payment Method</th>
                  <th>Payment Date</th>
                  <th>Bank Reference</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {payments.length > 0 ? (
                  payments.map((payment) => (
                    <tr key={payment.id}>
                      <td>{payment.payment_reference}</td>
                      <td>{payment.invoice}</td>
                      <td>₹{payment.amount}</td>
                      <td>{payment.payment_method}</td>
                      <td>{payment.payment_date || '-'}</td>
                      <td>{payment.bank_reference || '-'}</td>
                     <td>
  <span className="status-badge">
    {payment.payment_status}
  </span>

  <br />

  <select
    value={payment.payment_status}
    onChange={(e) =>
      updatePaymentStatus(payment.id, e.target.value)
    }
  >
    <option value="REQUESTED">Requested</option>
    <option value="PROCESSING">Processing</option>
    <option value="PAID">Paid</option>
    <option value="FAILED">Failed</option>
  </select>
</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7">No payment records available.</td>
                  </tr>
                )}
              </tbody>
            </table>

          </div>

        </section>
)}
 {/* APPROVAL RULE CONFIGURATION */}

{canConfigureApprovalRules && (
<section className="upload-section">

  <h2>Approval Rule Configuration</h2>
  <p>Configure approval levels based on invoice amounts.</p>

  <form onSubmit={submitApprovalRule} className="vendor-form">

    <input
      type="text"
      name="rule_name"
      placeholder="Rule Name"
      value={approvalRuleForm.rule_name}
      onChange={handleApprovalRuleChange}
      required
    />
    <input
  type="number"
  name="approval_level"
  placeholder="Approval Level (1 = First)"
  min="1"
  value={approvalRuleForm.approval_level}
  onChange={handleApprovalRuleChange}
  required
/>

    <input
      type="number"
      name="minimum_amount"
      placeholder="Minimum Amount"
      min="0"
      step="0.01"
      value={approvalRuleForm.minimum_amount}
      onChange={handleApprovalRuleChange}
      required
    />

    <input
      type="number"
      name="maximum_amount"
      placeholder="Maximum Amount (Leave blank for no limit)"
      min="0"
      step="0.01"
      value={approvalRuleForm.maximum_amount}
      onChange={handleApprovalRuleChange}
    />

    <input
      type="text"
      name="approver_role"
      placeholder="Approver Role (e.g. MANAGER)"
      value={approvalRuleForm.approver_role}
      onChange={handleApprovalRuleChange}
      required
    />

    <label>
      <input
        type="checkbox"
        name="is_active"
        checked={approvalRuleForm.is_active}
        onChange={handleApprovalRuleChange}
      />
      Active Rule
    </label>

    <button type="submit">
      Create Approval Rule
    </button>

  </form>

  <h3>Configured Approval Rules</h3>

  <div className="table-container">
    <table>
      <thead>
        <tr>
         <th>Rule Name</th>
         <th>Approval Level</th>
         <th>Minimum Amount</th>
         <th>Maximum Amount</th>
         <th>Approver Role</th>
         <th>Status</th>
        </tr>
      </thead>

      <tbody>
        {approvalRules.length > 0 ? (
          approvalRules.map(rule => (
            <tr key={rule.id}>
  <td>{rule.rule_name}</td>
  <td>{rule.approval_level}</td>
  <td>₹{rule.minimum_amount}</td>
  <td>
    {rule.maximum_amount
      ? `₹${rule.maximum_amount}`
      : 'No Limit'}
  </td>
  <td>{rule.approver_role}</td>
  <td>{rule.is_active ? 'Active' : 'Inactive'}</td>
</tr>
          ))
        ) : (
          <tr>
            <td colSpan="6">No approval rules configured.</td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
</section>
)}
        {canProcessApprovals && (
<section className="upload-section invoice-list">
  <h2>Approval Management</h2>
  <p>Review and process invoice approval requests.</p>

  <button type="button" onClick={fetchApprovals}>
    Refresh Approvals
  </button>

  <div className="table-container">
    <table>
      <thead>
        <tr>
          <th>Approval ID</th>
          <th>Invoice ID</th>
          <th>Approver Role</th>
          <th>Status</th>
          <th>Comments</th>
          <th>Created</th>
          <th>Action</th>
        </tr>
      </thead>

      <tbody>
        {approvals.length > 0 ? (
          approvals.map((approval) => (
            <tr key={approval.id}>
              <td>{approval.id}</td>
              <td>{approval.invoice}</td>
              <td>{approval.approver_role}</td>
              <td>{approval.status}</td>
              <td>{approval.comments || '-'}</td>
              <td>
                {approval.created_at
                  ? new Date(approval.created_at).toLocaleDateString()
                  : '-'}
              </td>
              <td>
                {approval.status === 'PENDING' ? (
                  <>
                    <button
                      type="button"
                      onClick={() =>
                        handleApprovalAction(approval.id, 'APPROVED')
                      }
                    >
                      Approve
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleApprovalAction(approval.id, 'REJECTED')
                      }
                    >
                      Reject
                    </button>
                  </>
                ) : (
                  approval.status
                )}
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="7">No approval requests available.</td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
</section>
)}
{canViewReports && (
<section className="upload-section invoice-list">
  <h2>Reports & Analytics</h2>
  <p>Monitor invoice status, aging, exceptions, audit activities and GST details.</p>

  <button type="button" onClick={fetchReports}>
    Refresh Reports
  </button>
  <div className="report-export-buttons">
  <button type="button" onClick={() => exportReportCSV('invoice-status.csv', reports?.invoice_status_report)}>
    Export Invoice Status
  </button>

  <button type="button" onClick={() => exportReportCSV('ap-aging.csv', reports?.ap_aging_report)}>
    Export AP Aging
  </button>

  <button type="button" onClick={() => exportReportCSV('overdue-invoices.csv', reports?.overdue_invoices)}>
    Export Overdue Invoices
  </button>

  <button type="button" onClick={() => exportReportCSV('exceptions.csv', reports?.exception_report)}>
    Export Exceptions
  </button>

  <button type="button" onClick={() => exportReportCSV('audit-logs.csv', reports?.audit_log_report)}>
    Export Audit Logs
  </button>

  <button type="button" onClick={() => exportReportCSV('gst-tax-report.csv', reports?.gst_tax_report)}>
    Export GST & Tax
  </button>
</div>

  {reports ? (
    <>
      <h3>1. Invoice Status Report</h3>
      <div className="dashboard-cards">
        {[
          ['Total Invoices', reports.invoice_status_report.total],
          ['Uploaded', reports.invoice_status_report.uploaded],
          ['Processing', reports.invoice_status_report.processing],
          ['Processed', reports.invoice_status_report.processed],
          ['Failed', reports.invoice_status_report.failed]
        ].map(([label, value]) => (
          <div className="card" key={label}>
            <h3>{label}</h3>
            <p>{value ?? 0}</p>
          </div>
        ))}
      </div>

      <h3>2. Accounts Payable Aging Report</h3>
      <div className="dashboard-cards">
        {Object.entries(reports.ap_aging_report || {}).map(([period, amount]) => (
          <div className="card" key={period}>
            <h3>{period.replaceAll('_', ' ').toUpperCase()}</h3>
            <p>₹{Number(amount).toLocaleString('en-IN')}</p>
          </div>
        ))}
      </div>

      <h3>3. Overdue Invoices</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Invoice Details</th>
              <th>Information</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(reports.overdue_invoices) &&
            reports.overdue_invoices.length > 0 ? (
              reports.overdue_invoices.map((item, index) => (
                <tr key={index}>
                  <td>{item.invoice_number || `Invoice ${index + 1}`}</td>
                  <td>{Object.entries(item).map(([key, value]) =>
                    `${key.replaceAll('_', ' ')}: ${value ?? '-'}`
                  ).join(' | ')}</td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="2">No overdue invoices found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <h3>4. Exception Report</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Exception Details</th>
              <th>Information</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(reports.exception_report) &&
            reports.exception_report.length > 0 ? (
              reports.exception_report.map((item, index) => (
                <tr key={index}>
                  <td>{item.invoice_number || `Exception ${index + 1}`}</td>
                  <td>{Object.entries(item).map(([key, value]) =>
                    `${key.replaceAll('_', ' ')}: ${value ?? '-'}`
                  ).join(' | ')}</td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="2">No exceptions found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <h3>5. Audit Log Report</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Audit Activity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(reports.audit_log_report) &&
            reports.audit_log_report.length > 0 ? (
              reports.audit_log_report.map((item, index) => (
                <tr key={index}>
                  <td>{item.action || `Activity ${index + 1}`}</td>
                  <td>{Object.entries(item).map(([key, value]) =>
                    `${key.replaceAll('_', ' ')}: ${value ?? '-'}`
                  ).join(' | ')}</td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="2">No audit activities found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <h3>6. GST & Tax Report</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Vendor</th>
              <th>GST Number</th>
              <th>Total Invoice Amount</th>
            </tr>
          </thead>
          <tbody>
            {reports.gst_tax_report.map((item, index) => (
              <tr key={index}>
                <td>{item.vendor}</td>
                <td>{item.gst_number || '-'}</td>
                <td>
                  ₹{Number(item.total_invoice_amount).toLocaleString('en-IN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  ) : (
    <p>Loading reports...</p>
  )}
</section>
)}

{currentUser?.role === 'Admin' && (
  <section className="upload-section invoice-list">
    <h2>User Management</h2>
    <p>Create employee accounts and manage their access.</p>

    <form onSubmit={handleEmployeeSubmit}>
      <input
        type="text"
        placeholder="Username"
        value={employeeForm.username}
        onChange={(e) => setEmployeeForm({
          ...employeeForm,
          username: e.target.value
        })}
        required
      />

      <input
        type="email"
        placeholder="Email"
        value={employeeForm.email}
        onChange={(e) => setEmployeeForm({
          ...employeeForm,
          email: e.target.value
        })}
        required
      />

      <input
        type="text"
        placeholder="First Name"
        value={employeeForm.first_name}
        onChange={(e) => setEmployeeForm({
          ...employeeForm,
          first_name: e.target.value
        })}
      />

      <input
        type="text"
        placeholder="Last Name"
        value={employeeForm.last_name}
        onChange={(e) => setEmployeeForm({
          ...employeeForm,
          last_name: e.target.value
        })}
      />

      <select
        value={employeeForm.role}
        onChange={(e) => setEmployeeForm({
          ...employeeForm,
          role: e.target.value
        })}
      >
        <option value="AP_Clerk">AP Clerk</option>
        <option value="Approver">Approver</option>
        <option value="Finance">Finance</option>
        <option value="Vendor_Manager">Vendor Manager</option>
        <option value="MANAGER">Manager</option>
      </select>

      <input
        type="password"
        placeholder="Temporary Password (minimum 8 characters)"
        value={employeeForm.password}
        onChange={(e) => setEmployeeForm({
          ...employeeForm,
          password: e.target.value
        })}
        minLength={8}
        required
      />

      <button type="submit" disabled={employeeLoading}>
        {employeeLoading ? 'Creating...' : 'Create Employee'}
      </button>
    </form>

    {employeeMessage && <p>{employeeMessage}</p>}

    <h3>Employee Accounts</h3>

    <button type="button" onClick={fetchEmployees}>
      Refresh Employees
    </button>

    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {employees.length > 0 ? (
            employees.map((employee) => (
              <tr key={employee.id}>
                <td>{employee.username}</td>
                <td>
                  {employee.first_name} {employee.last_name}
                </td>
                <td>{employee.email}</td>
                <td>{employee.role_name}</td>
                <td>{employee.is_active ? 'Active' : 'Inactive'}</td>
                <td>
                  <button
                    type="button"
                    onClick={() => toggleEmployeeStatus(employee)}
                  >
                    {employee.is_active ? 'Deactivate' : 'Activate'}
                  </button>

                  <button
                    type="button"
                    onClick={() => resetEmployeePassword(employee)}
                  >
                    Reset Password
                  </button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6">No employee accounts created yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  </section>
)}


      </main>

    </div>
  );
}

export default App;