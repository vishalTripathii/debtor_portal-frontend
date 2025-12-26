import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  IconButton,
  InputAdornment,
  Avatar,
  LinearProgress,
  Select,
  MenuItem,
  InputLabel,
  Snackbar,
  Checkbox
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckIcon,
  Payment as PaymentIcon,
  Schedule as ScheduleIcon,
  Description as DocumentIcon,
  GetApp as DownloadIcon,
  Send as SendIcon,
  School as EducationIcon,
  TrendingUp as GrowthIcon,
  AccountBalance as BudgetIcon,
  EmojiEvents as AchievementIcon,
  Lightbulb as TipIcon,
  Calculate as CalculatorIcon,
  AttachFile as AttachFileIcon,
  SupportAgent as SupportIcon
} from '@mui/icons-material';
import { useActivityLog } from '../context/ActivityLogContext';
import { useLanguage } from '../context/LanguageContext';
import LanguageSwitcher from './LanguageSwitcher';
import MaintenancePage from './MaintenancePage';
import { debtorApi, settingsApi, qrApi } from '../services/api';

const DebtorPortal = () => {
  const { addLog } = useActivityLog();
  const { t, language } = useLanguage();
  const currentUser = 'Debtor User';
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginStep, setLoginStep] = useState(0);
  const [loginMethod, setLoginMethod] = useState('national_id'); // national_id, email
  const [loginValue, setLoginValue] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [otp, setOtp] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [paymentDialog, setPaymentDialog] = useState(false);
  const [settlementDialog, setSettlementDialog] = useState(false);
  const [paymentType, setPaymentType] = useState('full');
  const [customAmount, setCustomAmount] = useState('');

  // Multi-account states
  const [accounts, setAccounts] = useState([]); // All accounts for this national_id
  const [selectedAccount, setSelectedAccount] = useState(null); // Currently selected account for payment
  const [totalBalance, setTotalBalance] = useState(0);

  // Payment dialog states
  const [paymentAmount, setPaymentAmount] = useState('');
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptPreview, setReceiptPreview] = useState(null);
  const [bankDetails, setBankDetails] = useState(null);

  // 2-step payment flow states
  const [paymentStep, setPaymentStep] = useState(1); // 1 = select type, 2 = QR + transaction
  const [transactionNumber, setTransactionNumber] = useState('');
  const [accountQrCode, setAccountQrCode] = useState(null);
  const [qrCodeLoading, setQrCodeLoading] = useState(false);
  const [notReadyDialog, setNotReadyDialog] = useState(false);
  const [nonPaymentReason, setNonPaymentReason] = useState('');
  const [instalmentPlan, setInstalmentPlan] = useState('Others');
  const [nonPaymentNotes, setNonPaymentNotes] = useState('');
  const [preferredContactDate, setPreferredContactDate] = useState('');
  const [preferredContactTime, setPreferredContactTime] = useState('');
  const [preferredContactMethod, setPreferredContactMethod] = useState('');
  const [preferredContactValue, setPreferredContactValue] = useState('');
  const [successDialog, setSuccessDialog] = useState(false);
  const [successMessage, setSuccessMessage] = useState({ title: '', details: [] });
  const [showOTP, setShowOTP] = useState(false);
  const [showPdpaDialog, setShowPdpaDialog] = useState(false);
  const [pdpaConsenting, setPdpaConsenting] = useState(false);
  const [paymentTermsConsent, setPaymentTermsConsent] = useState(false);
  const [digitalReceiptConsent, setDigitalReceiptConsent] = useState(false);
  const [showPaymentConsentDialog, setShowPaymentConsentDialog] = useState(false);
  const [paymentConsentLoading, setPaymentConsentLoading] = useState(false);
  const [budgetIncome, setBudgetIncome] = useState('');
  const [budgetExpenses, setBudgetExpenses] = useState('');
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizScore, setQuizScore] = useState(null);

  // API Integration states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');

  // LINE Support QR Code
  const [lineQrCode, setLineQrCode] = useState(null);
  const [showLoginSupport, setShowLoginSupport] = useState(false);

  // System Settings
  const [systemSettings, setSystemSettings] = useState(null);

  // Snackbar notification state
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info', duration: 6000 });

  // Show snackbar notification with optional duration (default 6 seconds)
  const showNotification = (message, severity = 'info', duration = 6000) => {
    setSnackbar({ open: true, message, severity, duration });
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  // Helper function to translate known error messages
  const getTranslatedError = (errorMessage) => {
    const errorMap = {
      'No accounts found. Please check your National ID.': t('noAccountsFound'),
      'Your session has expired. Please log in again.': t('sessionExpired'),
      'An error occurred. Please try again.': t('genericError'),
    };
    return errorMap[errorMessage] || errorMessage;
  };

  // Session timeout constant (15 minutes in milliseconds)
  const SESSION_TIMEOUT = 15 * 60 * 1000;

  // Format currency in Thai Baht
  const formatCurrency = (amount) => {
    return `฿${(amount || 0).toLocaleString()}`;
  };

  // Format date only (no time) for fields like loan_contract_date
  const formatDateOnly = (dateString) => {
    if (!dateString || dateString === 'N/A' || dateString === '-') return '-';
    // If it already looks like a date-only string (YYYY-MM-DD), return as is
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) return dateString;
    // Extract date part if time is included
    const dateOnly = dateString.split(' ')[0].split('T')[0];
    return dateOnly || '-';
  };

  // Update Contact Information states
  const [updateContactDialog, setUpdateContactDialog] = useState(false);
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [phoneOTP, setPhoneOTP] = useState('');
  const [emailOTP, setEmailOTP] = useState('');
  const [phoneOTPSent, setPhoneOTPSent] = useState(false);
  const [emailOTPSent, setEmailOTPSent] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(false);

  // Restore session from localStorage on component mount
  useEffect(() => {
    const checkSession = () => {
      const storedSession = localStorage.getItem('debtorSession');
      const token = localStorage.getItem('debtorToken');

      if (storedSession && token) {
        try {
          const session = JSON.parse(storedSession);
          const loginTime = session.loginTime;
          const now = Date.now();

          // Check if session has expired (15 minutes)
          if (now - loginTime > SESSION_TIMEOUT) {
            // Session expired - clear and logout
            handleLogout(true);
            return;
          }

          // Restore session - now with multi-account support
          setAccounts(session.accounts || []);
          setTotalBalance(session.totalBalance || 0);
          setNationalId(session.nationalId || '');
          setIsLoggedIn(true);

          // Check if PDPA consent was given in this session
          // If not, show the dialog (they refreshed before consenting)
          if (!session.pdpaConsentGivenThisSession) {
            setShowPdpaDialog(true);
          }
        } catch (e) {
          // Invalid session data - clear it
          handleLogout(true);
        }
      }
    };

    checkSession();
  }, []);

  // Session activity tracker - reset timeout on activity
  useEffect(() => {
    if (!isLoggedIn) return;

    const updateActivity = () => {
      const storedSession = localStorage.getItem('debtorSession');
      if (storedSession) {
        try {
          const session = JSON.parse(storedSession);
          session.loginTime = Date.now(); // Reset the timer on activity
          localStorage.setItem('debtorSession', JSON.stringify(session));
        } catch (e) {
          // Ignore errors
        }
      }
    };

    // Update activity on user interaction
    const events = ['click', 'keypress', 'scroll', 'mousemove'];
    events.forEach(event => window.addEventListener(event, updateActivity));

    // Check session expiry every minute
    const intervalId = setInterval(() => {
      const storedSession = localStorage.getItem('debtorSession');
      if (storedSession) {
        try {
          const session = JSON.parse(storedSession);
          if (Date.now() - session.loginTime > SESSION_TIMEOUT) {
            handleLogout(true);
          }
        } catch (e) {
          handleLogout(true);
        }
      }
    }, 60000); // Check every minute

    return () => {
      events.forEach(event => window.removeEventListener(event, updateActivity));
      clearInterval(intervalId);
    };
  }, [isLoggedIn]);

  // Fetch global LINE QR code on component mount (same for all users - contact support)
  useEffect(() => {
    const fetchLineQrCode = async () => {
      try {
        const response = await qrApi.getGlobalLineQr();
        if (response.success && response.qr_code?.image) {
          setLineQrCode(response.qr_code.image);
          console.log('✅ Global LINE QR loaded for contact support');
        }
      } catch (error) {
        console.error('Error fetching global LINE QR code:', error);
      }
    };
    fetchLineQrCode();
  }, []);

  // Test QR fetching with National ID (for testing purposes)
  const testNationalIdQR = async (nationalId) => {
    if (!nationalId) return null;
    
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
      const response = await fetch(`${API_BASE_URL}/qr/national-id/${nationalId}/`, {
        method: 'GET',
      });
      const data = await response.json();
      
      if (data.success) {
        console.log(`🎯 QR Test for National ID ${nationalId}:`, {
          type: data.type,
          hasQR: !!data.qr_code?.image,
          accountInfo: data.account_info
        });
        return data;
      }
    } catch (error) {
      console.log(`❌ QR Test failed for National ID ${nationalId}:`, error.message);
    }
    return null;
  };

  // Fetch system settings for feature toggles and bank details
  useEffect(() => {
    const fetchSystemSettings = async () => {
      try {
        const response = await settingsApi.getSystemSettings();
        if (response.success) {
          setSystemSettings(response.settings);
          // Set bank details if available
          if (response.settings?.bank_account) {
            setBankDetails(response.settings.bank_account);
          }
        }
      } catch (error) {
        console.error('Error fetching system settings:', error);
      }
    };
    fetchSystemSettings();
  }, []);

  // Logout handler
  const handleLogout = (sessionExpired = false) => {
    localStorage.removeItem('debtorToken');
    localStorage.removeItem('debtorSession');
    setIsLoggedIn(false);
    setAccounts([]);
    setSelectedAccount(null);
    setTotalBalance(0);
    setNationalId('');
    setOtp('');
    setLoginStep(0);
    setPaymentAmount('');
    setReceiptFile(null);
    setReceiptPreview(null);
    setContactData({ phone: '', email: '' });

    if (sessionExpired) {
      setError('Your session has expired. Please log in again.');
    }

    addLog({
      user: currentUser,
      action: sessionExpired ? 'Session Expired' : 'Logout',
      entity: 'Debtor Portal',
      entityId: nationalId || 'N/A',
      entityName: 'Debtor',
      details: sessionExpired ? 'Session expired due to inactivity' : 'User logged out',
      category: 'portal',
      status: 'success'
    });
  };

  // PDPA Consent handler - records consent on every login
  const handlePdpaConsent = async () => {
    setPdpaConsenting(true);
    try {
      const response = await debtorApi.savePdpaConsent();
      if (response.success) {
        // Update session data - mark consent given for this session
        const storedSession = localStorage.getItem('debtorSession');
        if (storedSession) {
          const session = JSON.parse(storedSession);
          session.pdpaConsentGivenThisSession = true;
          localStorage.setItem('debtorSession', JSON.stringify(session));
        }
        setShowPdpaDialog(false);
        addLog({
          user: currentUser,
          action: 'PDPA Consent Given',
          entity: 'Debtor Portal',
          entityId: nationalId || 'N/A',
          entityName: 'Debtor',
          details: `Customer provided PDPA consent at ${new Date().toISOString()}`,
          category: 'portal',
          status: 'success'
        });
      }
    } catch (err) {
      showNotification(err.message || 'Failed to save consent. Please try again.', 'error');
    } finally {
      setPdpaConsenting(false);
    }
  };

  const [emailVerified, setEmailVerified] = useState(false);
  const [contactData, setContactData] = useState({
    phone: '',
    email: ''
  });

  // Mock debtor account data
  const mockDebtorAccount = {
    accountNumber: 'ACC-10001',
    debtorName: 'John Smith',
    phone: '+1-555-0123',
    email: 'john.smith@email.com',
    outstandingBalance: 12500.00,
    originalBalance: 15000.00,
    originalCreditor: 'ABC Bank',
    debtType: 'Credit Card',
    chargeOffDate: '2024-01-15',
    daysPastDue: 365,
    settlementOffer: {
      available: true,
      discountPercent: 30,
      settlementAmount: 8750.00,
      validUntil: '2025-02-15',
      terms: 'One-time payment or 3 monthly installments'
    },
    paymentHistory: [
      { date: '2024-12-15', amount: 1000.00, type: 'Payment', status: 'Completed' },
      { date: '2024-11-20', amount: 500.00, type: 'Payment', status: 'Completed' },
      { date: '2024-10-10', amount: 1000.00, type: 'Payment', status: 'Completed' }
    ],
    documents: [
      { name: 'Account Statement', date: '2025-01-01', type: 'PDF' },
      { name: 'Original Agreement', date: '2023-06-15', type: 'PDF' },
      { name: 'Collection Notice', date: '2024-01-20', type: 'PDF' }
    ],
    activePTP: {
      amount: 5000.00,
      date: '2025-01-25',
      status: 'Active'
    }
  };

  // Helper function to get first account data (for display purposes)
  const getFirstAccountData = () => {
    const acct = accounts.length > 0 ? accounts[0] : null;
    if (acct) {
      return {
        accountNumber: acct.account_number || 'N/A',
        debtorName: acct.name || 'N/A',
        phone: acct.phone || 'N/A',
        email: acct.email || 'N/A',
        outstandingBalance: acct.outstanding_balance || 0,
        originalBalance: acct.outstanding_balance || 0,
        originalCreditor: acct.original_creditor || 'N/A',
        debtType: acct.debt_type || 'N/A',
        loanContractDate: acct.loan_contract_date || 'N/A',
      };
    }
    return mockDebtorAccount;
  };

  // Get first account data for header display
  const firstAccountData = getFirstAccountData();

  // Handle opening payment dialog - shows consent dialog first
  const handleOpenPaymentDialog = (account = null) => {
    const targetAccount = account || (accounts.length > 0 ? accounts[0] : null);
    if (!targetAccount) return;

    setSelectedAccount(targetAccount);
    // Reset consent states
    setPaymentTermsConsent(false);
    setDigitalReceiptConsent(false);
    // Show consent dialog first
    setShowPaymentConsentDialog(true);
  };

  // Handle payment consent agreement - saves to DB and opens payment dialog
  const handlePaymentConsentAgree = async () => {
    if (!paymentTermsConsent || !digitalReceiptConsent) return;

    setPaymentConsentLoading(true);
    try {
      // Save consent to database
      await debtorApi.savePaymentConsent();

      // Close consent dialog
      setShowPaymentConsentDialog(false);

      // Open payment dialog
      setPaymentAmount('');
      setTransactionNumber('');
      setReceiptFile(null);
      setReceiptPreview(null);
      setPaymentDialog(true);
      // Fetch QR code from first account (same QR for all accounts)
      fetchAccountQrCode(selectedAccount.account_number);

      addLog({
        user: currentUser,
        action: 'Payment Consent Given',
        entity: 'Debtor Portal',
        entityId: nationalId || 'N/A',
        entityName: 'Debtor',
        details: 'Customer agreed to payment terms and digital receipt consent',
        category: 'portal',
        status: 'success'
      });
    } catch (err) {
      showNotification(err.message || 'Failed to save consent. Please try again.', 'error');
    } finally {
      setPaymentConsentLoading(false);
    }
  };

  // Close payment consent dialog
  const handleClosePaymentConsentDialog = () => {
    setShowPaymentConsentDialog(false);
    setPaymentTermsConsent(false);
    setDigitalReceiptConsent(false);
    setSelectedAccount(null);
  };

  // Handle receipt file selection
  const handleReceiptChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setReceiptFile(file);
      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => {
          setReceiptPreview(reader.result);
        };
        reader.readAsDataURL(file);
      } else {
        setReceiptPreview(null);
      }
    }
  };

  // Handle removing receipt
  const handleRemoveReceipt = () => {
    setReceiptFile(null);
    setReceiptPreview(null);
  };

  const handleLogin = async () => {
    setError('');
    setLoading(true);

    // Use loginValue if set, otherwise fall back to nationalId for backward compatibility
    const currentLoginValue = loginValue || nationalId;

    try {
      if (loginStep === 0) {
        // Step 1: Send OTP request using selected login method
        const response = await debtorApi.login(currentLoginValue, language, loginMethod);
        if (response.success) {
          setMaskedEmail(response.masked_email);
          // OTP no longer returned in response - sent via email
          setNationalId(response.national_id); // Store national_id from response for OTP verification
          setLoginStep(1);
          addLog({
            user: currentUser,
            action: 'OTP Requested',
            entity: 'Debtor Portal',
            entityId: currentLoginValue,
            entityName: 'Login',
            details: `OTP sent to ${response.masked_email} (${response.account_count} accounts found) via ${loginMethod}`,
            category: 'portal',
            status: 'success'
          });
        }
      } else {
        // Step 2: Verify OTP - now returns all accounts
        const response = await debtorApi.verifyOtp(nationalId, otp);
        if (response.success) {
          // Store token
          localStorage.setItem('debtorToken', response.token);

          // Store session data with login timestamp for persistence (multi-account)
          const sessionData = {
            accounts: response.accounts,
            totalBalance: response.total_balance,
            nationalId: nationalId,
            loginTime: Date.now(),
            pdpaConsent: response.pdpa_consent || false
          };
          localStorage.setItem('debtorSession', JSON.stringify(sessionData));

          // Set accounts data from response
          setAccounts(response.accounts);
          setTotalBalance(response.total_balance);

          // Set contact data from first account
          if (response.accounts.length > 0) {
            setContactData({
              phone: response.accounts[0].phone || '',
              email: response.accounts[0].email || ''
            });
          }

          setIsLoggedIn(true);

          // Always show PDPA consent dialog on every login
          setShowPdpaDialog(true);

          addLog({
            user: currentUser,
            action: 'Login Success',
            entity: 'Debtor Portal',
            entityId: nationalId,
            entityName: 'Debtor',
            details: `Successfully logged in with ${response.account_count} accounts`,
            category: 'portal',
            status: 'success'
          });
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
      addLog({
        user: currentUser,
        action: loginStep === 0 ? 'OTP Request Failed' : 'Login Failed',
        entity: 'Debtor Portal',
        entityId: nationalId,
        entityName: 'Login',
        details: err.message,
        category: 'portal',
        status: 'failure'
      });
    } finally {
      setLoading(false);
    }
  };

  // Smart QR code fetching: Customer-specific payment QR ONLY (uploaded QR codes)
  // Does NOT show LINE QR as payment method - LINE QR is for contact support only
  const fetchAccountQrCode = async (accountNumber = null) => {
    const currentAccountNumber = accountNumber || selectedAccount?.account_number;
    const currentNationalId = selectedAccount?.national_id;
    
    if (!currentAccountNumber) return;

    setQrCodeLoading(true);
    try {
      // Method 1: Try account-specific payment QR (generated or uploaded)
      if (currentNationalId) {
        try {
          const qrData = await qrApi.getQrByNationalId(currentNationalId);
          if (qrData.success && qrData.qr_code?.image && qrData.type !== 'global_with_account_info') {
            const imageUrl = `data:${qrData.qr_code.content_type || 'image/png'};base64,${qrData.qr_code.image}`;
            setAccountQrCode(imageUrl);
            console.log(`✅ Account-specific QR found for National ID: ${qrData.type}`);
            return;
          }
        } catch (error) {
          console.log('⚠️ National ID specific QR not found:', error.message);
        }
      }

      // Method 2: Try account number specific QR
      try {
        const qrData = await qrApi.getAccountQr(currentAccountNumber);
        if (qrData.success && qrData.qr_code?.image && qrData.type !== 'global_with_account_info') {
          const imageUrl = `data:${qrData.qr_code.content_type || 'image/png'};base64,${qrData.qr_code.image}`;
          setAccountQrCode(imageUrl);
          console.log(`✅ Account-specific QR found: ${qrData.type}`);
          return;
        }
      } catch (error) {
        console.log('⚠️ Account specific QR not found:', error.message);
      }

      // Method 3: Try legacy debtor image endpoint
      try {
        const imageData = await qrApi.getDebtorImage(currentAccountNumber);
        if (imageData.success && imageData.image && imageData.image.data) {
          const imageUrl = `data:${imageData.image.content_type || 'image/png'};base64,${imageData.image.data}`;
          setAccountQrCode(imageUrl);
          console.log('✅ Customer-specific QR from legacy endpoint found');
          return;
        }
      } catch (error) {
        console.log('⚠️ Legacy account image not found:', error.message);
      }

      // No customer-specific payment QR found - do NOT show LINE QR as payment method
      // LINE QR is for contact support only, not for payment
      setAccountQrCode(null);
      console.log('❌ No customer-specific payment QR code available - customer should use bank details or contact support');
      
    } catch (error) {
      console.error('❌ Error in QR code fetching process:', error);
      setAccountQrCode(null);
    } finally {
      setQrCodeLoading(false);
    }
  };

  // Handle proceeding to step 2 of payment flow
  const handleProceedToPayment = async () => {
    // Validate step 1 inputs
    if (paymentType === 'custom' && (!customAmount || parseFloat(customAmount) <= 0)) {
      showNotification(t('enterValidPaymentAmount') || 'Please enter a valid payment amount.', 'warning');
      return;
    }

    // Move to step 2 and fetch QR code
    setPaymentStep(2);
    await fetchAccountQrCode();
  };

  // Reset payment dialog state
  const resetPaymentDialog = () => {
    setPaymentDialog(false);
    setPaymentStep(1);
    setPaymentType('full');
    setCustomAmount('');
    setTransactionNumber('');
    setAccountQrCode(null);
    setPaymentAmount('');
    setReceiptFile(null);
    setReceiptPreview(null);
    setSelectedAccount(null);
    setPaymentTermsConsent(false);
    setDigitalReceiptConsent(false);
  };

  const handleMakePayment = async () => {
    if (!selectedAccount) return;
    const currentAccountNumber = selectedAccount.account_number;

    // Validate payment amount
    const amount = parseFloat(paymentAmount);
    if (!amount || amount <= 0) {
      showNotification(t('enterValidPaymentAmount') || 'Please enter a valid payment amount.', 'warning');
      return;
    }

    // Validate transaction number
    if (!transactionNumber.trim()) {
      showNotification(t('enterTransactionNumber') || 'Please enter the transaction number.', 'warning');
      return;
    }

    const paymentTypeLabel = amount >= selectedAccount.outstanding_balance ? 'Full Payment' : 'Partial Payment';

    setLoading(true);
    try {
      // Send payment notification with transaction number and optional receipt (pass language for email)
      const response = await debtorApi.sendPaymentInterest(
        currentAccountNumber,
        paymentTypeLabel,
        amount,
        transactionNumber,
        receiptFile, // Optional receipt file
        language // Pass current language for email
      );

      if (response.success) {
        addLog({
          user: currentUser,
          action: 'Payment Submitted',
          entity: 'Debtor Portal',
          entityId: currentAccountNumber,
          entityName: selectedAccount.name,
          details: `Payment: ${paymentTypeLabel} - ${formatCurrency(amount)} - Transaction: ${transactionNumber}`,
          category: 'payment',
          status: 'success'
        });

        resetPaymentDialog();
        setSuccessMessage({
          title: t('thankYouPayment'),
          details: [],
          footer: t('teamNotified')
        });
        setSuccessDialog(true);
      }
    } catch (err) {
      console.error('Failed to submit payment:', err);
      addLog({
        user: currentUser,
        action: 'Payment Submission Failed',
        entity: 'Debtor Portal',
        entityId: currentAccountNumber,
        entityName: selectedAccount.name,
        details: err.message,
        category: 'payment',
        status: 'failure'
      });
      showNotification(t('failedToProcessPayment') || `Failed to process payment: ${err.message}. Please try again or contact support.`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptSettlement = () => {
    console.log('Accepting settlement offer');
    setSettlementDialog(false);
    // Show success message
  };

  const handleNotReady = async () => {
    if (!selectedAccount) return;
    const currentAccountNumber = selectedAccount.account_number;

    // Validation logic: 
    // - Only "Others" (- -) requires a reason, all other options don't need reason
    const needsReason = instalmentPlan === 'Others';
    
    if (needsReason && !nonPaymentReason) {
      showNotification(t('selectNonPaymentReason') || 'Please select a reason for non-payment.', 'warning');
      return;
    }

    // Ensure an instalment plan is selected
    if (!instalmentPlan) {
      showNotification('Please select an instalment plan option.', 'warning');
      return;
    }

    setLoading(true);
    try {
      const response = await debtorApi.sendNotReadyToPay(
        currentAccountNumber,
        nonPaymentReason,
        nonPaymentNotes,
        language, // Pass current language for email
        preferredContactDate,
        preferredContactTime,
        preferredContactMethod,
        preferredContactValue,
        instalmentPlan
      );

      if (response.success) {
        addLog({
          user: currentUser,
          action: 'Need Support to Pay Submitted',
          entity: 'Debtor Portal',
          entityId: currentAccountNumber,
          entityName: firstAccountData?.debtorName,
          details: `Reason: ${nonPaymentReason}${instalmentPlan ? `, Instalment Plan: ${instalmentPlan}` : ''}, Contact: ${preferredContactMethod} (${preferredContactValue}), Date: ${preferredContactDate}, Time: ${preferredContactTime}`,
          category: 'payment',
          status: 'success'
        });

        setNotReadyDialog(false);
        setNonPaymentReason('');
        setInstalmentPlan('Others');
        setNonPaymentNotes('');
        setPreferredContactDate('');
        setPreferredContactTime('');
        setPreferredContactMethod('');
        setPreferredContactValue('');
        setSuccessMessage({
          title: t('thankYouNotReady'),
          details: [],
          footer: t('followUpMessage'),
          showLineQr: true
        });
        setSuccessDialog(true);
      }
    } catch (err) {
      console.error('Failed to submit non-payment reason:', err);
      addLog({
        user: currentUser,
        action: 'Not Ready to Pay Failed',
        entity: 'Debtor Portal',
        entityId: selectedAccount?.account_number || 'N/A',
        entityName: firstAccountData?.debtorName,
        details: err.message,
        category: 'payment',
        status: 'failure'
      });
      showNotification(t('failedToSubmitRequest') || `Failed to submit request: ${err.message}. Please try again or contact support.`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setLoading(true);
    try {
      // Use the stored loginValue or nationalId to resend OTP
      const currentLoginValue = loginValue || nationalId;
      const response = await debtorApi.login(currentLoginValue, language, loginMethod);

      if (response.success) {
        // OTP no longer returned in response - sent via email
        addLog({
          user: currentUser,
          action: 'OTP Resent',
          entity: 'Debtor Portal',
          entityId: nationalId,
          entityName: 'Login',
          details: `OTP resent to ${response.masked_email}`,
          category: 'portal',
          status: 'success'
        });
        showNotification(t('otpResent') || 'OTP has been resent to your registered email! Please check your inbox.', 'success', 3000);
      }
    } catch (err) {
      console.error('Failed to resend OTP:', err);
      showNotification(err.message || 'Failed to resend OTP. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateContact = () => {
    setNewPhone(contactData.phone);
    setNewEmail(contactData.email);
    setPhoneOTPSent(false);
    setEmailOTPSent(false);
    setPhoneVerified(false);
    setEmailVerified(false);
    setPhoneOTP('');
    setEmailOTP('');
    setUpdateContactDialog(true);
  };

  const handleSendPhoneOTP = () => {
    if (!newPhone || newPhone === contactData.phone) {
      showNotification(t('enterNewPhoneNumber') || 'Please enter a new phone number', 'warning');
      return;
    }
    // Send OTP to registered email for phone number verification
    const maskedCurrentEmail = contactData.email
      ? contactData.email.replace(/(.{2})(.*)(@.*)/, '$1***$3')
      : 'your registered email';
    showNotification(t('otpSentForPhone') || `OTP sent to ${maskedCurrentEmail} for phone number verification.`, 'info');
    setPhoneOTPSent(true);
    addLog({
      user: currentUser,
      action: 'Phone Update OTP Sent',
      entity: 'Contact Update',
      entityId: firstAccountData?.accountNumber,
      entityName: firstAccountData?.debtorName,
      details: `OTP sent to registered email for phone update`,
      category: 'security',
      status: 'success'
    });
  };

  const handleVerifyPhoneOTP = () => {
    // Simulate OTP verification (in production, verify with backend)
    if (phoneOTP === '') {
      setPhoneVerified(true);
      showNotification(t('phoneVerifiedSuccessfully') || 'Phone number verified successfully!', 'success');
      addLog({
        user: currentUser,
        action: 'Phone Verified',
        entity: 'Contact Update',
        entityId: firstAccountData?.accountNumber,
        entityName: firstAccountData?.debtorName,
        details: `Phone verified: ${newPhone}`,
        category: 'security',
        status: 'success'
      });
    } else {
      showNotification(t('invalidOTP') || 'Invalid OTP. Please try again.', 'error');
    }
  };

  const handleSendEmailOTP = () => {
    if (!newEmail || newEmail === contactData.email) {
      showNotification(t('enterNewEmailAddress') || 'Please enter a new email address', 'warning');
      return;
    }
    // Send OTP to registered (current) email for email change verification
    const maskedCurrentEmail = contactData.email
      ? contactData.email.replace(/(.{2})(.*)(@.*)/, '$1***$3')
      : 'your registered email';
    showNotification(t('otpSentForEmail') || `OTP sent to ${maskedCurrentEmail} for email change verification.`, 'info');
    setEmailOTPSent(true);
    addLog({
      user: currentUser,
      action: 'Email Update OTP Sent',
      entity: 'Contact Update',
      entityId: firstAccountData?.accountNumber,
      entityName: firstAccountData?.debtorName,
      details: `OTP sent to registered email for email update`,
      category: 'security',
      status: 'success'
    });
  };

  const handleVerifyEmailOTP = () => {
    // Simulate OTP verification (in production, verify with backend)
    if (emailOTP === '654321') {
      setEmailVerified(true);
      showNotification(t('emailVerifiedSuccessfully') || 'Email address verified successfully!', 'success');
      addLog({
        user: currentUser,
        action: 'Email Verified',
        entity: 'Contact Update',
        entityId: firstAccountData?.accountNumber,
        entityName: firstAccountData?.debtorName,
        details: `Email verified: ${newEmail}`,
        category: 'security',
        status: 'success'
      });
    } else {
      showNotification(t('invalidOTP') || 'Invalid OTP. Please try again.', 'error');
    }
  };

  const handleSaveContactInfo = async () => {
    if (!selectedAccount) return;
    const currentAccountNumber = selectedAccount.account_number;

    let changes = [];
    let updatedPhone = null;
    let updatedEmail = null;

    if (newPhone !== contactData.phone && phoneVerified) {
      updatedPhone = newPhone;
      changes.push(`Phone updated to ${newPhone}`);
    }

    if (newEmail !== contactData.email && emailVerified) {
      updatedEmail = newEmail;
      changes.push(`Email updated to ${newEmail}`);
    }

    if (changes.length === 0) {
      showNotification(t('noChangesToSave') || 'No changes to save or verification pending.', 'warning');
      return;
    }

    setLoading(true);
    try {
      // Call API to update contact information
      const response = await debtorApi.updateContact(
        currentAccountNumber,
        updatedPhone || contactData.phone,
        updatedEmail || contactData.email
      );

      if (response.success) {
        // Update local state
        setContactData({
          phone: response.debtor.phone || contactData.phone,
          email: response.debtor.email || contactData.email
        });

        // Update the selected account with new data
        setSelectedAccount(response.debtor);

        // Update accounts list with the updated account
        setAccounts(prevAccounts =>
          prevAccounts.map(acc =>
            acc.account_number === currentAccountNumber ? response.debtor : acc
          )
        );

        // Update session storage with new data
        const storedSession = localStorage.getItem('debtorSession');
        if (storedSession) {
          const session = JSON.parse(storedSession);
          session.accounts = session.accounts.map(acc =>
            acc.account_number === currentAccountNumber ? response.debtor : acc
          );
          localStorage.setItem('debtorSession', JSON.stringify(session));
        }

        addLog({
          user: currentUser,
          action: 'Contact Information Updated',
          entity: 'Debtor Account',
          entityId: currentAccountNumber,
          entityName: firstAccountData?.debtorName,
          details: changes.join(', '),
          category: 'account',
          status: 'success'
        });

        showNotification(t('contactInfoUpdated') || `Contact information updated successfully! ${changes.join(', ')}`, 'success');
        setUpdateContactDialog(false);
      }
    } catch (err) {
      showNotification(t('failedToUpdateContact') || `Failed to update contact information: ${err.message}`, 'error');
      addLog({
        user: currentUser,
        action: 'Contact Update Failed',
        entity: 'Debtor Account',
        entityId: currentAccountNumber,
        entityName: firstAccountData?.debtorName,
        details: err.message,
        category: 'account',
        status: 'failure'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRequestPaymentPlan = () => {
    showNotification(t('paymentPlanRedirect') || 'You will be redirected to the payment plan request form. Connecting to backend API...', 'info');
  };

  const handleContactSupport = () => {
    showNotification(t('contactSupportInfo') || 'Contact Support: Email: support@collections.com, Phone: 1800-XXX-XXXX, Live Chat (9 AM - 6 PM)', 'info');
  };

  const handleDownloadStatement = (doc) => {
    addLog({
      user: currentUser,
      action: 'Document Downloaded',
      entity: 'Debtor Portal',
      entityId: selectedAccount?.account_number || nationalId,
      entityName: doc || 'Account Statement',
      details: `Downloaded: ${doc || 'Account Statement'}`,
      category: 'portal',
      status: 'success'
    });
    showNotification(t('downloadingDocument') || `Downloading ${doc || 'document'}...`, 'info');
  };

  const handleViewResources = (resource) => {
    addLog({
      user: currentUser,
      action: 'Resource Viewed',
      entity: 'Debtor Portal',
      entityId: selectedAccount?.account_number || nationalId,
      entityName: resource,
      details: `Viewed educational resource: ${resource}`,
      category: 'portal',
      status: 'success'
    });
    showNotification(t('openingResource') || `Opening resource: ${resource}`, 'info');
  };

  const handleViewAllTips = () => {
    showNotification(t('viewAllTips') || 'Opening comprehensive financial wellness guide...', 'info');
  };

  const calculateInstallment = (amount, months) => {
    return (amount / parseInt(months)).toFixed(2);
  };

  // Check for maintenance mode - show before login
  if (systemSettings?.maintenance_mode?.enabled) {
    return (
      <MaintenancePage
        title={systemSettings.maintenance_mode.title}
        message={systemSettings.maintenance_mode.message}
        estimatedTime={systemSettings.maintenance_mode.estimated_time}
      />
    );
  }

  // Login Screen
  if (!isLoggedIn) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          p: 3
        }}
      >
        <Card sx={{ maxWidth: 480, width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
          <CardContent sx={{ p: 4 }}>
            {/* Header with Logo and Language Switcher */}
            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
              <Box
                component="img"
                src="/poweramclogo.avif"
                alt="PowerAMC Logo"
                sx={{ height: 80, width: 'auto', objectFit: 'contain' }}
              />
              <LanguageSwitcher variant="default" size="small" />
            </Box>

            <Box textAlign="center" mb={4}>
              <Avatar sx={{ width: 72, height: 72, bgcolor: 'primary.main', mx: 'auto', mb: 2 }}>
                <PaymentIcon sx={{ fontSize: 40 }} />
              </Avatar>
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                {t('debtorPortalTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('debtorPortalSubtitle')}
              </Typography>
            </Box>

            <Stepper activeStep={loginStep} sx={{ mb: 4 }}>
              <Step>
                <StepLabel>{t('enterYourDetails')}</StepLabel>
              </Step>
              <Step>
                <StepLabel>{t('verifyOtp')}</StepLabel>
              </Step>
            </Stepper>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {getTranslatedError(error)}
              </Alert>
            )}

            {loginStep === 0 ? (
              <Box>
                {/* Login Method Selector */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    {t('loginWith')}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {[
                      { value: 'national_id', label: t('nationalId') },
                      { value: 'email', label: t('email') },
                    ].map((method) => (
                      <Chip
                        key={method.value}
                        label={method.label}
                        onClick={() => {
                          setLoginMethod(method.value);
                          setLoginValue('');
                        }}
                        color={loginMethod === method.value ? 'primary' : 'default'}
                        variant={loginMethod === method.value ? 'filled' : 'outlined'}
                        sx={{ cursor: 'pointer' }}
                      />
                    ))}
                  </Box>
                </Box>

                <TextField
                  fullWidth
                  label={loginMethod === 'national_id' ? t('nationalId') : t('email')}
                  value={loginValue}
                  onChange={(e) => setLoginValue(e.target.value)}
                  placeholder={loginMethod === 'national_id' ? t('enterNationalId') : t('enterEmail')}
                  disabled={loading}
                  type={loginMethod === 'email' ? 'email' : 'text'}
                  sx={{ mb: 2 }}
                />
                <Alert severity="info" sx={{ mb: 3 }}>
                  {t('loginMethodInfo')}
                </Alert>

                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, mb: showLoginSupport ? 0 : 3 }}>
                  <Typography
                    variant="body2"
                    color="primary"
                    sx={{ cursor: 'pointer', textDecoration: 'underline', '&:hover': { color: 'primary.dark' } }}
                    onClick={() => setShowLoginSupport(!showLoginSupport)}
                  >
                    {t('issuesLoggingIn')}
                  </Typography>
                </Box>

                {/* Login Support Section with LINE QR */}
                {showLoginSupport && (
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      mt: 2,
                      mb: 3,
                      backgroundColor: 'grey.50',
                      borderRadius: 2
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom color="primary">
                      {t('needHelp')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {t('loginSupportMessage')}
                    </Typography>
                    {lineQrCode ? (
                      <Box textAlign="center">
                        <Box
                          component="img"
                          src={`data:image/png;base64,${lineQrCode}`}
                          alt="LINE Support QR Code"
                          sx={{
                            width: 150,
                            height: 150,
                            borderRadius: 1,
                            border: '1px solid',
                            borderColor: 'grey.300',
                            mb: 1
                          }}
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          {t('scanToContactSupport')}
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" textAlign="center">
                        {t('supportQrNotAvailable')}
                      </Typography>
                    )}
                  </Paper>
                )}
              </Box>
            ) : (
              <Box>
                <TextField
                  fullWidth
                  label={t('enterOtp')}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder={t('sixDigitOtp')}
                  type={showOTP ? 'text' : 'password'}
                  disabled={loading}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowOTP(!showOTP)}
                          edge="end"
                        >
                          {showOTP ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                  sx={{ mb: 2 }}
                />
                <Alert severity="info" sx={{ mb: 2 }}>
                  {t('otpSentTo')} {maskedEmail || 'your registered email'}. {t('validFor')} 5 {t('minutes')}.
                </Alert>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Button size="small" onClick={handleResendOTP} disabled={loading}>
                    {t('resendOtp')}
                  </Button>
                  <Typography
                    variant="body2"
                    color="primary"
                    sx={{ cursor: 'pointer', textDecoration: 'underline', '&:hover': { color: 'primary.dark' } }}
                    onClick={() => setShowLoginSupport(!showLoginSupport)}
                  >
                    {t('issuesLoggingIn')}
                  </Typography>
                </Box>

                {/* Login Support Section with LINE QR */}
                {showLoginSupport && (
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      mb: 2,
                      backgroundColor: 'grey.50',
                      borderRadius: 2
                    }}
                  >
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom color="primary">
                      {t('needHelp')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {t('loginSupportMessage')}
                    </Typography>
                    {lineQrCode ? (
                      <Box textAlign="center">
                        <Box
                          component="img"
                          src={`data:image/png;base64,${lineQrCode}`}
                          alt="LINE Support QR Code"
                          sx={{
                            width: 150,
                            height: 150,
                            borderRadius: 1,
                            border: '1px solid',
                            borderColor: 'grey.300',
                            mb: 1
                          }}
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          {t('scanToContactSupport')}
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary" textAlign="center">
                        {t('supportQrNotAvailable')}
                      </Typography>
                    )}
                  </Paper>
                )}
              </Box>
            )}

            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleLogin}
              disabled={loading || (loginStep === 0 ? !loginValue : !otp)}
            >
              {loading ? t('pleaseWait') : (loginStep === 0 ? t('sendOtp') : t('verifyAndLogin'))}
            </Button>
            {loading && <LinearProgress sx={{ mt: 1 }} />}

            <Box mt={3} textAlign="center">
              <Button
                variant="text"
                size="small"
                color="primary"
                onClick={() => window.open('/admin', '_blank')}
              >
                {t('adminPortalTitle')}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Snackbar Notification for Login Screen */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={snackbar.duration}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }} variant="filled">
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    );
  }

  // Main Portal Interface
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
          color: 'white',
          borderRadius: 0
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" maxWidth="lg" mx="auto">
          <Box>
            <Typography variant="h5" fontWeight="bold">
              {t('welcome')}, {language === 'th' ? 'คุณ' : ''}{firstAccountData.debtorName}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={2}>
            <LanguageSwitcher variant="outlined-white" size="small" />
            <Button
              variant="outlined"
              onClick={() => handleLogout(false)}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' }
              }}
            >
              {t('logout')}
            </Button>
          </Box>
        </Box>
      </Paper>

      <Box sx={{ maxWidth: 'lg', mx: 'auto', px: 3, pb: 4 }}>

      {/* Main Content - Details View */}
      <>

      {/* Total Outstanding Balance Card */}
      <Card
        sx={{
          mb: 3,
          background: 'linear-gradient(135deg, #d32f2f 0%, #c62828 100%)',
          color: 'white',
          boxShadow: '0 8px 32px rgba(211, 47, 47, 0.3)'
        }}
      >
        <CardContent sx={{ p: { xs: 3, md: 4 } }}>
          {/* Motivational Tagline - Top Center */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              mb: { xs: 2, md: 3 }
            }}
          >
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 1,
                bgcolor: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(4px)',
                px: { xs: 2.5, md: 3 },
                py: { xs: 0.75, md: 1 },
                borderRadius: 3,
                border: '1px solid rgba(255,255,255,0.3)'
              }}
            >
              <Typography
                sx={{
                  fontWeight: 600,
                  letterSpacing: { xs: 1, md: 1.5 },
                  fontSize: { xs: '0.75rem', sm: '0.95rem', md: '1.1rem' },
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap'
                }}
              >
                ✨ {t('paymentTagline')} ✨
              </Typography>
            </Box>
          </Box>

          <Grid container spacing={4} alignItems="center">
            <Grid size={{ xs: 12, md: 7 }}>
              <Typography variant="overline" sx={{ opacity: 0.9, letterSpacing: 2 }}>
                {t('totalOutstandingBalance')}
              </Typography>
              <Typography variant="h2" fontWeight="bold" sx={{ my: 1, fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' } }}>
                {formatCurrency(totalBalance)}
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 5 }}>
              <Box display="flex" flexDirection="column" gap={2}>
                {(systemSettings?.debtor_features?.not_ready_to_pay !== false) && (
                  <Button
                    variant="outlined"
                    size="large"
                    fullWidth
                    sx={{
                      borderColor: 'rgba(255,255,255,0.5)',
                      color: 'white',
                      py: 1.5,
                      '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' }
                    }}
                    startIcon={<SupportIcon />}
                    onClick={() => {
                      // Set the first account as selected for the not ready dialog
                      if (accounts.length > 0) {
                        setSelectedAccount(accounts[0]);
                      }
                      setNotReadyDialog(true);
                    }}
                  >
                    {t('notReadyToPay')}
                  </Button>
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>


      {/* Active PTP Alert */}
      {firstAccountData?.activePTP && (
        <Alert severity="info" sx={{ mb: 3 }} icon={<ScheduleIcon />}>
          <Typography variant="body2">
            <strong>{t('activePaymentPromise')}:</strong> {formatCurrency(firstAccountData?.activePTP?.amount)}
            {t('dueOn')} {firstAccountData?.activePTP?.date}
          </Typography>
        </Alert>
      )}

      {/* Accounts Section - Shows all linked accounts */}
      <Card sx={{ mb: 3, borderRadius: 3, boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}>
        <CardContent sx={{ p: 3 }}>
          <Box display="flex" alignItems="center" mb={3}>
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2, width: 44, height: 44 }}>
              <BudgetIcon sx={{ fontSize: 24 }} />
            </Avatar>
            <Box>
              <Typography variant="h6" fontWeight="bold">
                {t('yourAccounts')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('accountsLinkedPrefix')} {accounts.length} {t('accountsLinkedSuffix')}
              </Typography>
            </Box>
          </Box>

          {/* Accounts Table/List */}
          <Paper variant="outlined" sx={{ borderRadius: 2, overflow: 'hidden' }}>
            {accounts.map((account, index) => (
              <Box
                key={account.account_number}
                sx={{
                  p: { xs: 2, sm: 2.5 },
                  borderBottom: index < accounts.length - 1 ? '1px solid' : 'none',
                  borderColor: 'divider',
                  '&:hover': { bgcolor: 'grey.50' },
                  transition: 'background-color 0.2s'
                }}
              >
                {/* Mobile Layout */}
                <Box sx={{ display: { xs: 'block', md: 'none' } }}>
                  {/* Account Header with Number Badge */}
                  <Box display="flex" alignItems="center" gap={1.5} mb={2}>
                    <Avatar
                      sx={{
                        bgcolor: 'primary.main',
                        width: 36,
                        height: 36,
                        fontSize: '0.85rem',
                        fontWeight: 'bold'
                      }}
                    >
                      {index + 1}
                    </Avatar>
                    <Box flex={1} sx={{ minWidth: 0, overflow: 'hidden' }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', display: 'block' }}>
                        {t('accountNumber')}
                      </Typography>
                      <Typography
                        variant="body1"
                        fontWeight="bold"
                        color="primary.main"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {account.account_number}
                      </Typography>
                    </Box>
                    <Chip
                      label={account.debt_type || t('notProvided')}
                      size="small"
                      variant="outlined"
                      sx={{
                        maxWidth: '100px',
                        flexShrink: 0,
                        '& .MuiChip-label': {
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }
                      }}
                    />
                  </Box>

                  {/* Account Details Grid - 2 columns */}
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: 1.5,
                      mb: 2,
                      p: 1.5,
                      bgcolor: 'grey.50',
                      borderRadius: 1.5
                    }}
                  >
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', display: 'block', mb: 0.25 }}>
                        {t('creditor')}
                      </Typography>
                      <Typography variant="body2" fontWeight="500" sx={{ wordBreak: 'break-word' }}>
                        {account.original_creditor || t('notProvided')}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', display: 'block', mb: 0.25 }}>
                        {t('loanContractDate')}
                      </Typography>
                      <Typography variant="body2" fontWeight="500">
                        {formatDateOnly(account.loan_contract_date) || t('notProvided')}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Balance and Pay Button Row */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 1.5,
                      bgcolor: 'error.50',
                      borderRadius: 1.5
                    }}
                  >
                    <Box>
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem', display: 'block', mb: 0.25 }}>
                        {t('outstandingBalance')}
                      </Typography>
                      <Typography variant="h6" fontWeight="bold" color="error.main">
                        {formatCurrency(account.outstanding_balance || 0)}
                      </Typography>
                    </Box>
                    {(systemSettings?.debtor_features?.make_payment !== false) && (
                      <Button
                        variant="contained"
                        size="medium"
                        color="error"
                        startIcon={<PaymentIcon />}
                        onClick={() => handleOpenPaymentDialog(account)}
                        sx={{
                          textTransform: 'none',
                          fontWeight: 'bold',
                          whiteSpace: 'nowrap',
                          px: 2,
                          py: 1
                        }}
                      >
                        {t('pay')}
                      </Button>
                    )}
                  </Box>
                </Box>

                {/* Desktop Layout */}
                <Grid container spacing={2} alignItems="center" sx={{ display: { xs: 'none', md: 'flex' } }}>
                  {/* Account Number & Badge */}
                  <Grid size={{ md: 3 }}>
                    <Box display="flex" alignItems="center" gap={1.5}>
                      <Avatar
                        sx={{
                          bgcolor: 'primary.main',
                          width: 40,
                          height: 40,
                          fontSize: '0.9rem',
                          fontWeight: 'bold'
                        }}
                      >
                        {index + 1}
                      </Avatar>
                      <Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                          {t('accountNumber')}
                        </Typography>
                        <Typography variant="body1" fontWeight="bold" color="primary.main">
                          {account.account_number}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>

                  {/* Creditor */}
                  <Grid size={{ md: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {t('creditor')}
                    </Typography>
                    <Typography variant="body2" fontWeight="500">
                      {account.original_creditor || t('notProvided')}
                    </Typography>
                  </Grid>

                  {/* Debt Type */}
                  <Grid size={{ md: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {t('type')}
                    </Typography>
                    <Box sx={{ mt: 0.5 }}>
                      <Chip label={account.debt_type || t('notProvided')} size="small" variant="outlined" />
                    </Box>
                  </Grid>

                  {/* Loan Contract Date */}
                  <Grid size={{ md: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                      {t('loanContractDate')}
                    </Typography>
                    <Typography variant="body2" fontWeight="500">
                      {formatDateOnly(account.loan_contract_date) || t('notProvided')}
                    </Typography>
                  </Grid>

                  {/* Balance & Payment Button */}
                  <Grid size={{ md: 3 }}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        gap: 2
                      }}
                    >
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                          {t('outstandingBalance')}
                        </Typography>
                        <Typography variant="h6" fontWeight="bold" color="error.main">
                          {formatCurrency(account.outstanding_balance || 0)}
                        </Typography>
                      </Box>

                      {/* Make Payment Button */}
                      {(systemSettings?.debtor_features?.make_payment !== false) && (
                        <Button
                          variant="contained"
                          size="small"
                          color="error"
                          startIcon={<PaymentIcon />}
                          onClick={() => handleOpenPaymentDialog(account)}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 'bold',
                            whiteSpace: 'nowrap',
                            minWidth: 'fit-content',
                            px: 1.5,
                            py: 0.75
                          }}
                        >
                          {t('pay')}
                        </Button>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            ))}
          </Paper>
        </CardContent>
      </Card>

      {/* Contact & LINE Support Section - Side by Side */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Contact Information Card */}
        <Grid size={{ xs: 12, md: (systemSettings?.debtor_features?.line_qr_support !== false) ? 6 : 12 }}>
          <Card
            sx={{
              height: '100%',
              background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
              color: 'white',
              borderRadius: 3,
              boxShadow: '0 10px 40px rgba(17, 153, 142, 0.3)'
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Box display="flex" alignItems="center">
                  <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2, width: 44, height: 44 }}>
                    <SendIcon sx={{ fontSize: 24 }} />
                  </Avatar>
                  <Typography variant="h6" fontWeight="bold">
                    {t('contactInformation')}
                  </Typography>
                </Box>
                {(systemSettings?.debtor_features?.update_contact !== false) && (
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleUpdateContact}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      fontSize: '0.75rem',
                      px: 2,
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
                    }}
                  >
                    {t('update')}
                  </Button>
                )}
              </Box>

              {/* Name - Prominent Display */}
              <Box sx={{
                p: 2,
                bgcolor: 'rgba(255,255,255,0.15)',
                borderRadius: 2,
                mb: 2,
                textAlign: 'center',
                border: '1px solid rgba(255,255,255,0.2)'
              }}>
                <Typography variant="caption" sx={{ opacity: 0.9, textTransform: 'uppercase', letterSpacing: 1.5, fontSize: '0.7rem' }}>
                  {t('fullName')}
                </Typography>
                <Typography variant="h5" fontWeight="bold" sx={{ mt: 0.5 }}>
                  {language === 'th' ? 'คุณ' : ''}{firstAccountData?.debtorName}
                </Typography>
              </Box>

              {/* Contact Details */}
              <Grid container spacing={1.5}>
                <Grid size={12}>
                  <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 1.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 36, height: 36 }}>
                      <ScheduleIcon sx={{ fontSize: 20 }} />
                    </Avatar>
                    <Box>
                      <Typography variant="caption" sx={{ opacity: 0.8, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: '0.65rem' }}>
                        {t('phoneNumber')}
                      </Typography>
                      <Typography variant="body1" fontWeight="600">
                        {firstAccountData?.phone || t('notProvided')}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid size={12}>
                  <Box sx={{ p: 1.5, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 1.5, display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 36, height: 36 }}>
                      <DocumentIcon sx={{ fontSize: 20 }} />
                    </Avatar>
                    <Box sx={{ minWidth: 0, flex: 1 }}>
                      <Typography variant="caption" sx={{ opacity: 0.8, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: '0.65rem' }}>
                        {t('emailAddress')}
                      </Typography>
                      <Typography variant="body1" fontWeight="600" sx={{ wordBreak: 'break-word' }}>
                        {firstAccountData?.email || t('notProvided')}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* LINE Support QR Code Card - Side by Side with Contact */}
        {(systemSettings?.debtor_features?.line_qr_support !== false) && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card
              sx={{
                height: '100%',
                borderRadius: 3,
                background: 'linear-gradient(135deg, #00B900 0%, #00C300 100%)',
                color: 'white',
                boxShadow: '0 10px 40px rgba(0, 185, 0, 0.3)'
              }}
            >
              <CardContent sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box display="flex" alignItems="center" gap={1.5} mb={2}>
                  <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 44, height: 44 }}>
                    <SendIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {t('needHelpContactLine')}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      {t('scanQrCode')}
                    </Typography>
                  </Box>
                </Box>

                {lineQrCode ? (
                  <Box
                    sx={{
                      flex: 1,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      p: 2,
                      bgcolor: 'white',
                      borderRadius: 2,
                    }}
                  >
                    <img
                      src={`data:image/png;base64,${lineQrCode}`}
                      alt="LINE Support QR Code"
                      style={{
                        maxWidth: '160px',
                        maxHeight: '160px',
                        borderRadius: '8px',
                      }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5, textAlign: 'center' }}>
                      {t('openLineAndScan')}
                    </Typography>
              </Box>
            ) : (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  p: 3,
                  bgcolor: 'rgba(255,255,255,0.1)',
                  borderRadius: 2,
                  border: '2px dashed rgba(255,255,255,0.3)'
                }}
              >
                <Typography variant="body1" sx={{ opacity: 0.8 }}>
                  {t('qrCodeNotAvailable')}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.7, mt: 1 }}>
                  {t('contactSupportAt')} support@collections.com
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
        )}
      </Grid>
      </>

      {/* Payment Consent Dialog - Shows before payment dialog */}
      <Dialog
        open={showPaymentConsentDialog}
        onClose={handleClosePaymentConsentDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: 'primary.main', color: 'white' }}>
          <Typography variant="h6" fontWeight="bold">
            {t('termsAndConsent')}
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              {t('pleaseReadAndAgree')}
            </Typography>
          </Alert>

          {/* Payment Terms Consent */}
          <Paper variant="outlined" sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
            <Box display="flex" alignItems="flex-start">
              <Checkbox
                checked={paymentTermsConsent}
                onChange={(e) => setPaymentTermsConsent(e.target.checked)}
                sx={{ mt: -0.5, mr: 1 }}
              />
              <Box>
                <Typography variant="subtitle2" fontWeight="bold" color="primary.main" gutterBottom>
                  {t('paymentTermsTitle')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                  {t('paymentTermsText')}
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Digital Receipt Consent */}
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Box display="flex" alignItems="flex-start">
              <Checkbox
                checked={digitalReceiptConsent}
                onChange={(e) => setDigitalReceiptConsent(e.target.checked)}
                sx={{ mt: -0.5, mr: 1 }}
              />
              <Box>
                <Typography variant="subtitle2" fontWeight="bold" color="primary.main" gutterBottom>
                  {t('digitalReceiptTitle')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                  {t('digitalReceiptText')}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2 }}>
          <Button onClick={handleClosePaymentConsentDialog} disabled={paymentConsentLoading}>
            {t('cancel')}
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handlePaymentConsentAgree}
            disabled={!paymentTermsConsent || !digitalReceiptConsent || paymentConsentLoading}
          >
            {paymentConsentLoading ? t('loading') : t('agreeAndContinue')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Payment Dialog - Simplified (QR + Bank Details + Receipt Upload) */}
      <Dialog open={paymentDialog} onClose={resetPaymentDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {t('makePayment')}
        </DialogTitle>
        <DialogContent>
          {/* Account Balance Summary */}
          <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'grey.50', overflow: 'hidden' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography variant="caption" color="text.secondary">{t('outstandingBalance')}</Typography>
                <Typography variant="h5" fontWeight="bold" color="error.main">
                  {formatCurrency(selectedAccount?.outstanding_balance || 0)}
                </Typography>
              </Box>
              <Chip
                label={selectedAccount?.account_number || ''}
                size="small"
                color="primary"
                variant="outlined"
                sx={{
                  maxWidth: { xs: '140px', sm: '200px' },
                  flexShrink: 0,
                  '& .MuiChip-label': {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }
                }}
              />
            </Box>
          </Paper>

          {/* Two Column Layout: QR Code + Bank Details */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {/* Left: QR Code */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%', textAlign: 'center' }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  {t('scanQrCodeToPay')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('useYourBankingApp')}
                </Typography>

                {qrCodeLoading ? (
                  <Box sx={{ py: 4 }}>
                    <LinearProgress sx={{ mb: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      {t('loadingQrCode')}
                    </Typography>
                  </Box>
                ) : accountQrCode ? (
                  <Box
                    sx={{
                      display: 'inline-block',
                      p: 2,
                      bgcolor: 'white',
                      borderRadius: 2,
                      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                      border: '1px solid #eee'
                    }}
                  >
                    <img
                      src={accountQrCode}
                      alt="Payment QR Code"
                      style={{
                        maxWidth: '180px',
                        maxHeight: '180px',
                        display: 'block'
                      }}
                    />
                  </Box>
                ) : (
                  <Alert severity="info" sx={{ textAlign: 'left' }}>
                    {t('qrCodeNotAvailableUseBank')}
                  </Alert>
                )}
              </Paper>
            </Grid>

            {/* Right: Bank Account Details */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%', bgcolor: 'primary.50' }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  {t('bankTransferDetails')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('orTransferDirectly')}
                </Typography>

                {bankDetails && (bankDetails.bank_name || bankDetails.account_number || bankDetails.promptpay_id) ? (
                  <Box sx={{ '& > div': { mb: 1.5 } }}>
                    {bankDetails.bank_name && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">{t('bankName')}</Typography>
                        <Typography variant="body1" fontWeight="600">{bankDetails.bank_name}</Typography>
                      </Box>
                    )}
                    {bankDetails.account_name && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">{t('accountName')}</Typography>
                        <Typography variant="body1" fontWeight="600">{bankDetails.account_name}</Typography>
                      </Box>
                    )}
                    {bankDetails.account_number && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">{t('accountNumber')}</Typography>
                        <Typography variant="body1" fontWeight="600">{bankDetails.account_number}</Typography>
                      </Box>
                    )}
                    {bankDetails.promptpay_id && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">{t('promptPayId')}</Typography>
                        <Typography variant="body1" fontWeight="600">{bankDetails.promptpay_id}</Typography>
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Alert severity="info" sx={{ textAlign: 'left' }}>
                    {t('bankDetailsNotConfigured')} {t('pleaseContactSupport')}
                  </Alert>
                )}
              </Paper>
            </Grid>
          </Grid>

          {/* Transaction Details Section */}
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            {t('enterTransactionDetails')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('afterCompletingPayment')}
          </Typography>

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label={t('paymentAmountLabel')}
                type="number"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                InputProps={{ startAdornment: <Typography sx={{ mr: 1 }}>฿</Typography> }}
                required
                helperText={t('enterPaymentAmount')}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField
                fullWidth
                label={t('transactionNumberLabel')}
                value={transactionNumber}
                onChange={(e) => setTransactionNumber(e.target.value)}
                placeholder={t('enterTransactionNumber')}
                required
                helperText={t('fromYourPaymentConfirmation')}
              />
            </Grid>
          </Grid>

          {/* Receipt Upload Section */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              {t('uploadPaymentReceipt')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('uploadReceiptDescription')}
            </Typography>

            {!receiptFile ? (
              <Button
                variant="outlined"
                component="label"
                startIcon={<AttachFileIcon />}
                fullWidth
                sx={{ py: 2, borderStyle: 'dashed' }}
              >
                {t('selectReceiptImageOrPdf')}
                <input
                  type="file"
                  hidden
                  accept="image/*,.pdf"
                  onChange={handleReceiptChange}
                />
              </Button>
            ) : (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box display="flex" alignItems="center" gap={2}>
                    {receiptPreview ? (
                      <img
                        src={receiptPreview}
                        alt="Receipt preview"
                        style={{ width: 60, height: 60, objectFit: 'cover', borderRadius: 4 }}
                      />
                    ) : (
                      <Avatar sx={{ bgcolor: 'primary.light', width: 60, height: 60 }}>
                        <AttachFileIcon />
                      </Avatar>
                    )}
                    <Box>
                      <Typography variant="body2" fontWeight="500">
                        {receiptFile.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(receiptFile.size / 1024).toFixed(1)} KB
                      </Typography>
                    </Box>
                  </Box>
                  <Button color="error" size="small" onClick={handleRemoveReceipt}>
                    {t('remove')}
                  </Button>
                </Box>
              </Paper>
            )}
          </Box>

        </DialogContent>
        <DialogActions>
          <Button onClick={resetPaymentDialog}>{t('cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleMakePayment}
            disabled={loading || !paymentAmount || !transactionNumber || !receiptFile}
          >
            {loading ? t('submitting') : t('submitPayment')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settlement Dialog */}
      <Dialog open={settlementDialog} onClose={() => setSettlementDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('settlementDialogTitle')}</DialogTitle>
        <DialogContent>
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight="bold">
              {t('limitedTimeOffer')}
            </Typography>
            <Typography variant="body2">
              {t('settlementValidUntil')} {firstAccountData?.settlementOffer?.validUntil}
            </Typography>
          </Alert>

          <Grid container spacing={2}>
            <Grid size={6}>
              <Typography variant="body2" color="text.secondary">{t('currentBalance')}</Typography>
              <Typography variant="h6" color="error.main">
                {formatCurrency(firstAccountData?.outstandingBalance)}
              </Typography>
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" color="text.secondary">{t('settlementAmount')}</Typography>
              <Typography variant="h6" color="success.main">
                {formatCurrency(firstAccountData?.settlementOffer?.settlementAmount)}
              </Typography>
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" color="text.secondary">{t('discount')}</Typography>
              <Typography variant="h6" color="primary.main">
                {firstAccountData?.settlementOffer?.discountPercent}%
              </Typography>
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" color="text.secondary">{t('youSave')}</Typography>
              <Typography variant="h6" color="success.main">
                {formatCurrency((firstAccountData?.outstandingBalance || 0) - (firstAccountData?.settlementOffer?.settlementAmount || 0))}
              </Typography>
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Typography variant="subtitle2" gutterBottom>
            {t('paymentOptions')}
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {firstAccountData?.settlementOffer?.terms}
          </Typography>

          <Alert severity="info">
            <Typography variant="body2">
              {t('settlementAgreement')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettlementDialog(false)}>{t('maybeLater')}</Button>
          <Button variant="contained" onClick={handleAcceptSettlement}>
            {t('acceptAndPayNow')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Not Ready to Pay Dialog */}
      <Dialog open={notReadyDialog} onClose={() => setNotReadyDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('notReadyDialogTitle')}</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            {t('notReadyInfo')}
          </Alert>

          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel id="instalment-plan-label">{t('needInstalmentPlan')}</InputLabel>
            <Select
              labelId="instalment-plan-label"
              id="instalment-plan"
              value={instalmentPlan}
              label={t('needInstalmentPlan')}
              onChange={(e) => {
                setInstalmentPlan(e.target.value);
                // When selecting non-Others option, auto-set reason to 'Other' so backend gets a value
                // When selecting Others (- -), clear the reason so user must select one
                if (e.target.value !== 'Others') {
                  setNonPaymentReason('Other');
                } else {
                  setNonPaymentReason('');
                }
              }}
            >
              <MenuItem value="Others">- -</MenuItem>
              <MenuItem value="2 months">{t('months2')}</MenuItem>
              <MenuItem value="4 months">{t('months4')}</MenuItem>
              <MenuItem value="6 months">{t('months6')}</MenuItem>
              <MenuItem value="8 months">{t('months8')}</MenuItem>
              <MenuItem value="10 months">{t('months10')}</MenuItem>
              <MenuItem value="12 months">{t('months12')}</MenuItem>
              <MenuItem value="Other Plans">{t('others')}</MenuItem>
            </Select>
          </FormControl>

          {/* Show "Unable to Pay Now" field only when "Others" (- -) is selected */}
          {instalmentPlan === 'Others' && (
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel id="non-payment-reason-label">{t('reasonForNonPayment')}</InputLabel>
              <Select
                labelId="non-payment-reason-label"
                id="non-payment-reason"
                value={nonPaymentReason}
                label={t('reasonForNonPayment')}
                onChange={(e) => setNonPaymentReason(e.target.value)}
              >
                <MenuItem value="Medical Emergency">{t('medicalEmergency')}</MenuItem>
                <MenuItem value="Job Loss">{t('jobLoss')}</MenuItem>
                <MenuItem value="Reduced Income">{t('reducedIncome')}</MenuItem>
                <MenuItem value="Divorce Settlement">{t('divorceSettlement')}</MenuItem>
                <MenuItem value="Natural Disaster">{t('naturalDisaster')}</MenuItem>
                <MenuItem value="Family Emergency">{t('familyEmergency')}</MenuItem>
                <MenuItem value="Business Closure">{t('businessClosure')}</MenuItem>
                <MenuItem value="Others">{t('others')}</MenuItem>
              </Select>
            </FormControl>
          )}

          <TextField
            fullWidth
            label={t('additionalNotes')}
            multiline
            rows={3}
            value={nonPaymentNotes}
            onChange={(e) => setNonPaymentNotes(e.target.value)}
            placeholder={t('additionalNotesPlaceholder')}
            sx={{ mb: 3 }}
          />

          {/* Contact Preferences Section */}
          <Typography variant="subtitle2" fontWeight="bold" color="primary" sx={{ mb: 2 }}>
            {t('contactPreferences')}
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label={t('preferredDate')}
                type="date"
                value={preferredContactDate}
                onChange={(e) => setPreferredContactDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
                inputProps={{ min: new Date().toISOString().split('T')[0] }}
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel id="preferred-time-label">{t('preferredTime')}</InputLabel>
                <Select
                  labelId="preferred-time-label"
                  value={preferredContactTime}
                  label={t('preferredTime')}
                  onChange={(e) => setPreferredContactTime(e.target.value)}
                >
                  <MenuItem value="morning">{t('timeMorning')}</MenuItem>
                  <MenuItem value="afternoon">{t('timeAfternoon')}</MenuItem>
                  <MenuItem value="evening">{t('timeEvening')}</MenuItem>
                  <MenuItem value="anytime">{t('timeAnytime')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel id="contact-method-label">{t('preferredContactMethod')}</InputLabel>
                <Select
                  labelId="contact-method-label"
                  value={preferredContactMethod}
                  label={t('preferredContactMethod')}
                  onChange={(e) => {
                    const method = e.target.value;
                    setPreferredContactMethod(method);
                    // Don't auto-fill - let user enter manually
                    setPreferredContactValue('');
                  }}
                >
                  <MenuItem value="phone">{t('contactByPhone')}</MenuItem>
                  <MenuItem value="email">{t('contactByEmail')}</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label={preferredContactMethod === 'phone' ? t('phoneNumber') : preferredContactMethod === 'email' ? t('emailAddress') : t('contactInfo')}
                value={preferredContactValue}
                onChange={(e) => setPreferredContactValue(e.target.value)}
                placeholder={preferredContactMethod === 'phone' ? '+66-XX-XXX-XXXX' : preferredContactMethod === 'email' ? 'example@email.com' : t('selectContactMethod')}
                type={preferredContactMethod === 'email' ? 'email' : 'tel'}
                disabled={!preferredContactMethod}
                helperText={!preferredContactMethod ? t('selectContactMethodFirst') : ''}
              />
            </Grid>
          </Grid>

          <Alert severity="warning">
            <Typography variant="body2">
              {t('interestWarning')}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setNotReadyDialog(false);
            setNonPaymentReason('');
            setInstalmentPlan('');
            setNonPaymentNotes('');
            setPreferredContactDate('');
            setPreferredContactTime('');
            setPreferredContactMethod('');
            setPreferredContactValue('');
          }}>{t('cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleNotReady}
            disabled={
              loading || 
              !instalmentPlan || 
              (instalmentPlan === 'Others' && !nonPaymentReason) ||
              !preferredContactDate ||
              !preferredContactTime ||
              !preferredContactMethod ||
              !preferredContactValue
            }
          >
            {loading ? t('submitting') : t('submitRequest')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Update Contact Information Dialog */}
      <Dialog open={updateContactDialog} onClose={() => setUpdateContactDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h6" fontWeight="bold">{t('updateContactTitle')}</Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              {t('updateContactInfo')}
            </Typography>
          </Alert>

          {/* Phone Number Section */}
          <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Chip label={t('phoneNumber')} color="primary" size="small" />
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('currentPhone')}: <strong>{contactData.phone}</strong>
            </Typography>

            <TextField
              fullWidth
              label={t('newPhoneNumber')}
              value={newPhone}
              onChange={(e) => {
                setNewPhone(e.target.value);
                setPhoneOTPSent(false);
                setPhoneVerified(false);
              }}
              placeholder="+1-555-0000"
              disabled={phoneVerified}
              size="medium"
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: phoneVerified && (
                  <InputAdornment position="end">
                    <CheckIcon color="success" />
                  </InputAdornment>
                )
              }}
            />

            {!phoneVerified && newPhone !== contactData.phone && (
              <Box>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={handleSendPhoneOTP}
                  disabled={!newPhone || phoneOTPSent}
                  startIcon={<SendIcon />}
                  sx={{ mb: 2 }}
                >
                  {phoneOTPSent ? t('otpSent') : t('sendOtpToPhone')}
                </Button>

                {phoneOTPSent && (
                  <Box display="flex" gap={2} alignItems="stretch">
                    <TextField
                      label={t('enterOtp')}
                      value={phoneOTP}
                      onChange={(e) => setPhoneOTP(e.target.value)}
                      placeholder=""
                      sx={{ flex: 1 }}
                    />
                    <Button
                      variant="contained"
                      onClick={handleVerifyPhoneOTP}
                      disabled={!phoneOTP}
                      sx={{ minWidth: 100 }}
                    >
                      {t('verify')}
                    </Button>
                  </Box>
                )}
              </Box>
            )}

            {phoneVerified && (
              <Alert severity="success" sx={{ mt: 1 }}>
                {t('phoneVerified')}
              </Alert>
            )}
          </Paper>

          {/* Email Address Section */}
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Chip label={t('emailAddress')} color="primary" size="small" />
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('currentEmail')}: <strong>{contactData.email}</strong>
            </Typography>

            <TextField
              fullWidth
              label={t('newEmailAddress')}
              type="email"
              value={newEmail}
              onChange={(e) => {
                setNewEmail(e.target.value);
                setEmailOTPSent(false);
                setEmailVerified(false);
              }}
              placeholder="email@example.com"
              disabled={emailVerified}
              size="medium"
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: emailVerified && (
                  <InputAdornment position="end">
                    <CheckIcon color="success" />
                  </InputAdornment>
                )
              }}
            />

            {!emailVerified && newEmail !== contactData.email && (
              <Box>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={handleSendEmailOTP}
                  disabled={!newEmail || emailOTPSent}
                  startIcon={<SendIcon />}
                  sx={{ mb: 2 }}
                >
                  {emailOTPSent ? t('otpSent') : t('sendOtpToEmail')}
                </Button>

                {emailOTPSent && (
                  <Box display="flex" gap={2} alignItems="stretch">
                    <TextField
                      label={t('enterOtp')}
                      value={emailOTP}
                      onChange={(e) => setEmailOTP(e.target.value)}
                      placeholder="654321"
                      sx={{ flex: 1 }}
                    />
                    <Button
                      variant="contained"
                      onClick={handleVerifyEmailOTP}
                      disabled={!emailOTP}
                      sx={{ minWidth: 100 }}
                    >
                      {t('verify')}
                    </Button>
                  </Box>
                )}
              </Box>
            )}

            {emailVerified && (
              <Alert severity="success" sx={{ mt: 1 }}>
                {t('emailVerified')}
              </Alert>
            )}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdateContactDialog(false)}>{t('cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleSaveContactInfo}
            disabled={
              (!phoneVerified || newPhone === contactData.phone) &&
              (!emailVerified || newEmail === contactData.email)
            }
          >
            {t('saveChanges')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Dialog */}
      <Dialog open={successDialog} onClose={() => setSuccessDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ pb: 1 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <CheckIcon color="success" sx={{ fontSize: 28 }} />
            <Typography variant="h6" fontWeight="bold" color="success.main">
              {t('requestSubmitted')}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body1" fontWeight="bold">
              {successMessage.title}
            </Typography>
          </Alert>

          {successMessage.details && successMessage.details.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              {successMessage.details.map((item, index) => (
                <Box key={index} display="flex" justifyContent="space-between" sx={{ py: 1, borderBottom: index < successMessage.details.length - 1 ? '1px solid #eee' : 'none' }}>
                  <Typography variant="body2" color="text.secondary">
                    {item.label}:
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {item.value}
                  </Typography>
                </Box>
              ))}
            </Paper>
          )}

          {successMessage.footer && (
            <Alert severity="info">
              <Typography variant="body2">
                {successMessage.footer}
              </Typography>
            </Alert>
          )}

          {/* LINE QR Code for Need Support to Pay */}
          {successMessage.showLineQr && lineQrCode && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="subtitle2" fontWeight="bold" color="primary" gutterBottom>
                {t('contactUsViaLine')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('scanQrToChat')}
              </Typography>
              <Box
                sx={{
                  display: 'inline-block',
                  p: 2,
                  bgcolor: 'white',
                  borderRadius: 2,
                  boxShadow: 2,
                  border: '2px solid #00B900'
                }}
              >
                <img
                  src={`data:image/png;base64,${lineQrCode}`}
                  alt="LINE QR Code"
                  style={{ width: 150, height: 150, display: 'block' }}
                />
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => setSuccessDialog(false)}>
            {t('close')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* PDPA Consent Dialog */}
      <Dialog
        open={showPdpaDialog}
        maxWidth="sm"
        fullWidth
        disableEscapeKeyDown
        onClose={(event, reason) => {
          // Prevent closing by clicking outside
          if (reason === 'backdropClick') return;
        }}
      >
        <DialogTitle sx={{ pb: 1, bgcolor: 'primary.main', color: 'white' }}>
          <Typography variant="h6" fontWeight="bold">
            {t('pdpaConsentTitle')}
          </Typography>
        </DialogTitle>
        <DialogContent sx={{ pt: 3 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              {t('pdpaConsentRequired')}
            </Typography>
          </Alert>
          <Paper variant="outlined" sx={{ p: 3, bgcolor: 'grey.50' }}>
            <Typography variant="body1" sx={{ lineHeight: 1.8, textAlign: 'justify' }}>
              {t('pdpaConsentText')}
            </Typography>
          </Paper>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            fullWidth
            onClick={handlePdpaConsent}
            disabled={pdpaConsenting}
          >
            {pdpaConsenting ? t('loading') : t('pdpaAgree')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar Notification */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={snackbar.duration}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
      </Box>
    </Box>
  );
};

export default DebtorPortal;
