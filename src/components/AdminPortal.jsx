import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Avatar,
  LinearProgress,
  Tabs,
  Tab,
  Divider,
  InputAdornment,
  Badge,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  FormControl,
  InputLabel,
  Select,
  ToggleButton,
  ToggleButtonGroup,
  Pagination,
  Skeleton,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  VisibilityOff as VisibilityOffIcon,
  AdminPanelSettings as AdminIcon,
  Logout as LogoutIcon,
  Description as FileIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Notifications as NotificationsIcon,
  Payment as PaymentIcon,
  Warning as WarningIcon,
  MarkEmailRead as MarkReadIcon,
  QrCode as QrCodeIcon,
  Settings as SettingsIcon,
  Image as ImageIcon,
  History as HistoryIcon,
  Assignment as RequestIcon,
  FilterList as FilterIcon,
  SupervisorAccount as SuperAdminIcon,
  PhotoLibrary as PhotoLibraryIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  AccountBalance as BankIcon,
  Save as SaveIcon,
  Lock as LockIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import Grid from '@mui/material/Grid';
import { adminApi, settingsApi } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import LanguageSwitcher from './LanguageSwitcher';
import SuperAdminPortal from './SuperAdminPortal';

const AdminPortal = () => {
  const { t } = useLanguage();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loading, setLoading] = useState(false);


  // Role and Super Admin
  const [userRole, setUserRole] = useState('admin');
  const [showSuperAdmin, setShowSuperAdmin] = useState(false);
  const [systemSettings, setSystemSettings] = useState(null);

  // Image upload states
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageUploadProgress, setImageUploadProgress] = useState(false);
  const [imageUploadResult, setImageUploadResult] = useState(null);
  const [uploadPercentage, setUploadPercentage] = useState(0);
  const [uploadBatchInfo, setUploadBatchInfo] = useState({ current: 0, total: 0, uploaded: 0, failed: 0 });
  const [batchSize, setBatchSize] = useState(25); // Default batch size
  const [isDragging, setIsDragging] = useState(false); // Drag and drop state

  // Bulk QR Code Upload states (replaces PDF processing)
  const [qrFiles, setQrFiles] = useState([]);
  const [qrUploadProgress, setQrUploadProgress] = useState(false);
  const [qrJobs, setQrJobs] = useState([]);
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobPollingInterval, setJobPollingInterval] = useState(null);
  const [isDraggingQr, setIsDraggingQr] = useState(false);
  const [completedJobSummary, setCompletedJobSummary] = useState(null); // Shows for 5 mins after completion

  // Debtor images cache (account_number -> image data)
  const [debtorImages, setDebtorImages] = useState({});

  const [tabValue, setTabValue] = useState('upload_data');

  // Define available tabs - will be filtered based on admin settings
  const allTabs = [
    { key: 'upload_data', label: 'uploadData', icon: UploadIcon },
    { key: 'view_accounts', label: 'viewAccounts', icon: ViewIcon },
    { key: 'debtor_requests', label: 'debtorPaymentsAndRequests', icon: RequestIcon, showBadge: true },
    { key: 'upload_history', label: 'uploadHistory', icon: HistoryIcon },
    { key: 'settings', label: 'settings', icon: SettingsIcon },
  ];

  // Filter visible tabs based on admin_tabs settings
  const visibleTabs = allTabs.filter(tab => {
    // If settings not loaded yet, show all tabs
    if (!systemSettings?.admin_tabs) return true;
    // Check if this tab is enabled (default to true if not specified)
    return systemSettings.admin_tabs[tab.key] !== false;
  });

  // Ensure selected tab is valid (if current tab was hidden, switch to first visible)
  const currentTabValid = visibleTabs.some(tab => tab.key === tabValue);
  const effectiveTabValue = currentTabValid ? tabValue : (visibleTabs[0]?.key || 'upload_data');
  const [debtors, setDebtors] = useState([]);
  const [totalOutstandingBalance, setTotalOutstandingBalance] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(false);
  const [asyncUploadJobId, setAsyncUploadJobId] = useState(null);
  const [asyncUploadStatus, setAsyncUploadStatus] = useState(null);

  const [deleteDialog, setDeleteDialog] = useState({ open: false, debtor: null });
  const [viewDialog, setViewDialog] = useState({ open: false, debtor: null });
  const [dialogImage, setDialogImage] = useState(null);
  const [dialogImageLoading, setDialogImageLoading] = useState(false);

  // Notification states
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationAnchor, setNotificationAnchor] = useState(null);

  // QR Code states
  const [qrCode, setQrCode] = useState(null);
  const [qrCodeFile, setQrCodeFile] = useState(null);
  const [qrCodeUploading, setQrCodeUploading] = useState(false);

  // Bank Account Settings states
  const [bankSettings, setBankSettings] = useState({
    bank_name: '',
    account_name: '',
    account_number: '',
    promptpay_id: '',
  });
  const [bankSettingsSaving, setBankSettingsSaving] = useState(false);
  const [bankSettingsMessage, setBankSettingsMessage] = useState(null);

  // Change Password states
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordChanging, setPasswordChanging] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState(null);

  // Upload History states
  const [uploadHistory, setUploadHistory] = useState([]);

  // Debtor Requests states
  const [requestTypeFilter, setRequestTypeFilter] = useState('all');
  const [requestStatusFilter, setRequestStatusFilter] = useState('all');
  const [requestDetailsDialog, setRequestDetailsDialog] = useState({ open: false, request: null });
  const [receiptDialog, setReceiptDialog] = useState({ open: false, url: null, filename: null, loading: false });

  // Pagination and search states
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 50,
    totalCount: 0,
    totalPages: 0,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [sortModel, setSortModel] = useState([{ field: 'created_at', sort: 'desc' }]);

  // Snackbar notification state
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info', duration: 6000 });

  // Confirmation dialog state
  const [confirmDialog, setConfirmDialog] = useState({ open: false, title: '', message: '', onConfirm: null });

  // Show snackbar notification with optional duration (default 6 seconds)
  const showNotification = (message, severity = 'info', duration = 6000) => {
    setSnackbar({ open: true, message, severity, duration });
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  // Show confirmation dialog
  const showConfirmation = (title, message, onConfirm) => {
    setConfirmDialog({ open: true, title, message, onConfirm });
  };

  const handleCloseConfirmDialog = () => {
    setConfirmDialog({ open: false, title: '', message: '', onConfirm: null });
  };

  const handleConfirmAction = () => {
    if (confirmDialog.onConfirm) {
      confirmDialog.onConfirm();
    }
    handleCloseConfirmDialog();
  };
  const searchTimeoutRef = useRef(null);

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedRole = localStorage.getItem('adminRole');
    if (token) {
      setIsLoggedIn(true);
      setUserRole(savedRole || 'admin');
      fetchDebtors();
      fetchNotifications();
      fetchQrCode();
      fetchUploadHistory();
      fetchSystemSettings();
    } else {
      fetchSystemSettings();
    }
  }, []);

  const fetchSystemSettings = async () => {
    try {
      const response = await settingsApi.getSystemSettings();
      setSystemSettings(response.settings);
      // Load bank settings if available
      if (response.settings?.bank_account) {
        setBankSettings(response.settings.bank_account);
      }
    } catch (error) {
      console.error('Error fetching system settings:', error);
    }
  };

  // Auto-refresh notifications every 5 seconds for near real-time updates
  useEffect(() => {
    if (!isLoggedIn) return;

    const interval = setInterval(() => {
      fetchNotifications();
    }, 5000);

    return () => clearInterval(interval);
  }, [isLoggedIn]);

  // Refetch debtors when pagination, search, or sort changes
  useEffect(() => {
    if (isLoggedIn) {
      fetchDebtors();
    }
  }, [pagination.page, pagination.pageSize, searchQuery, sortModel, isLoggedIn]);

  // Fetch image when view dialog opens
  useEffect(() => {
    if (viewDialog.open && viewDialog.debtor && systemSettings?.enable_image_upload) {
      setDialogImageLoading(true);
      setDialogImage(null);
      adminApi
        .getDebtorImage(viewDialog.debtor.account_number)
        .then((response) => {
          if (response.success && response.image) {
            setDialogImage(response.image);
          }
        })
        .catch((error) => {
          console.error('Error fetching dialog image:', error);
        })
        .finally(() => {
          setDialogImageLoading(false);
        });
    } else {
      setDialogImage(null);
    }
  }, [viewDialog.open, viewDialog.debtor?.account_number, systemSettings?.enable_image_upload]);

  const handleLogin = async () => {
    setLoginError('');
    setLoading(true);

    try {
      const response = await adminApi.login(username, password);
      localStorage.setItem('token', response.token);
      localStorage.setItem('adminRole', response.role);
      setUserRole(response.role);
      setIsLoggedIn(true);
      fetchDebtors();
      fetchNotifications();
      fetchSystemSettings();
    } catch (error) {
      setLoginError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await adminApi.getNotifications();
      setNotifications(response.notifications || []);
      setUnreadCount(response.unread_count || 0);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const handleNotificationClick = (event) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchor(null);
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await adminApi.markNotificationRead(notificationId);
      fetchNotifications();
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await adminApi.markAllNotificationsRead();
      fetchNotifications();
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const fetchQrCode = async () => {
    try {
      const response = await settingsApi.getQrCode();
      if (response.success && response.qr_code?.image) {
        setQrCode(response.qr_code.image);
      } else {
        setQrCode(null);
      }
    } catch (error) {
      console.error('Error fetching QR code:', error);
    }
  };

  const handleQrCodeSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      const validTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
      if (validTypes.includes(file.type) || file.name.match(/\.(png|jpg|jpeg|gif|webp)$/i)) {
        setQrCodeFile(file);
      } else {
        showNotification(t('invalidImageFile') || 'Please select a valid image file (PNG, JPG, GIF, WEBP)', 'warning');
      }
    }
  };

  const handleQrCodeUpload = async () => {
    if (!qrCodeFile) {
      showNotification(t('selectFileFirst') || 'Please select a file first', 'warning');
      return;
    }

    setQrCodeUploading(true);
    try {
      await adminApi.uploadQrCode(qrCodeFile);
      setQrCodeFile(null);
      fetchQrCode();
      showNotification(t('qrCodeUploadSuccess') || 'QR code uploaded successfully!', 'success');
    } catch (error) {
      showNotification(t('qrCodeUploadError') || 'Error uploading QR code: ' + error.message, 'error');
    } finally {
      setQrCodeUploading(false);
    }
  };

  const handleQrCodeDeleteConfirmed = async () => {
    try {
      await adminApi.deleteQrCode();
      setQrCode(null);
      showNotification(t('qrCodeDeleteSuccess') || 'QR code deleted successfully!', 'success');
    } catch (error) {
      showNotification(t('qrCodeDeleteError') || 'Error deleting QR code: ' + error.message, 'error');
    }
  };

  const handleQrCodeDelete = () => {
    showConfirmation(
      t('deleteQrCode') || 'Delete QR Code',
      t('confirmDeleteQrCode') || 'Are you sure you want to delete the QR code?',
      handleQrCodeDeleteConfirmed
    );
  };

  // Bank Settings handlers
  const handleBankSettingChange = (field) => (event) => {
    setBankSettings((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));
    setBankSettingsMessage(null);
  };

  const handleSaveBankSettings = async () => {
    setBankSettingsSaving(true);
    setBankSettingsMessage(null);
    try {
      const { superAdminApi } = await import('../services/api');
      await superAdminApi.updateSystemSettings({ bank_account: bankSettings });
      setBankSettingsMessage({ type: 'success', text: t('bankSettingsSaved') });
      fetchSystemSettings();
    } catch (error) {
      console.error('Error saving bank settings:', error);
      setBankSettingsMessage({ type: 'error', text: t('bankSettingsFailed') + ': ' + error.message });
    } finally {
      setBankSettingsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    setPasswordMessage(null);

    if (!currentPassword) {
      setPasswordMessage({ type: 'error', text: t('currentPasswordRequired') });
      return;
    }
    if (!newPassword) {
      setPasswordMessage({ type: 'error', text: t('newPasswordRequired') });
      return;
    }
    if (newPassword.length < 6) {
      setPasswordMessage({ type: 'error', text: t('passwordMinLength') });
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordMessage({ type: 'error', text: t('passwordsDoNotMatch') });
      return;
    }

    setPasswordChanging(true);
    try {
      await adminApi.changePassword(currentPassword, newPassword);
      setPasswordMessage({ type: 'success', text: t('passwordChangedSuccess') });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (error) {
      console.error('Error changing password:', error);
      setPasswordMessage({ type: 'error', text: error.message || t('passwordChangeFailed') });
    } finally {
      setPasswordChanging(false);
    }
  };

  const fetchUploadHistory = async () => {
    try {
      const response = await adminApi.getUploadHistory();
      setUploadHistory(response.history || []);
    } catch (error) {
      console.error('Error fetching upload history:', error);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
      timeZone: 'Asia/Bangkok',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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

  // Format currency in Thai Baht
  const formatCurrency = (amount) => {
    return `฿${(amount || 0).toLocaleString()}`;
  };

  // Get filtered requests for the Debtor Requests tab
  const getFilteredRequests = () => {
    return notifications.filter((notification) => {
      // Filter by type
      if (requestTypeFilter !== 'all') {
        // Handle both old 'payment_request' and new 'payment_submitted' types
        if (requestTypeFilter === 'payment_submitted' &&
            notification.type !== 'payment_submitted' && notification.type !== 'payment_request') {
          return false;
        }
        if (requestTypeFilter === 'not_ready_to_pay' && notification.type !== 'not_ready_to_pay') {
          return false;
        }
      }
      // Filter by read status
      if (requestStatusFilter !== 'all') {
        if (requestStatusFilter === 'read' && !notification.read) {
          return false;
        }
        if (requestStatusFilter === 'unread' && notification.read) {
          return false;
        }
      }
      return true;
    });
  };

  const handleDownloadFile = async (uploadId, filename) => {
    try {
      const response = await adminApi.downloadUploadFile(uploadId);
      if (response.success && response.file_content) {
        // Convert base64 to blob
        const byteCharacters = atob(response.file_content);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: response.content_type });

        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.filename || filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      showNotification(t('errorDownloadingFile') || 'Error downloading file: ' + error.message, 'error');
    }
  };

  const handleViewReceipt = async (filename) => {
    setReceiptDialog({ open: true, url: null, filename, loading: true });
    try {
      const blob = await adminApi.getPaymentReceipt(filename);
      const url = window.URL.createObjectURL(blob);
      setReceiptDialog({ open: true, url, filename, loading: false });
    } catch (error) {
      showNotification(t('errorLoadingReceipt') || 'Error loading receipt: ' + error.message, 'error');
      setReceiptDialog({ open: false, url: null, filename: null, loading: false });
    }
  };

  const handleDownloadReceipt = () => {
    if (receiptDialog.url && receiptDialog.filename) {
      const a = document.createElement('a');
      a.href = receiptDialog.url;
      a.download = receiptDialog.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  const handleCloseReceiptDialog = () => {
    if (receiptDialog.url) {
      window.URL.revokeObjectURL(receiptDialog.url);
    }
    setReceiptDialog({ open: false, url: null, filename: null, loading: false });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('adminRole');
    setIsLoggedIn(false);
    setUserRole('admin');
    setShowSuperAdmin(false);
    setDebtors([]);
    setTotalOutstandingBalance(0);
    setUsername('');
    setPassword('');
  };

  // Image upload handlers
  const processFiles = (files) => {
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter((file) => {
      const validTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'application/pdf'];
      const validExtensions = /\.(png|jpg|jpeg|gif|webp|pdf)$/i;
      // Check both MIME type and file extension (some systems don't set MIME correctly)
      return validTypes.includes(file.type) || validExtensions.test(file.name);
    });
    setSelectedImages(validFiles);
    setImageUploadResult(null);
    setUploadPercentage(0);
    setUploadBatchInfo({ current: 0, total: 0, uploaded: 0, failed: 0 });
  };

  const handleImageSelect = (event) => {
    processFiles(event.target.files);
  };

  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set dragging to false if we're leaving the drop zone entirely
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processFiles(files);
    }
  };

  const handleImageUpload = async () => {
    if (selectedImages.length === 0) {
      showNotification(t('selectImagesFirst') || 'Please select images first', 'warning');
      return;
    }

    setImageUploadProgress(true);
    setImageUploadResult(null);
    setUploadPercentage(0);

    const totalFiles = selectedImages.length;
    const totalBatches = Math.ceil(totalFiles / batchSize);

    let totalUploaded = 0;
    let totalFailed = 0;
    let allErrors = [];
    let allNotFound = [];

    setUploadBatchInfo({ current: 0, total: totalBatches, uploaded: 0, failed: 0 });

    try {
      for (let i = 0; i < totalBatches; i++) {
        const start = i * batchSize;
        const end = Math.min(start + batchSize, totalFiles);
        const batch = selectedImages.slice(start, end);

        setUploadBatchInfo(prev => ({ ...prev, current: i + 1 }));

        try {
          const response = await adminApi.uploadDebtorImages(batch);

          // Backend returns counts as numbers, not arrays
          if (response.uploaded) {
            totalUploaded += response.uploaded;
          }
          if (response.not_found) {
            // not_found is a count number
            allNotFound.push(response.not_found);
          }
          if (response.errors && Array.isArray(response.errors)) {
            allErrors = [...allErrors, ...response.errors];
            totalFailed += response.errors.length;
          }
        } catch (batchError) {
          totalFailed += batch.length;
          allErrors.push(`Batch ${i + 1} failed: ${batchError.message}`);
        }

        // Update progress percentage
        const progress = Math.round(((i + 1) / totalBatches) * 100);
        setUploadPercentage(progress);
        setUploadBatchInfo(prev => ({
          ...prev,
          uploaded: totalUploaded,
          failed: totalFailed
        }));
      }

      // Sum up not_found counts from all batches
      const totalNotFound = allNotFound.reduce((sum, count) => sum + count, 0);

      setImageUploadResult({
        success: totalUploaded > 0,
        message: `Upload complete: ${totalUploaded.toLocaleString()} uploaded, ${totalNotFound.toLocaleString()} not found in DB, ${totalFailed.toLocaleString()} failed`,
        uploaded: totalUploaded,
        notFound: totalNotFound,
        errors: allErrors,
      });
      setSelectedImages([]);

      // Refresh debtors to show updated images
      fetchDebtors();
    } catch (error) {
      setImageUploadResult({
        success: false,
        message: error.message || 'Image upload failed',
      });
    } finally {
      setImageUploadProgress(false);
    }
  };

  // ============================================
  // BULK QR CODE UPLOAD FUNCTIONS
  // ============================================

  const handleQrSelect = (event) => {
    const files = Array.from(event.target.files).filter(
      (file) => {
        const name = file.name.toLowerCase();
        return name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg') || 
               name.endsWith('.gif') || name.endsWith('.webp') || name.endsWith('.pdf') || 
               name.endsWith('.zip');
      }
    );
    setQrFiles(files);
  };

  const handleQrDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingQr(true);
  };

  const handleQrDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDraggingQr(false);
  };

  const handleQrDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleQrDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingQr(false);

    const files = Array.from(e.dataTransfer.files).filter(
      (file) => {
        const name = file.name.toLowerCase();
        return name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg') || 
               name.endsWith('.gif') || name.endsWith('.webp') || name.endsWith('.pdf') || 
               name.endsWith('.zip');
      }
    );
    if (files.length > 0) {
      setQrFiles(files);
    }
  };

  const [qrUploadInfo, setQrUploadInfo] = useState({ 
    current: 0, 
    total: 0, 
    uploaded: 0, 
    status: '', 
    message: '',
    percentage: 0 
  });

  const handleUploadQrCodes = async () => {
    console.log('handleUploadQrCodes function called');
    console.log('qrFiles:', qrFiles);
    console.log('qrFiles length:', qrFiles?.length || 0);
    
    if (qrFiles.length === 0) {
      console.log('No files, returning early');
      return;
    }

    console.log('Setting upload progress to true');
    setQrUploadProgress(true);
    
    console.log('Checking if single file upload');
    // For single file (ZIP, PDF, or image), use async upload with progress
    if (qrFiles.length === 1) {
      console.log('Single file upload path');
      const file = qrFiles[0];
      const fileName = file.name.toLowerCase();
      
      // Check if it's a ZIP, PDF, or single image
      if (fileName.endsWith('.zip') || fileName.endsWith('.pdf') || 
          fileName.match(/\.(png|jpg|jpeg|gif|webp|bmp)$/)) {
        
        setQrUploadInfo({ 
          current: 1, 
          total: 1, 
          uploaded: 0, 
          status: 'preparing',
          message: 'Preparing upload...',
          percentage: 0
        });

        try {
          console.log('Starting QR upload with stageQrFiles...');
          const response = await adminApi.stageQrFiles(qrFiles, (progress) => {
            console.log('Progress callback received:', progress);
            console.log('Progress type:', typeof progress);
            console.log('Progress keys:', progress ? Object.keys(progress) : 'null progress');
            
            // Safely extract progress values
            const safeProgress = {
              current: 1,
              total: 1,
              uploaded: Number(progress?.uploaded_count || 0),
              status: String(progress?.status || 'processing'),
              message: String(progress?.message || 'Processing...'),
              percentage: Number(progress?.percentage || 0),
              total_images: Number(progress?.total_images || 0),
              processed_images: Number(progress?.processed_images || 0),
              not_found: Number(progress?.not_found_count || 0),
              error_count: Number(progress?.error_count || 0),
            };
            
            console.log('Setting safe progress:', safeProgress);
            setQrUploadInfo(safeProgress);
          });

          console.log('QR upload response received:', response);
          console.log('Full response object:', JSON.stringify(response, null, 2));
          
          // Wrap the entire completion handling in try-catch
          try {
            // Safely handle uploaded count
            const uploadedCount = typeof response.uploaded === 'number' ? response.uploaded : 0;
            const notFoundCount = typeof response.not_found === 'number' ? response.not_found : 0;
            const errorsArray = Array.isArray(response.errors) ? response.errors : [];
            
            console.log('Safe values extracted - uploadedCount:', uploadedCount, 'notFoundCount:', notFoundCount, 'errorsArray length:', errorsArray.length);

            let message = `Successfully uploaded ${uploadedCount.toString()} QR images`;
            console.log('Base message created:', message);
            
            if (notFoundCount > 0) {
              message += `, ${notFoundCount} not matched (no debtor found)`;
              console.log('Added not_found to message:', message);
            }
            
            if (errorsArray.length > 0) {
              console.log('Processing errors array of length:', errorsArray.length);
              try {
                const errorSample = errorsArray.slice(0, 3);
                console.log('Error sample extracted:', errorSample);
                const errorText = errorSample.join(', ');
                console.log('Error text joined:', errorText);
                message += `. Errors: ${errorText}`;
                console.log('Added errors to message:', message);
              } catch (errorProcessingErr) {
                console.error('Error processing errors array:', errorProcessingErr);
                message += `. ${errorsArray.length} errors found`;
                console.log('Added fallback error message:', message);
              }
            }
            
            console.log('Final message prepared:', message);
            
            // Show notification with extra safety
            try {
              console.log('Calling showNotification...');
              const severity = errorsArray.length > 0 ? 'warning' : 'success';
              console.log('Notification severity:', severity);
              showNotification(message, severity, 10000);
              console.log('showNotification completed successfully');
            } catch (notificationErr) {
              console.error('Error in showNotification:', notificationErr);
              // Fallback notification
              alert(`QR Upload Complete: ${message}`);
            }
            
            // Clear files with safety
            try {
              console.log('Clearing QR files...');
              setQrFiles([]);
              console.log('QR files cleared successfully');
            } catch (clearErr) {
              console.error('Error clearing QR files:', clearErr);
            }
            
            // Refresh images with safety
            try {
              console.log('Refreshing debtors list...');
              await fetchDebtors();
              console.log('Debtors list refreshed successfully');
            } catch (fetchErr) {
              console.error('Error refreshing debtors:', fetchErr);
            }
            
          } catch (completionError) {
            console.error('Error in completion handling:', completionError);
            console.error('Completion error stack:', completionError.stack);
            showNotification('Upload completed but there was an error displaying results. Please refresh to see updated images.', 'warning');
          }
          
        } catch (error) {
          console.error('QR upload error:', error);
          console.error('Error stack:', error.stack);
          console.error('Error details:', {
            message: error.message,
            name: error.name,
            toString: error.toString()
          });
          showNotification(error.message || 'Failed to upload QR codes', 'error');
        } finally {
          setQrUploadProgress(false);
          setQrUploadInfo({ current: 0, total: 0, uploaded: 0, status: '', message: '', percentage: 0 });
        }
        return;
      }
    }

    // For multiple individual images, batch process
    const BATCH_SIZE = 500;
    const totalFiles = qrFiles.length;
    const totalBatches = Math.ceil(totalFiles / BATCH_SIZE);
    let totalUploaded = 0;

    setQrUploadInfo({ current: 0, total: totalBatches, uploaded: 0, status: 'uploading', message: 'Uploading...', percentage: 0 });

    try {
      let allErrors = [];
      let totalNotFound = 0;
      let totalSkipped = 0;
      
      for (let i = 0; i < totalBatches; i++) {
        const start = i * BATCH_SIZE;
        const end = Math.min(start + BATCH_SIZE, totalFiles);
        const batch = qrFiles.slice(start, end);

        setQrUploadInfo({ 
          current: i + 1, 
          total: totalBatches, 
          uploaded: totalUploaded,
          status: 'uploading',
          message: `Uploading batch ${i + 1} of ${totalBatches}...`,
          percentage: Math.round((i / totalBatches) * 100)
        });

        const response = await adminApi.stageQrFiles(batch);
        console.log('Batch response:', response);
        totalUploaded += response.uploaded || 0;
        totalNotFound += response.not_found || 0;
        totalSkipped += response.skipped || 0;
        
        if (response.errors) {
          if (Array.isArray(response.errors)) {
            allErrors = allErrors.concat(response.errors);
          } else if (typeof response.errors === 'string') {
            allErrors.push(response.errors);
          }
        }
      }

      // Build detailed message: X uploaded, Y skipped, Z not found, W errors
      let messageParts = [];
      messageParts.push(`${totalUploaded} uploaded`);
      if (totalSkipped > 0) {
        messageParts.push(`${totalSkipped} skipped (already have QR)`);
      }
      if (totalNotFound > 0) {
        messageParts.push(`${totalNotFound} not found (no matching debtor)`);
      }
      if (allErrors.length > 0) {
        messageParts.push(`${allErrors.length} errors`);
      }
      
      let message = `QR Upload Complete: ${messageParts.join(', ')}`;
      console.log('Multiple files upload completed with message:', message);
      showNotification(message, (allErrors.length > 0 || totalNotFound > 0) ? 'warning' : 'success', 10000);
      setQrFiles([]);
      console.log('Refreshing debtors list after upload...');
      await fetchDebtors();
      console.log('Debtors list refreshed successfully');
    } catch (error) {
      console.error('QR upload error:', error);
      const errorMessage = error.message || error.toString() || 'Failed to upload QR codes';
      showNotification(errorMessage, 'error');
    } finally {
      setQrUploadProgress(false);
      setQrUploadInfo({ current: 0, total: 0, uploaded: 0, status: '', message: '', percentage: 0 });
    }
  };

  // Legacy PDF functions for backward compatibility
  const handlePdfSelect = handleQrSelect;
  const handlePdfDragEnter = handleQrDragEnter;
  const handlePdfDragLeave = handleQrDragLeave;
  const handlePdfDragOver = handleQrDragOver;
  const handlePdfDrop = handleQrDrop;
  const pdfFiles = qrFiles;
  const isDraggingPdf = isDraggingQr;
  const pdfStagingProgress = qrUploadProgress;
  const pdfStagingInfo = qrUploadInfo;
  const pdfJobs = qrJobs;
  const setPdfJobs = setQrJobs;

  const handleStagePdfs = async () => {
    return handleUploadQrCodes();
  };

  const fetchPdfJobs = async () => {
    // Legacy function - no longer fetches jobs since bulk QR upload is direct
    console.log('fetchPdfJobs called - no jobs to fetch for direct QR upload');
  };

  const handleStartProcessing = async (jobId) => {
    // Legacy function - no longer needed since bulk QR upload is direct
    console.log('handleStartProcessing called - not needed for direct QR upload');
  };

  const startJobPolling = (jobId) => {
    // Legacy function - no longer needed since bulk QR upload is direct
    console.log('startJobPolling called - not needed for direct QR upload');
  };

  // Fetch PDF jobs on mount and when tab changes
  useEffect(() => {
    if (isLoggedIn && effectiveTabValue === 'upload_data') {
      fetchPdfJobs();
    }
    return () => {
      if (jobPollingInterval) {
        clearInterval(jobPollingInterval);
      }
    };
  }, [isLoggedIn, effectiveTabValue]);

  // Fetch image for a specific debtor
  const fetchDebtorImage = async (accountNumber) => {
    try {
      const response = await adminApi.getDebtorImage(accountNumber);
      if (response.success && response.image) {
        setDebtorImages((prev) => ({
          ...prev,
          [accountNumber]: response.image,
        }));
      }
    } catch (error) {
      console.error(`Error fetching image for ${accountNumber}:`, error);
    }
  };

  // Fetch images for multiple debtors
  const fetchDebtorImages = async (accountNumbers) => {
    // Safety check - if no account numbers provided, fetch debtors first
    if (!accountNumbers || !Array.isArray(accountNumbers) || accountNumbers.length === 0) {
      console.log('fetchDebtorImages called without account numbers, refreshing debtors instead');
      await fetchDebtors();
      return;
    }
    
    for (const accountNumber of accountNumbers) {
      await fetchDebtorImage(accountNumber);
    }
  };

  const fetchDebtors = useCallback(async (options = {}) => {
    setLoading(true);
    try {
      const sortBy = sortModel.length > 0 ? sortModel[0].field : 'created_at';
      const sortOrder = sortModel.length > 0 ? sortModel[0].sort : 'desc';

      const response = await adminApi.getAllDebtors({
        page: options.page || pagination.page,
        pageSize: options.pageSize || pagination.pageSize,
        search: options.search !== undefined ? options.search : searchQuery,
        sortBy: sortBy,
        sortOrder: sortOrder,
      });

      setDebtors(response.debtors || []);
      setTotalOutstandingBalance(response.total_outstanding_balance || 0);
      if (response.pagination) {
        setPagination((prev) => ({
          ...prev,
          page: response.pagination.page,
          pageSize: response.pagination.page_size,
          totalCount: response.pagination.total_count,
          totalPages: response.pagination.total_pages,
        }));
      }

      // Fetch images for visible debtors (batch request)
      if (response.debtors && response.debtors.length > 0 && systemSettings?.enable_image_upload) {
        const accountNumbers = response.debtors.map((d) => d.account_number);
        fetchDebtorImagesBatch(accountNumbers);
      }
    } catch (error) {
      console.error('Error fetching debtors:', error);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, searchQuery, sortModel, systemSettings?.enable_image_upload]);

  // Batch fetch images for visible debtors
  const fetchDebtorImagesBatch = async (accountNumbers) => {
    try {
      const response = await adminApi.getDebtorImagesBatch(accountNumbers);
      if (response.success && response.images) {
        setDebtorImages((prev) => ({
          ...prev,
          ...response.images,
        }));
      }
    } catch (error) {
      console.error('Error fetching debtor images batch:', error);
    }
  };

  // Handle search with debounce
  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchInput(value);

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce search - wait 500ms after user stops typing
    searchTimeoutRef.current = setTimeout(() => {
      setSearchQuery(value);
      setPagination((prev) => ({ ...prev, page: 1 }));
    }, 500);
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (event, newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  };

  const handleSortModelChange = (newSortModel) => {
    setSortModel(newSortModel);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    const files = Array.from(event.target.files || []);
    if (files.length > 0) {
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv',
      ];
      const validFiles = files.filter(file => 
        validTypes.includes(file.type) || file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv')
      );
      
      if (validFiles.length === 0) {
        showNotification(t('selectValidExcelFile') || 'Please select valid files (.xlsx, .xls, or .csv)', 'warning');
      } else {
        setSelectedFiles(validFiles);
        setUploadResult(null);
        if (validFiles.length < files.length) {
          showNotification(`${validFiles.length} valid files selected, ${files.length - validFiles.length} invalid files skipped`, 'info');
        }
      }
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      showNotification(t('selectFileFirst') || 'Please select at least one file first', 'warning');
      return;
    }

    setUploadProgress(true);
    setUploadResult(null);
    setAsyncUploadJobId(null);
    setAsyncUploadStatus(null);

    try {
      // Upload all files sequentially
      let totalInserted = 0;
      let totalUpdated = 0;
      const results = [];

      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        setUploadResult({
          success: true,
          message: `Processing file ${i + 1}/${selectedFiles.length}: ${file.name}...`,
          inserted: totalInserted,
          updated: totalUpdated
        });

        const response = await adminApi.uploadExcel(file, (progress) => {
          // Update UI with progress
          setAsyncUploadStatus({
            status: progress.status,
            message: progress.message,
            percentage: progress.percentage,
            processed_records: progress.processed,
            total_records: progress.total,
            inserted_count: progress.inserted,
            updated_count: progress.updated,
          });
          
          // Update result message for user visibility
          setUploadResult({
            success: true,
            message: `File ${i + 1}/${selectedFiles.length}: ${progress.message}`,
            isAsync: true,
            status: progress.status,
          });
        });
        
        // Accumulate results
        if (response.success) {
          totalInserted += response.inserted || 0;
          totalUpdated += response.updated || 0;
          results.push({
            filename: file.name,
            inserted: response.inserted || 0,
            updated: response.updated || 0
          });
        }
      }

      // Show final results
      const resultMessage = results.map(r => 
        `${r.filename}: ${r.inserted} inserted, ${r.updated} updated`
      ).join('\\n');

      setUploadResult({
        success: true,
        message: `All ${selectedFiles.length} file(s) processed!\\n${resultMessage}`,
        inserted: totalInserted,
        updated: totalUpdated
      });
      
      showNotification(
        `✓ All files processed. Total - Inserted: ${totalInserted}, Updated: ${totalUpdated}`,
        'success',
        8000
      );
      
      setSelectedFiles([]);
      fetchDebtors();
      fetchUploadHistory();
    } catch (error) {
      console.error('Excel upload error:', error);
      const errorMessage = error.message || 'Upload failed';
      setUploadResult({
        success: false,
        message: errorMessage,
      });
      showNotification(errorMessage, 'error', 10000);
      setSelectedFiles([]);
    } finally {
      setUploadProgress(false);
    }
  };

  const pollAsyncUploadStatus = async (jobId) => {
    let pollingCount = 0;
    const maxPolls = 120; // 10 minutes max (5s intervals)
    
    const poll = async () => {
      try {
        const status = await adminApi.getUploadStatus(jobId);
        setAsyncUploadStatus(status);
        
        if (status.status === 'completed') {
          setUploadProgress(false);
          setUploadResult({
            success: true,
            message: `Upload completed! Processed ${status.processed_records} records. Inserted: ${status.inserted_count}, Updated: ${status.updated_count}`,
            inserted: status.inserted_count,
            updated: status.updated_count,
          });
          setSelectedFiles([]);
          fetchDebtors();
          fetchUploadHistory();
          return;
        } else if (status.status === 'failed') {
          setUploadProgress(false);
          setUploadResult({
            success: false,
            message: `Upload failed: ${Array.isArray(status.errors) ? status.errors.join(', ') : (status.errors || 'Unknown error')}`,
          });
          return;
        }
        
        // Continue polling if still processing
        pollingCount++;
        if (pollingCount < maxPolls && (status.status === 'staged' || status.status === 'processing')) {
          setTimeout(poll, 10000); // Poll every 10 seconds for real-time progress
        } else if (pollingCount >= maxPolls) {
          setUploadProgress(false);
          setUploadResult({
            success: false,
            message: 'Upload timeout - check upload history for final status',
          });
        }
      } catch (error) {
        console.error('Error polling upload status:', error);
        pollingCount++;
        if (pollingCount < maxPolls) {
          setTimeout(poll, 10000);
        } else {
          setUploadProgress(false);
          setUploadResult({
            success: false,
            message: 'Error checking upload status',
          });
        }
      }
    };
    
    poll();
  };

  const handleDeleteDebtor = async () => {
    if (!deleteDialog.debtor) return;

    try {
      await adminApi.deleteDebtor(deleteDialog.debtor.account_number);
      setDeleteDialog({ open: false, debtor: null });
      fetchDebtors();
    } catch (error) {
      showNotification(t('errorDeletingDebtor') || 'Error deleting debtor: ' + error.message, 'error');
    }
  };

  const downloadTemplate = () => {
    // Create sample data with National ID
    const templateData = `Account Number,National ID,Original Creditor,Outstanding Balance,Debt Type,Loan CONTRACT DATE,Name,Phone,Email
ACC-10001,NID-123456789,ABC Bank,12500.00,Credit Card,2024-01-15,John Smith,+1-555-0123,john.smith@email.com
ACC-10002,NID-987654321,XYZ Finance,8750.50,Personal Loan,2024-02-20,Jane Doe,+1-555-0456,jane.doe@email.com`;

    const blob = new Blob([templateData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'debtor_upload_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Super Admin Portal
  if (showSuperAdmin && userRole === 'super_admin') {
    return (
      <SuperAdminPortal
        onLogout={handleLogout}
        onSwitchToAdmin={() => {
          setShowSuperAdmin(false);
          fetchSystemSettings();
        }}
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
          background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)',
          p: 3,
        }}
      >
        <Card sx={{ maxWidth: 450, width: '100%', boxShadow: '0 20px 60px rgba(0,0,0,0.3)' }}>
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
                <AdminIcon sx={{ fontSize: 40 }} />
              </Avatar>
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                {t('adminPortalTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('signInToManage')}
              </Typography>
            </Box>

            {loginError && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {loginError}
              </Alert>
            )}

            <TextField
              fullWidth
              label={t('username')}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{ mb: 2 }}
              onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
            />

            <TextField
              fullWidth
              label={t('password')}
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{ mb: 3 }}
              onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                      {showPassword ? <VisibilityOffIcon /> : <ViewIcon />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleLogin}
              disabled={loading || !username || !password}
            >
              {loading ? t('signingIn') : t('signIn')}
            </Button>

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

  // Admin Dashboard
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 100%)',
          color: 'white',
          borderRadius: 0,
        }}
      >
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          maxWidth="lg"
          mx="auto"
          flexWrap="wrap"
          gap={1}
        >
          <Box display="flex" alignItems="center" gap={{ xs: 1, sm: 2 }}>
            <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: { xs: 36, sm: 40 }, height: { xs: 36, sm: 40 } }}>
              <AdminIcon />
            </Avatar>
            <Box>
              <Typography variant="h5" fontWeight="bold" sx={{ fontSize: { xs: '1.1rem', sm: '1.5rem' } }}>
                {t('adminDashboard')}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" alignItems="center" gap={{ xs: 0.5, sm: 2 }}>
            {/* Language Switcher */}
            <LanguageSwitcher variant="outlined-white" size="small" />
            {/* Notification Icon */}
            <IconButton
              onClick={handleNotificationClick}
              sx={{ color: 'white' }}
            >
              <Badge badgeContent={unreadCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            {userRole === 'super_admin' && (
              <IconButton
                onClick={() => setShowSuperAdmin(true)}
                sx={{
                  color: 'white',
                  border: '1px solid white',
                  borderRadius: 1,
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
                  display: { xs: 'flex', md: 'none' },
                }}
              >
                <SuperAdminIcon />
              </IconButton>
            )}
            {userRole === 'super_admin' && (
              <Button
                variant="outlined"
                onClick={() => setShowSuperAdmin(true)}
                startIcon={<SuperAdminIcon />}
                sx={{
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
                  display: { xs: 'none', md: 'flex' },
                }}
              >
                Super Admin
              </Button>
            )}
            {/* Mobile: Icon only */}
            <IconButton
              onClick={handleLogout}
              sx={{
                color: 'white',
                border: '1px solid white',
                borderRadius: 1,
                '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
                display: { xs: 'flex', sm: 'none' },
              }}
            >
              <LogoutIcon />
            </IconButton>
            {/* Desktop: Full button */}
            <Button
              variant="outlined"
              onClick={handleLogout}
              startIcon={<LogoutIcon />}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
                display: { xs: 'none', sm: 'flex' },
              }}
            >
              {t('logout')}
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Notification Menu */}
      <Menu
        anchorEl={notificationAnchor}
        open={Boolean(notificationAnchor)}
        onClose={handleNotificationClose}
        PaperProps={{
          sx: {
            width: 380,
            maxHeight: 480,
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #eee' }}>
          <Typography variant="h6" fontWeight="bold">
            {t('notifications')}
          </Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={handleMarkAllAsRead} startIcon={<MarkReadIcon />}>
              {t('markAllRead')}
            </Button>
          )}
        </Box>
        {notifications.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <NotificationsIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
            <Typography color="text.secondary">{t('noNotifications')}</Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {notifications.map((notification) => (
              <ListItem
                key={notification._id}
                sx={{
                  bgcolor: notification.read ? 'transparent' : 'action.hover',
                  borderBottom: '1px solid #f0f0f0',
                  '&:hover': { bgcolor: 'action.selected' },
                }}
                secondaryAction={
                  !notification.read && (
                    <IconButton
                      size="small"
                      onClick={() => handleMarkAsRead(notification._id)}
                      title="Mark as read"
                    >
                      <MarkReadIcon fontSize="small" />
                    </IconButton>
                  )
                }
              >
                <ListItemAvatar>
                  <Avatar
                    sx={{
                      bgcolor: notification.type === 'payment_request' ? 'success.light' : 'warning.light',
                    }}
                  >
                    {notification.type === 'payment_request' ? (
                      <PaymentIcon color="success" />
                    ) : (
                      <WarningIcon color="warning" />
                    )}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box>
                      <Typography variant="subtitle2" fontWeight={notification.read ? 'normal' : 'bold'}>
                        {notification.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                        {notification.message}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Chip
                        size="small"
                        label={notification.debtor?.account_number || 'N/A'}
                        sx={{ mr: 1, fontSize: '0.7rem' }}
                      />
                      <Typography variant="caption" color="text.disabled">
                        {formatTimeAgo(notification.created_at)}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Menu>

      <Box sx={{ maxWidth: 'lg', mx: 'auto', px: 3, pb: 4 }}>
        {/* Stats Cards */}
        <Box display="flex" gap={3} mb={3} flexWrap="wrap">
          <Card sx={{ flex: 1, minWidth: 200 }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                {t('totalAccounts')}
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="primary">
                {pagination.totalCount.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
          <Card sx={{ flex: 1, minWidth: 200 }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                {t('totalOutstanding')}
              </Typography>
              <Typography variant="h3" fontWeight="bold" color="error.main">
                {formatCurrency(totalOutstandingBalance)}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Tabs */}
        <Card>
          <Tabs
            value={effectiveTabValue}
            onChange={(e, v) => setTabValue(v)}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{ bgcolor: 'grey.50', borderBottom: 1, borderColor: 'divider' }}
          >
            {visibleTabs.map((tab) => {
              const IconComponent = tab.icon;
              return (
                <Tab
                  key={tab.key}
                  value={tab.key}
                  label={t(tab.label)}
                  icon={
                    tab.showBadge ? (
                      <Badge badgeContent={notifications.filter(n => !n.read).length} color="error" max={99}>
                        <IconComponent />
                      </Badge>
                    ) : (
                      <IconComponent />
                    )
                  }
                  iconPosition="start"
                  sx={{
                    minHeight: { xs: 48, sm: 64 },
                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    px: { xs: 1, sm: 2 },
                  }}
                />
              );
            })}
          </Tabs>

          <CardContent sx={{ p: 4 }}>
            {/* Upload Tab */}
            {effectiveTabValue === 'upload_data' && (
              <Box>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  {t('uploadDebtorData')}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {t('uploadDescription')}
                </Typography>

                <Paper variant="outlined" sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    {t('requiredColumns')}:
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {[
                      'Account Number',
                      'National ID',
                      'Original Creditor',
                      'Outstanding Balance',
                      'Debt Type',
                      'Charge-off Date',
                      'Name',
                      'Phone',
                      'Email',
                    ].map((col) => (
                      <Chip key={col} label={col} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Paper>

                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={downloadTemplate}
                  sx={{ mb: 3 }}
                >
                  {t('downloadTemplate')}
                </Button>

                <Divider sx={{ my: 3 }} />

                <Paper
                  variant="outlined"
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    bgcolor: selectedFiles.length > 0 ? 'success.light' : 'grey.50',
                    border: '2px dashed',
                    borderColor: selectedFiles.length > 0 ? 'success.main' : 'grey.300',
                    cursor: 'pointer',
                  }}
                  onClick={() => document.getElementById('file-input').click()}
                >
                  <input
                    id="file-input"
                    type="file"
                    multiple
                    accept=".xlsx,.xls,.csv"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                  {selectedFiles.length > 0 ? (
                    <Box>
                      <FileIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                      <Typography variant="body1" fontWeight="bold">
                        {selectedFiles.length} file(s) selected
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {selectedFiles.map(f => f.name).join(', ')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total: {(selectedFiles.reduce((sum, f) => sum + f.size, 0) / 1024).toFixed(2)} KB
                      </Typography>
                    </Box>
                  ) : (
                    <Box>
                      <UploadIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                      <Typography variant="body1">
                        {t('clickToSelect')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('supportedFormats')}: .xlsx, .xls, .csv
                      </Typography>
                    </Box>
                  )}
                </Paper>

                {uploadProgress && (
                  <>
                    <LinearProgress sx={{ mt: 2 }} />
                    {asyncUploadStatus && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                        <Typography variant="body2" fontWeight="bold" color="info.main">
                          Upload Status: {asyncUploadStatus.status?.toUpperCase()}
                        </Typography>
                        {asyncUploadStatus.processed_records !== undefined && (
                          <Typography variant="body2" color="info.main">
                            Processed: {asyncUploadStatus.processed_records} records
                          </Typography>
                        )}
                        {asyncUploadStatus.total_records && (
                          <Typography variant="body2" color="info.main">
                            Remaining: {asyncUploadStatus.total_records - (asyncUploadStatus.processed_records || 0)} records
                          </Typography>
                        )}
                        {asyncUploadStatus.percentage !== undefined && (
                          <Typography variant="body2" color="info.main">
                            Progress: {Math.round(asyncUploadStatus.percentage || 0)}%
                          </Typography>
                        )}
                      </Box>
                    )}
                  </>
                )}

                {uploadResult && (
                  <Alert
                    severity={uploadResult.success ? 'success' : 'error'}
                    sx={{ mt: 2 }}
                    icon={uploadResult.success ? <SuccessIcon /> : <ErrorIcon />}
                  >
                    <Typography variant="body2" fontWeight="bold">
                      {uploadResult.message}
                    </Typography>
                    {uploadResult.success && (
                      <Typography variant="body2">
                        {t('inserted')}: {uploadResult.inserted} | {t('updated')}: {uploadResult.updated}
                      </Typography>
                    )}
                  </Alert>
                )}

                <Button
                  variant="contained"
                  size="large"
                  startIcon={<UploadIcon />}
                  onClick={handleUpload}
                  disabled={selectedFiles.length === 0 || uploadProgress}
                  sx={{ mt: 3 }}
                >
                  {uploadProgress ? t('uploadingData') : t('uploadData')}
                </Button>

                {/* Bulk PDF Processing Section - Only visible when enabled in Super Admin */}
                {systemSettings?.enable_image_upload && (
                  <>
                    {/* Bulk QR Code Upload Section */}
                    <Divider sx={{ my: 4 }} />
                    <Typography variant="h6" gutterBottom fontWeight="bold">
                      <QrCodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      {t('bulkQrCodeUpload') || 'Bulk QR Code Upload'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {t('bulkQrDescription') || 'Upload QR codes in bulk via images (PNG/JPG), PDF files, or ZIP archives. Files will be automatically mapped to debtor accounts by filename.'}
                    </Typography>

                    {/* Completed Job Summary - shows for 5 minutes */}
                    {completedJobSummary && (
                      <Alert
                        severity={completedJobSummary.status === 'completed' ? 'success' : 'error'}
                        sx={{ mb: 3 }}
                        onClose={() => setCompletedJobSummary(null)}
                      >
                        <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                          {completedJobSummary.status === 'completed' ? t('processingComplete') : t('processingFailed')}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                          <Typography variant="body2">
                            <strong>{t('job')}:</strong> {completedJobSummary.job_id}
                          </Typography>
                          <Typography variant="body2">
                            <strong>{t('totalFiles')}:</strong> {completedJobSummary.total_files?.toLocaleString()}
                          </Typography>
                          <Typography variant="body2" color="success.main">
                            <strong>{t('extracted')}:</strong> {completedJobSummary.successful?.toLocaleString()}
                          </Typography>
                          <Typography variant="body2" color="error.main">
                            <strong>{t('failed')}:</strong> {completedJobSummary.failed?.toLocaleString()}
                          </Typography>
                          <Typography variant="body2" color="warning.main">
                            <strong>{t('notFound')}:</strong> {completedJobSummary.not_found?.toLocaleString()}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                          {t('completedAt')}: {completedJobSummary.completed_at} ({t('summaryAutoDismiss')})
                        </Typography>
                      </Alert>
                    )}

                    {/* QR Code Drop Zone */}
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 3,
                        textAlign: 'center',
                        bgcolor: isDraggingPdf
                          ? 'info.light'
                          : pdfFiles.length > 0
                          ? 'success.light'
                          : 'grey.50',
                        border: '2px dashed',
                        borderColor: isDraggingPdf
                          ? 'info.main'
                          : pdfFiles.length > 0
                          ? 'success.main'
                          : 'grey.300',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease-in-out',
                      }}
                      onClick={() => document.getElementById('pdf-input').click()}
                      onDragEnter={handlePdfDragEnter}
                      onDragOver={handlePdfDragOver}
                      onDragLeave={handlePdfDragLeave}
                      onDrop={handlePdfDrop}
                    >
                      <input
                        id="pdf-input"
                        type="file"
                        accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.zip,image/*,application/pdf,application/zip"
                        multiple
                        onChange={handlePdfSelect}
                        style={{ display: 'none' }}
                      />
                      {isDraggingPdf ? (
                        <Box>
                          <QrCodeIcon sx={{ fontSize: 48, color: 'info.main', mb: 1 }} />
                          <Typography variant="body1" fontWeight="bold" color="info.main">
                            {t('dropQrFilesHere') || 'Drop QR files here'}
                          </Typography>
                        </Box>
                      ) : pdfFiles.length > 0 ? (
                        <Box>
                          <QrCodeIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                          <Typography variant="body1" fontWeight="bold">
                            {pdfFiles.length.toLocaleString()} {t('qrFilesSelected') || 'QR files selected'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('readyToUpload') || 'Ready to upload'}
                          </Typography>
                        </Box>
                      ) : (
                        <Box>
                          <QrCodeIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                          <Typography variant="body1" fontWeight="bold">
                            {t('dragDropQrFiles') || 'Drag & drop QR images, PDFs, or ZIP files'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {t('clickToBrowseQr') || 'Or click to browse (PNG, JPG, GIF, WEBP, PDF, ZIP)'}
                          </Typography>
                        </Box>
                      )}
                    </Paper>

                    {pdfStagingProgress && (
                      <Box sx={{ mt: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" fontWeight="bold">
                            {qrUploadInfo.message || (t('uploadingBatch') || 'Uploading batch') + ` ${pdfStagingInfo.current} ${t('of')} ${pdfStagingInfo.total}`}
                          </Typography>
                          <Typography variant="body2" color="info.main">
                            {qrUploadInfo.uploaded > 0 && `${qrUploadInfo.uploaded.toLocaleString()} uploaded`}
                            {qrUploadInfo.not_found > 0 && `, ${qrUploadInfo.not_found} not found`}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={qrUploadInfo.percentage || (pdfStagingInfo.total > 0 ? (pdfStagingInfo.current / pdfStagingInfo.total) * 100 : 0)}
                          sx={{ height: 10, borderRadius: 5 }}
                          color="info"
                        />
                        {qrUploadInfo.total_images > 0 && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                            Processing: {qrUploadInfo.processed_images?.toLocaleString() || 0} of {qrUploadInfo.total_images?.toLocaleString()} images ({qrUploadInfo.percentage}%)
                          </Typography>
                        )}
                      </Box>
                    )}

                    <Button
                      variant="contained"
                      size="large"
                      startIcon={<UploadIcon />}
                      onClick={handleStagePdfs}
                      disabled={pdfFiles.length === 0 || pdfStagingProgress}
                      sx={{ mt: 2 }}
                      color="info"
                    >
                      {pdfStagingProgress
                        ? `${t('uploadingBatchProgress') || 'Uploading'} ${pdfStagingInfo.current}/${pdfStagingInfo.total}...`
                        : `${t('uploadQrCodes') || 'Upload QR Codes'} (${pdfFiles.length.toLocaleString()})`}
                    </Button>

                    {/* Processing Jobs Table */}
                    {pdfJobs.length > 0 && (
                      <Box sx={{ mt: 4 }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          {t('processingJobs')}
                        </Typography>
                        <TableContainer component={Paper} variant="outlined">
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>{t('jobId')}</TableCell>
                                <TableCell>{t('status')}</TableCell>
                                <TableCell>{t('progress')}</TableCell>
                                <TableCell>{t('results')}</TableCell>
                                <TableCell>{t('action')}</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {pdfJobs.map((job) => (
                                <TableRow key={job.job_id}>
                                  <TableCell>
                                    <Typography variant="caption" fontFamily="monospace">
                                      {job.job_id}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    <Chip
                                      label={job.status}
                                      size="small"
                                      color={
                                        job.status === 'completed'
                                          ? 'success'
                                          : job.status === 'processing'
                                          ? 'warning'
                                          : job.status === 'failed'
                                          ? 'error'
                                          : 'default'
                                      }
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      <LinearProgress
                                        variant="determinate"
                                        value={job.percentage || 0}
                                        sx={{ width: 100, height: 8, borderRadius: 4 }}
                                      />
                                      <Typography variant="caption">
                                        {job.percentage || 0}%
                                      </Typography>
                                    </Box>
                                    <Typography variant="caption" color="text.secondary">
                                      {job.processed}/{job.total_files} {t('files')}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="caption" color="success.main">
                                      {job.successful} {t('extracted')}
                                    </Typography>
                                    <br />
                                    <Typography variant="caption" color="error.main">
                                      {job.failed} {t('failed')}, {job.not_found} {t('notFound')}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    {job.status === 'staging' && (
                                      <Chip label={t('uploading')} size="small" color="info" />
                                    )}
                                    {job.status === 'staged' && (
                                      <Button
                                        size="small"
                                        variant="contained"
                                        color="primary"
                                        onClick={() => handleStartProcessing(job.job_id)}
                                      >
                                        {t('start')}
                                      </Button>
                                    )}
                                    {job.status === 'processing' && (
                                      <CircularProgress size={20} />
                                    )}
                                    {job.status === 'completed' && (
                                      <SuccessIcon color="success" />
                                    )}
                                    {job.status === 'failed' && (
                                      <ErrorIcon color="error" />
                                    )}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Box>
                    )}
                  </>
                )}
              </Box>
            )}

            {/* View Accounts Tab */}
            {effectiveTabValue === 'view_accounts' && (
              <Box>
                {/* Header with title and search */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={2}>
                  <Typography variant="h6" fontWeight="bold">
                    {t('debtorAccounts')} ({pagination.totalCount.toLocaleString()})
                  </Typography>
                  <Box display="flex" gap={2} alignItems="center">
                    <TextField
                      size="small"
                      placeholder="Search by name, account, ID, case..."
                      value={searchInput}
                      onChange={handleSearchChange}
                      sx={{ minWidth: 300 }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <SearchIcon color="action" />
                          </InputAdornment>
                        ),
                        endAdornment: searchInput && (
                          <InputAdornment position="end">
                            <IconButton size="small" onClick={handleClearSearch}>
                              <ClearIcon />
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                    <Button startIcon={<RefreshIcon />} onClick={() => fetchDebtors()} disabled={loading}>
                      {t('refresh')}
                    </Button>
                  </Box>
                </Box>

                {loading && <LinearProgress sx={{ mb: 2 }} />}

                {/* DataGrid with virtual scrolling */}
                <Paper variant="outlined" sx={{ height: 600, width: '100%' }}>
                  <DataGrid
                    rows={debtors}
                    getRowId={(row) => row.account_number}
                    columns={[
                      ...(systemSettings?.table_columns?.view_accounts?.case_id !== false ? [{
                        field: 'case_id',
                        headerName: t('caseId'),
                        width: 130,
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold" color="secondary.main">
                            {params.value || '-'}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.upload_id !== false ? [{
                        field: 'upload_id',
                        headerName: t('uploadId'),
                        width: 160,
                        renderCell: (params) => (
                          <Typography variant="body2" color="primary.main">
                            {params.value || '-'}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.account_number !== false ? [{
                        field: 'account_number',
                        headerName: t('accountNumber'),
                        width: 140,
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold">
                            {params.value}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.national_id !== false ? [{
                        field: 'national_id',
                        headerName: t('nationalId'),
                        width: 140,
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.name !== false ? [{
                        field: 'name',
                        headerName: t('name'),
                        width: 180,
                        flex: 1,
                        renderCell: (params) => (
                          <Typography variant="body2" noWrap title={params.value}>
                            {params.value}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.debt_type !== false ? [{
                        field: 'debt_type',
                        headerName: t('debtType'),
                        width: 120,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => <Chip label={params.value} size="small" />,
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.loan_contract_date !== false ? [{
                        field: 'loan_contract_date',
                        headerName: t('loanContractDate'),
                        width: 140,
                        renderCell: (params) => (
                          <Typography variant="body2">
                            {formatDateOnly(params.value)}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.outstanding_balance !== false ? [{
                        field: 'outstanding_balance',
                        headerName: t('outstandingBalance'),
                        width: 150,
                        type: 'number',
                        headerAlign: 'right',
                        align: 'right',
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold" color="error.main">
                            {formatCurrency(params.value)}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.created_at !== false ? [{
                        field: 'created_at',
                        headerName: t('createdAt'),
                        width: 150,
                        renderCell: (params) => (
                          <Typography variant="body2" color="text.secondary">
                            {params.value ? formatDateTime(params.value) : '-'}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.view_accounts?.updated_at !== false ? [{
                        field: 'updated_at',
                        headerName: t('updatedAt'),
                        width: 150,
                        renderCell: (params) => (
                          <Typography variant="body2" color="text.secondary">
                            {params.value ? formatDateTime(params.value) : '-'}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.enable_image_upload && systemSettings?.table_columns?.view_accounts?.qr_code !== false
                        ? [
                            {
                              field: 'qr_code',
                              headerName: t('qrCodeColumn'),
                              width: 90,
                              headerAlign: 'center',
                              align: 'center',
                              sortable: false,
                              renderCell: (params) => {
                                const hasImage = debtorImages[params.row.account_number];
                                return hasImage ? (
                                  <Avatar
                                    variant="rounded"
                                    sx={{ width: 36, height: 36, bgcolor: 'primary.light' }}
                                  >
                                    <QrCodeIcon sx={{ color: 'primary.main', fontSize: 20 }} />
                                  </Avatar>
                                ) : (
                                  <Avatar variant="rounded" sx={{ width: 36, height: 36, bgcolor: 'grey.200' }}>
                                    <ImageIcon sx={{ color: 'grey.400', fontSize: 20 }} />
                                  </Avatar>
                                );
                              },
                            },
                          ]
                        : []),
                      ...(systemSettings?.table_actions?.view_accounts !== false
                        ? [
                            {
                              field: 'actions',
                              headerName: t('actions'),
                              width: 100,
                              headerAlign: 'center',
                              align: 'center',
                              sortable: false,
                              renderCell: (params) => (
                                <Box>
                                  <IconButton size="small" onClick={() => setViewDialog({ open: true, debtor: params.row })}>
                                    <ViewIcon />
                                  </IconButton>
                                  <IconButton size="small" color="error" onClick={() => setDeleteDialog({ open: true, debtor: params.row })}>
                                    <DeleteIcon />
                                  </IconButton>
                                </Box>
                              ),
                            },
                          ]
                        : []),
                    ]}
                    loading={loading}
                    disableRowSelectionOnClick
                    sortingMode="server"
                    sortModel={sortModel}
                    onSortModelChange={handleSortModelChange}
                    hideFooter
                    sx={{
                      '& .MuiDataGrid-row:hover': { backgroundColor: 'action.hover' },
                      '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
                      '& .MuiDataGrid-columnHeader': { backgroundColor: 'grey.50' },
                    }}
                    localeText={{
                      noRowsLabel: t('noDebtorAccounts'),
                    }}
                  />
                </Paper>

                {/* Pagination */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mt={2}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="body2" color="text.secondary">
                      Showing {debtors.length} of {pagination.totalCount.toLocaleString()} records
                      {searchQuery && ` (filtered by "${searchQuery}")`}
                    </Typography>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <InputLabel>Rows per page</InputLabel>
                      <Select
                        value={pagination.pageSize}
                        label="Rows per page"
                        onChange={(e) => {
                          setPagination(prev => ({ ...prev, page: 1, pageSize: e.target.value }));
                        }}
                      >
                        <MenuItem value={10}>10</MenuItem>
                        <MenuItem value={25}>25</MenuItem>
                        <MenuItem value={50}>50</MenuItem>
                        <MenuItem value={100}>100</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                  <Pagination
                    count={pagination.totalPages}
                    page={pagination.page}
                    onChange={handlePageChange}
                    color="primary"
                    showFirstButton
                    showLastButton
                    disabled={loading}
                  />
                </Box>
              </Box>
            )}

            {/* Debtor Payments and Requests Tab */}
            {effectiveTabValue === 'debtor_requests' && (
              <Box>
                {/* Header with filters */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={2}>
                  <Typography variant="h6" fontWeight="bold">
                    {t('debtorPaymentsAndRequests')} ({getFilteredRequests().length})
                  </Typography>
                  <Box display="flex" gap={2} alignItems="center">
                    {(systemSettings?.admin_filters?.type_filter !== false) && (
                      <FormControl size="small" sx={{ minWidth: 180 }}>
                        <InputLabel>{t('filterByType')}</InputLabel>
                        <Select
                          value={requestTypeFilter}
                          label={t('filterByType')}
                          onChange={(e) => setRequestTypeFilter(e.target.value)}
                        >
                          <MenuItem value="all">{t('allRequests')}</MenuItem>
                          <MenuItem value="payment_submitted">{t('paymentSubmitted')}</MenuItem>
                          <MenuItem value="not_ready_to_pay">{t('notReadyRequests')}</MenuItem>
                        </Select>
                      </FormControl>
                    )}
                    {(systemSettings?.admin_filters?.status_filter !== false) && (
                      <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>{t('filterByStatus')}</InputLabel>
                        <Select
                          value={requestStatusFilter}
                          label={t('filterByStatus')}
                          onChange={(e) => setRequestStatusFilter(e.target.value)}
                        >
                          <MenuItem value="all">{t('all')}</MenuItem>
                          <MenuItem value="unread">{t('unread')}</MenuItem>
                          <MenuItem value="read">{t('read')}</MenuItem>
                        </Select>
                      </FormControl>
                    )}
                    <Button startIcon={<RefreshIcon />} onClick={fetchNotifications} disabled={loading}>
                      {t('refresh')}
                    </Button>
                  </Box>
                </Box>

                {/* DataGrid */}
                <Paper variant="outlined" sx={{ height: 500, width: '100%' }}>
                  <DataGrid
                    rows={getFilteredRequests()}
                    getRowId={(row) => row._id}
                    columns={[
                      ...(systemSettings?.table_columns?.debtor_requests?.type !== false ? [{
                        field: 'type',
                        headerName: t('requestType'),
                        width: 170,
                        renderCell: (params) => {
                          const isPayment = params.value === 'payment_submitted' || params.value === 'payment_request';
                          return (
                            <Chip
                              icon={isPayment ? <PaymentIcon /> : <WarningIcon />}
                              label={isPayment ? t('paymentSubmitted') : t('notReadyToPay')}
                              size="small"
                              color={isPayment ? 'success' : 'warning'}
                            />
                          );
                        },
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.debtor_name !== false ? [{
                        field: 'debtor_name',
                        headerName: t('debtorName'),
                        width: 150,
                        flex: 1,
                        valueGetter: (value, row) => row.debtor?.name || '-',
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold">
                            {params.value}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.account_number !== false ? [{
                        field: 'account_number',
                        headerName: t('accountNumber'),
                        width: 140,
                        valueGetter: (value, row) => row.debtor?.account_number || '-',
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.outstanding_balance !== false ? [{
                        field: 'outstanding_balance',
                        headerName: t('outstandingBalance'),
                        width: 140,
                        type: 'number',
                        valueGetter: (value, row) => row.debtor?.outstanding_balance || 0,
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold" color="error.main">
                            {formatCurrency(params.value)}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.payment_amount !== false ? [{
                        field: 'payment_amount',
                        headerName: t('paymentAmount') || 'Payment Amount',
                        width: 130,
                        valueGetter: (value, row) => row.metadata?.payment_amount || 0,
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            {params.value ? formatCurrency(params.value) : '-'}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.transaction_number !== false ? [{
                        field: 'transaction_number',
                        headerName: t('transactionNumber') || 'Transaction #',
                        width: 150,
                        valueGetter: (value, row) => row.metadata?.transaction_number || '-',
                        renderCell: (params) => (
                          <Typography
                            variant="body2"
                            fontWeight="medium"
                            color="primary.main"
                            sx={{ fontFamily: 'monospace' }}
                          >
                            {params.value}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.receipt !== false ? [{
                        field: 'receipt',
                        headerName: t('receipt') || 'Receipt',
                        width: 100,
                        headerAlign: 'center',
                        align: 'center',
                        sortable: false,
                        valueGetter: (value, row) => row.metadata?.receipt_filename || null,
                        renderCell: (params) => (
                          params.value ? (
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<ViewIcon />}
                              onClick={() => handleViewReceipt(params.value)}
                              sx={{ textTransform: 'none', fontSize: '0.75rem' }}
                            >
                              View
                            </Button>
                          ) : (
                            <Typography variant="body2" color="text.disabled">-</Typography>
                          )
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.message !== false ? [{
                        field: 'message',
                        headerName: t('message'),
                        width: 180,
                        flex: 1,
                        renderCell: (params) => (
                          <Typography
                            variant="body2"
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                            title={params.value}
                          >
                            {params.value}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.created_at !== false ? [{
                        field: 'created_at',
                        headerName: t('receivedAt'),
                        width: 160,
                        renderCell: (params) => (
                          <Typography variant="body2" color="text.secondary">
                            {formatDateTime(params.value)}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.debtor_requests?.read !== false ? [{
                        field: 'read',
                        headerName: t('status'),
                        width: 100,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => (
                          <Chip
                            label={params.value ? t('read') : t('unread')}
                            size="small"
                            color={params.value ? 'default' : 'primary'}
                            variant={params.value ? 'outlined' : 'filled'}
                          />
                        ),
                      }] : []),
                      ...(systemSettings?.table_actions?.debtor_requests !== false
                        ? [
                            {
                              field: 'actions',
                              headerName: t('actions'),
                              width: 100,
                              headerAlign: 'center',
                              align: 'center',
                              sortable: false,
                              renderCell: (params) => (
                                <Box>
                                  <IconButton
                                    size="small"
                                    onClick={() => setRequestDetailsDialog({ open: true, request: params.row })}
                                    title={t('viewDetails')}
                                  >
                                    <ViewIcon />
                                  </IconButton>
                                  {!params.row.read && (
                                    <IconButton
                                      size="small"
                                      onClick={() => handleMarkAsRead(params.row._id)}
                                      title={t('markAllRead')}
                                    >
                                      <MarkReadIcon />
                                    </IconButton>
                                  )}
                                </Box>
                              ),
                            },
                          ]
                        : []),
                    ]}
                    loading={loading}
                    disableRowSelectionOnClick
                    pageSizeOptions={[10, 25, 50, 100]}
                    initialState={{
                      pagination: { paginationModel: { pageSize: 25 } },
                    }}
                    getRowClassName={(params) => (params.row.read ? '' : 'unread-row')}
                    sx={{
                      '& .MuiDataGrid-row:hover': { backgroundColor: 'action.hover' },
                      '& .unread-row': { backgroundColor: 'action.selected' },
                      '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
                      '& .MuiDataGrid-columnHeader': { backgroundColor: 'grey.50' },
                    }}
                    localeText={{
                      noRowsLabel: t('noDebtorRequests'),
                    }}
                  />
                </Paper>
              </Box>
            )}

            {/* Upload History Tab */}
            {effectiveTabValue === 'upload_history' && (
              <Box>
                {/* Header */}
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" fontWeight="bold">
                    {t('uploadHistory')} ({uploadHistory.length})
                  </Typography>
                  <Button startIcon={<RefreshIcon />} onClick={fetchUploadHistory} disabled={loading}>
                    {t('refresh')}
                  </Button>
                </Box>

                {/* DataGrid */}
                <Paper variant="outlined" sx={{ height: 500, width: '100%' }}>
                  <DataGrid
                    rows={uploadHistory}
                    getRowId={(row) => row._id || row.upload_id}
                    columns={[
                      ...(systemSettings?.table_columns?.upload_history?.upload_id !== false ? [{
                        field: 'upload_id',
                        headerName: t('uploadId'),
                        width: 160,
                        renderCell: (params) => (
                          <Typography variant="body2" fontWeight="bold" color="primary.main">
                            {params.value || '-'}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.uploaded_at !== false ? [{
                        field: 'uploaded_at',
                        headerName: t('dateTime'),
                        width: 160,
                        renderCell: (params) => (
                          <Typography variant="body2">
                            {formatDateTime(params.value)}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.filename !== false ? [{
                        field: 'filename',
                        headerName: t('filename'),
                        width: 200,
                        flex: 1,
                        renderCell: (params) => (
                          <Box display="flex" alignItems="center" gap={1}>
                            <FileIcon color="primary" fontSize="small" />
                            <Typography variant="body2" fontWeight="medium" noWrap title={params.value}>
                              {params.value}
                            </Typography>
                          </Box>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.file_size !== false ? [{
                        field: 'file_size',
                        headerName: t('fileSize'),
                        width: 100,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => (
                          <Typography variant="body2">
                            {formatFileSize(params.value)}
                          </Typography>
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.total_records !== false ? [{
                        field: 'total_records',
                        headerName: t('totalRecords'),
                        width: 100,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => (
                          <Chip label={params.value} size="small" color="primary" variant="outlined" />
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.inserted_count !== false ? [{
                        field: 'inserted_count',
                        headerName: t('inserted'),
                        width: 90,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => (
                          <Chip label={params.value} size="small" color="success" />
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.updated_count !== false ? [{
                        field: 'updated_count',
                        headerName: t('updated'),
                        width: 90,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => (
                          <Chip label={params.value} size="small" color="info" />
                        ),
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.uploaded_by !== false ? [{
                        field: 'uploaded_by',
                        headerName: t('uploadedBy'),
                        width: 120,
                      }] : []),
                      ...(systemSettings?.table_columns?.upload_history?.status !== false ? [{
                        field: 'status',
                        headerName: t('status'),
                        width: 110,
                        headerAlign: 'center',
                        align: 'center',
                        renderCell: (params) => (
                          <Chip
                            label={params.value}
                            size="small"
                            color={params.value === 'success' ? 'success' : 'error'}
                            icon={params.value === 'success' ? <SuccessIcon /> : <ErrorIcon />}
                          />
                        ),
                      }] : []),
                      ...(systemSettings?.table_actions?.upload_history !== false
                        ? [
                            {
                              field: 'actions',
                              headerName: t('actions'),
                              width: 80,
                              headerAlign: 'center',
                              align: 'center',
                              sortable: false,
                              renderCell: (params) => (
                                <IconButton
                                  size="small"
                                  color="primary"
                                  onClick={() => handleDownloadFile(params.row._id, params.row.filename)}
                                  title={t('downloadFile')}
                                >
                                  <DownloadIcon />
                                </IconButton>
                              ),
                            },
                          ]
                        : []),
                    ]}
                    loading={loading}
                    disableRowSelectionOnClick
                    pageSizeOptions={[10, 25, 50, 100]}
                    initialState={{
                      pagination: { paginationModel: { pageSize: 25 } },
                    }}
                    sx={{
                      '& .MuiDataGrid-row:hover': { backgroundColor: 'action.hover' },
                      '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
                      '& .MuiDataGrid-columnHeader': { backgroundColor: 'grey.50' },
                    }}
                    localeText={{
                      noRowsLabel: t('noUploadHistory'),
                    }}
                  />
                </Paper>
              </Box>
            )}

            {/* Settings Tab */}
            {effectiveTabValue === 'settings' && (
              <Box>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  {t('settings')}
                </Typography>

                {/* LINE QR Code Section */}
                <Paper variant="outlined" sx={{ p: 3, mt: 3 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <QrCodeIcon color="primary" />
                    <Typography variant="subtitle1" fontWeight="bold">
                      {t('lineQrCodeSettings')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {t('lineQrCodeDescription')}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  {/* Current QR Code Display */}
                  {qrCode && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        {t('currentQrCode')}:
                      </Typography>
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          p: 2,
                          bgcolor: 'grey.50',
                          borderRadius: 2,
                          border: '1px solid',
                          borderColor: 'grey.200',
                        }}
                      >
                        <img
                          src={`data:image/png;base64,${qrCode}`}
                          alt="LINE QR Code"
                          style={{
                            maxWidth: '200px',
                            maxHeight: '200px',
                            borderRadius: '8px',
                          }}
                        />
                        <Button
                          variant="outlined"
                          color="error"
                          size="small"
                          startIcon={<DeleteIcon />}
                          onClick={handleQrCodeDelete}
                          sx={{ mt: 2 }}
                        >
                          {t('deleteQrCode')}
                        </Button>
                      </Box>
                    </Box>
                  )}

                  {/* Upload New QR Code */}
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      {qrCode ? t('replaceQrCode') : t('uploadQrCode')}:
                    </Typography>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 3,
                        textAlign: 'center',
                        bgcolor: qrCodeFile ? 'success.light' : 'grey.50',
                        border: '2px dashed',
                        borderColor: qrCodeFile ? 'success.main' : 'grey.300',
                        cursor: 'pointer',
                      }}
                      onClick={() => document.getElementById('qr-code-input').click()}
                    >
                      <input
                        id="qr-code-input"
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/gif,image/webp,image/bmp"
                        onChange={handleQrCodeSelect}
                        style={{ display: 'none' }}
                      />
                      {qrCodeFile ? (
                        <Box>
                          <ImageIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                          <Typography variant="body1" fontWeight="bold">
                            {qrCodeFile.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {(qrCodeFile.size / 1024).toFixed(2)} KB
                          </Typography>
                        </Box>
                      ) : (
                        <Box>
                          <QrCodeIcon sx={{ fontSize: 40, color: 'grey.400', mb: 1 }} />
                          <Typography variant="body1">
                            {t('clickToSelectQr')}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {t('supportedFormats')}: PNG, JPG, GIF, WEBP
                          </Typography>
                        </Box>
                      )}
                    </Paper>

                    {qrCodeUploading && <LinearProgress sx={{ mt: 2 }} />}

                    <Button
                      variant="contained"
                      startIcon={<UploadIcon />}
                      onClick={handleQrCodeUpload}
                      disabled={!qrCodeFile || qrCodeUploading}
                      sx={{ mt: 2 }}
                    >
                      {qrCodeUploading ? t('uploadingData') : t('uploadQrCode')}
                    </Button>
                  </Box>
                </Paper>

                {/* Bank Account Settings Section */}
                <Paper variant="outlined" sx={{ p: 3, mt: 3 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <BankIcon color="primary" />
                    <Typography variant="subtitle1" fontWeight="bold">
                      {t('bankAccountSettings')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {t('bankAccountSettingsDescription')}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  {bankSettingsMessage && (
                    <Alert
                      severity={bankSettingsMessage.type}
                      sx={{ mb: 2 }}
                      onClose={() => setBankSettingsMessage(null)}
                    >
                      {bankSettingsMessage.text}
                    </Alert>
                  )}

                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label={t('bankName')}
                        value={bankSettings.bank_name}
                        onChange={handleBankSettingChange('bank_name')}
                        placeholder={t('bankNamePlaceholder')}
                        helperText={t('bankNameHelper')}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label={t('accountName')}
                        value={bankSettings.account_name}
                        onChange={handleBankSettingChange('account_name')}
                        placeholder={t('accountNamePlaceholder')}
                        helperText={t('accountNameHelper')}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label={t('accountNumber')}
                        value={bankSettings.account_number}
                        onChange={handleBankSettingChange('account_number')}
                        placeholder={t('accountNumberPlaceholder')}
                        helperText={t('accountNumberHelper')}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label={t('promptPayId')}
                        value={bankSettings.promptpay_id}
                        onChange={handleBankSettingChange('promptpay_id')}
                        placeholder={t('promptPayIdPlaceholder')}
                        helperText={t('promptPayIdHelper')}
                      />
                    </Grid>
                  </Grid>

                  <Box display="flex" justifyContent="flex-end" mt={3}>
                    <Button
                      variant="contained"
                      startIcon={bankSettingsSaving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                      onClick={handleSaveBankSettings}
                      disabled={bankSettingsSaving}
                    >
                      {bankSettingsSaving ? t('saving') : t('saveBankSettings')}
                    </Button>
                  </Box>
                </Paper>

                {/* Change Password Section */}
                <Paper variant="outlined" sx={{ p: 3, mt: 3 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={2}>
                    <LockIcon color="primary" />
                    <Typography variant="subtitle1" fontWeight="bold">
                      {t('changePassword')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {t('changePasswordDescription')}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  {passwordMessage && (
                    <Alert
                      severity={passwordMessage.type}
                      sx={{ mb: 2 }}
                      onClose={() => setPasswordMessage(null)}
                    >
                      {passwordMessage.text}
                    </Alert>
                  )}

                  <Grid container spacing={2}>
                    <Grid size={{ xs: 12 }}>
                      <TextField
                        fullWidth
                        label={t('currentPassword')}
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                                edge="end"
                              >
                                {showCurrentPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label={t('newPassword')}
                        type={showNewPassword ? 'text' : 'password'}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        helperText={t('passwordMinLengthHint')}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowNewPassword(!showNewPassword)}
                                edge="end"
                              >
                                {showNewPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    </Grid>
                    <Grid size={{ xs: 12, md: 6 }}>
                      <TextField
                        fullWidth
                        label={t('confirmNewPassword')}
                        type={showNewPassword ? 'text' : 'password'}
                        value={confirmNewPassword}
                        onChange={(e) => setConfirmNewPassword(e.target.value)}
                        error={confirmNewPassword && newPassword !== confirmNewPassword}
                        helperText={confirmNewPassword && newPassword !== confirmNewPassword ? t('passwordsDoNotMatch') : ''}
                      />
                    </Grid>
                  </Grid>

                  <Box display="flex" justifyContent="flex-end" mt={3}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={passwordChanging ? <CircularProgress size={20} color="inherit" /> : <LockIcon />}
                      onClick={handleChangePassword}
                      disabled={passwordChanging || !currentPassword || !newPassword || !confirmNewPassword}
                    >
                      {passwordChanging ? t('changingPassword') : t('changePassword')}
                    </Button>
                  </Box>
                </Paper>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* View Dialog */}
      <Dialog open={viewDialog.open} onClose={() => setViewDialog({ open: false, debtor: null })} maxWidth="sm" fullWidth>
        <DialogTitle>{t('debtorDetails')}</DialogTitle>
        <DialogContent>
          {viewDialog.debtor && (
            <Box sx={{ pt: 2 }}>
              {/* Debtor QR Code Image */}
              {systemSettings?.enable_image_upload && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                  {dialogImageLoading ? (
                    <Skeleton variant="rounded" width={150} height={150} />
                  ) : dialogImage ? (
                    <Box
                      component="img"
                      src={`data:${dialogImage.content_type};base64,${dialogImage.data}`}
                      alt={viewDialog.debtor.name}
                      sx={{
                        width: 150,
                        height: 150,
                        objectFit: 'cover',
                        borderRadius: 2,
                        boxShadow: 2,
                      }}
                    />
                  ) : (
                    <Avatar
                      variant="rounded"
                      sx={{ width: 150, height: 150, bgcolor: 'grey.200' }}
                    >
                      <ImageIcon sx={{ fontSize: 60, color: 'grey.400' }} />
                    </Avatar>
                  )}
                </Box>
              )}

              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('accountInformation')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('caseId')}</Typography>
                    <Typography variant="body1" fontWeight="bold" color="secondary.main">{viewDialog.debtor.case_id || '-'}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('uploadId')}</Typography>
                    <Typography variant="body1" fontWeight="bold" color="primary.main">{viewDialog.debtor.upload_id || '-'}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('accountNumber')}</Typography>
                    <Typography variant="body1" fontWeight="bold">{viewDialog.debtor.account_number}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('nationalId')}</Typography>
                    <Typography variant="body1" fontWeight="bold">{viewDialog.debtor.national_id}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('originalCreditor')}</Typography>
                    <Typography variant="body1">{viewDialog.debtor.original_creditor}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('outstandingBalance')}</Typography>
                    <Typography variant="body1" fontWeight="bold" color="error.main">
                      {formatCurrency(viewDialog.debtor.outstanding_balance)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('debtType')}</Typography>
                    <Typography variant="body1">{viewDialog.debtor.debt_type}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('loanContractDate')}</Typography>
                    <Typography variant="body1">{viewDialog.debtor.loan_contract_date || '-'}</Typography>
                  </Box>
                </Box>
              </Paper>

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('contactInformation')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('name')}</Typography>
                    <Typography variant="body1" fontWeight="bold">{viewDialog.debtor.name}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('phoneNumber')}</Typography>
                    <Typography variant="body1">{viewDialog.debtor.phone}</Typography>
                  </Box>
                  <Box gridColumn="span 2">
                    <Typography variant="caption" color="text.secondary">{t('emailAddress')}</Typography>
                    <Typography variant="body1">{viewDialog.debtor.email}</Typography>
                  </Box>
                </Box>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialog({ open: false, debtor: null })}>{t('close')}</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, debtor: null })}>
        <DialogTitle>{t('confirmDelete')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('confirmDeleteMessage')}{' '}
            <strong>{deleteDialog.debtor?.name}</strong> ({deleteDialog.debtor?.account_number})?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t('actionCannotBeUndone')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, debtor: null })}>{t('cancel')}</Button>
          <Button variant="contained" color="error" onClick={handleDeleteDebtor}>
            {t('delete')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Request Details Dialog */}
      <Dialog
        open={requestDetailsDialog.open}
        onClose={() => setRequestDetailsDialog({ open: false, request: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            {(requestDetailsDialog.request?.type === 'payment_submitted' || requestDetailsDialog.request?.type === 'payment_request') ? (
              <PaymentIcon color="success" />
            ) : (
              <WarningIcon color="warning" />
            )}
            {t('requestDetails')}
          </Box>
        </DialogTitle>
        <DialogContent>
          {requestDetailsDialog.request && (
            <Box sx={{ pt: 2 }}>
              {/* Request Type Badge */}
              <Box mb={3}>
                <Chip
                  icon={(requestDetailsDialog.request.type === 'payment_submitted' || requestDetailsDialog.request.type === 'payment_request') ? <PaymentIcon /> : <WarningIcon />}
                  label={(requestDetailsDialog.request.type === 'payment_submitted' || requestDetailsDialog.request.type === 'payment_request') ? t('paymentSubmitted') : t('notReadyToPay')}
                  color={(requestDetailsDialog.request.type === 'payment_submitted' || requestDetailsDialog.request.type === 'payment_request') ? 'success' : 'warning'}
                />
                <Chip
                  label={requestDetailsDialog.request.read ? t('read') : t('unread')}
                  size="small"
                  color={requestDetailsDialog.request.read ? 'default' : 'primary'}
                  variant={requestDetailsDialog.request.read ? 'outlined' : 'filled'}
                  sx={{ ml: 1 }}
                />
              </Box>

              {/* Debtor Information */}
              <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('debtorInfo')}
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('name')}</Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {requestDetailsDialog.request.debtor?.name || '-'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('accountNumber')}</Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {requestDetailsDialog.request.debtor?.account_number || '-'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('phoneNumber')}</Typography>
                    <Typography variant="body1">
                      {requestDetailsDialog.request.debtor?.phone || '-'}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">{t('emailAddress')}</Typography>
                    <Typography variant="body1">
                      {requestDetailsDialog.request.debtor?.email || '-'}
                    </Typography>
                  </Box>
                  <Box gridColumn="span 2">
                    <Typography variant="caption" color="text.secondary">{t('outstandingBalance')}</Typography>
                    <Typography variant="body1" fontWeight="bold" color="error.main">
                      {formatCurrency(requestDetailsDialog.request.debtor?.outstanding_balance)}
                    </Typography>
                  </Box>
                </Box>
              </Paper>

              {/* Request Information */}
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('requestInfo')}
                </Typography>
                <Divider sx={{ mb: 2 }} />

                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary">{t('message')}</Typography>
                  <Typography variant="body1">
                    {requestDetailsDialog.request.message}
                  </Typography>
                </Box>

                {/* Payment Submitted specific fields */}
                {(requestDetailsDialog.request.type === 'payment_submitted' || requestDetailsDialog.request.type === 'payment_request') && requestDetailsDialog.request.metadata && (
                  <>
                    <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">{t('paymentType') || 'Payment Type'}</Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {requestDetailsDialog.request.metadata.payment_type || '-'}
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">{t('paymentAmount') || 'Payment Amount'}</Typography>
                        <Typography variant="body1" fontWeight="bold" color="success.main">
                          {formatCurrency(requestDetailsDialog.request.metadata.payment_amount)}
                        </Typography>
                      </Box>
                    </Box>
                    {requestDetailsDialog.request.metadata.transaction_number && (
                      <Box mb={2}>
                        <Typography variant="caption" color="text.secondary">{t('transactionNumber') || 'Transaction Number'}</Typography>
                        <Typography variant="body1" fontWeight="bold" color="primary.main" sx={{ fontFamily: 'monospace' }}>
                          {requestDetailsDialog.request.metadata.transaction_number}
                        </Typography>
                      </Box>
                    )}
                    {requestDetailsDialog.request.metadata.receipt_filename && (
                      <Box mb={2}>
                        <Typography variant="caption" color="text.secondary">{t('paymentReceipt')}</Typography>
                        <Box mt={1}>
                          <Button
                            variant="outlined"
                            startIcon={<ViewIcon />}
                            onClick={() => handleViewReceipt(requestDetailsDialog.request.metadata.receipt_filename)}
                            size="small"
                          >
                            {t('viewReceipt')}
                          </Button>
                        </Box>
                      </Box>
                    )}

                    {/* Consent Information */}
                    <Box mb={2} sx={{ p: 2, bgcolor: 'success.50', borderRadius: 1, border: '1px solid', borderColor: 'success.200' }}>
                      <Typography variant="subtitle2" fontWeight="bold" color="success.main" gutterBottom>
                        {t('consentInformation')}
                      </Typography>
                      <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">{t('paymentTermsConsent')}</Typography>
                          <Typography variant="body2" fontWeight="500" color={requestDetailsDialog.request.metadata.payment_terms_consent ? 'success.main' : 'error.main'}>
                            {requestDetailsDialog.request.metadata.payment_terms_consent ? t('yes') : t('no')}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">{t('digitalReceiptConsent')}</Typography>
                          <Typography variant="body2" fontWeight="500" color={requestDetailsDialog.request.metadata.digital_receipt_consent ? 'success.main' : 'error.main'}>
                            {requestDetailsDialog.request.metadata.digital_receipt_consent ? t('yes') : t('no')}
                          </Typography>
                        </Box>
                        {requestDetailsDialog.request.metadata.payment_terms_consent_date && (
                          <Box gridColumn="span 2">
                            <Typography variant="caption" color="text.secondary">{t('consentDate')}</Typography>
                            <Typography variant="body2">
                              {formatDateTime(requestDetailsDialog.request.metadata.payment_terms_consent_date)}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </Box>
                  </>
                )}

                {/* Not Ready to Pay specific fields */}
                {requestDetailsDialog.request.type === 'not_ready_to_pay' && requestDetailsDialog.request.metadata && (
                  <>
                    <Box mb={2}>
                      <Typography variant="caption" color="text.secondary">{t('reason')}</Typography>
                      <Typography variant="body1">
                        {requestDetailsDialog.request.metadata.reason || '-'}
                      </Typography>
                    </Box>
                    {requestDetailsDialog.request.metadata.notes && (
                      <Box mb={2}>
                        <Typography variant="caption" color="text.secondary">{t('notes')}</Typography>
                        <Typography variant="body1">
                          {requestDetailsDialog.request.metadata.notes}
                        </Typography>
                      </Box>
                    )}

                    {/* Contact Preferences */}
                    {(requestDetailsDialog.request.metadata.preferred_contact_date ||
                      requestDetailsDialog.request.metadata.preferred_contact_time ||
                      requestDetailsDialog.request.metadata.preferred_contact_method) && (
                      <Box mb={2} sx={{ p: 2, bgcolor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.200' }}>
                        <Typography variant="subtitle2" fontWeight="bold" color="info.main" gutterBottom>
                          {t('contactPreferences')}
                        </Typography>
                        <Box display="grid" gridTemplateColumns="1fr 1fr 1fr" gap={2}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">{t('preferredDate')}</Typography>
                            <Typography variant="body2" fontWeight="500">
                              {requestDetailsDialog.request.metadata.preferred_contact_date || '-'}
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">{t('preferredTime')}</Typography>
                            <Typography variant="body2" fontWeight="500">
                              {requestDetailsDialog.request.metadata.preferred_contact_time === 'morning' ? t('timeMorning') :
                               requestDetailsDialog.request.metadata.preferred_contact_time === 'afternoon' ? t('timeAfternoon') :
                               requestDetailsDialog.request.metadata.preferred_contact_time === 'evening' ? t('timeEvening') :
                               requestDetailsDialog.request.metadata.preferred_contact_time === 'anytime' ? t('timeAnytime') : '-'}
                            </Typography>
                          </Box>
                          <Box>
                            <Typography variant="caption" color="text.secondary">{t('preferredContactMethod')}</Typography>
                            <Typography variant="body2" fontWeight="500">
                              {requestDetailsDialog.request.metadata.preferred_contact_method === 'phone' ? t('contactByPhone') :
                               requestDetailsDialog.request.metadata.preferred_contact_method === 'email' ? t('contactByEmail') :
                               requestDetailsDialog.request.metadata.preferred_contact_method === 'line' ? t('contactByLine') :
                               requestDetailsDialog.request.metadata.preferred_contact_method === 'any' ? t('contactByAny') : '-'}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    )}
                  </>
                )}

                <Box>
                  <Typography variant="caption" color="text.secondary">{t('receivedAt')}</Typography>
                  <Typography variant="body1">
                    {formatDateTime(requestDetailsDialog.request.created_at)}
                  </Typography>
                </Box>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {requestDetailsDialog.request && !requestDetailsDialog.request.read && (
            <Button
              onClick={() => {
                handleMarkAsRead(requestDetailsDialog.request._id);
                setRequestDetailsDialog({ open: false, request: null });
              }}
              startIcon={<MarkReadIcon />}
            >
              {t('markAllRead')}
            </Button>
          )}
          <Button onClick={() => setRequestDetailsDialog({ open: false, request: null })}>
            {t('close')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Receipt Viewer Dialog */}
      <Dialog
        open={receiptDialog.open}
        onClose={handleCloseReceiptDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <ViewIcon color="primary" />
              {t('paymentReceipt')}
            </Box>
            {receiptDialog.url && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={handleDownloadReceipt}
              >
                {t('download')}
              </Button>
            )}
          </Box>
        </DialogTitle>
        <DialogContent>
          {receiptDialog.loading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight={300}>
              <CircularProgress />
            </Box>
          ) : receiptDialog.url ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: 300,
                bgcolor: 'grey.100',
                borderRadius: 2,
                p: 2,
              }}
            >
              <img
                src={receiptDialog.url}
                alt="Payment Receipt"
                style={{
                  maxWidth: '100%',
                  maxHeight: '60vh',
                  objectFit: 'contain',
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                }}
              />
            </Box>
          ) : (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight={300}>
              <Typography color="text.secondary">
                {t('noReceiptAvailable')}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseReceiptDialog}>
            {t('close')}
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

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.open} onClose={handleCloseConfirmDialog}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <Typography>{confirmDialog.message}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseConfirmDialog}>{t('cancel')}</Button>
          <Button onClick={handleConfirmAction} variant="contained" color="error">
            {t('confirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminPortal;
