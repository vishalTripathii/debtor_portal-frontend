import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
  Avatar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
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
  Chip,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  SupervisorAccount as SuperAdminIcon,
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  Person as PersonIcon,
  Image as ImageIcon,
  Logout as LogoutIcon,
  Email as EmailIcon,
  AccountBalance as BankIcon,
  TableChart as TableChartIcon,
  Security as SecurityIcon,
  BuildCircle as MaintenanceIcon,
  Group as GroupIcon,
  LockReset as LockResetIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import Grid from '@mui/material/Grid';
import { superAdminApi } from '../services/api';

const SuperAdminPortal = ({ onLogout, onSwitchToAdmin }) => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);

  // Admin user management state
  const [adminUsers, setAdminUsers] = useState([]);
  const [loadingAdmins, setLoadingAdmins] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [selectedAdmin, setSelectedAdmin] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState(null);

  useEffect(() => {
    fetchSettings();
    fetchAdminUsers();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await superAdminApi.getSystemSettings();
      setSettings(response.settings);
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminUsers = async () => {
    setLoadingAdmins(true);
    try {
      const response = await superAdminApi.getAdminUsers();
      setAdminUsers(response.admins || []);
    } catch (error) {
      console.error('Error fetching admin users:', error);
    } finally {
      setLoadingAdmins(false);
    }
  };

  const handleOpenResetDialog = (admin) => {
    setSelectedAdmin(admin);
    setNewPassword('');
    setConfirmPassword('');
    setShowPassword(false);
    setResetMessage(null);
    setResetDialogOpen(true);
  };

  const handleCloseResetDialog = () => {
    setResetDialogOpen(false);
    setSelectedAdmin(null);
    setNewPassword('');
    setConfirmPassword('');
    setResetMessage(null);
  };

  const handleResetPassword = async () => {
    if (!newPassword) {
      setResetMessage({ type: 'error', text: 'Please enter a new password' });
      return;
    }
    if (newPassword.length < 6) {
      setResetMessage({ type: 'error', text: 'Password must be at least 6 characters' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setResetMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }

    setResetting(true);
    setResetMessage(null);
    try {
      await superAdminApi.resetAdminPassword(selectedAdmin.username, newPassword);
      setResetMessage({ type: 'success', text: `Password for ${selectedAdmin.username} has been reset successfully` });
      setTimeout(() => {
        handleCloseResetDialog();
      }, 2000);
    } catch (error) {
      setResetMessage({ type: 'error', text: error.message || 'Failed to reset password' });
    } finally {
      setResetting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage(null);
    try {
      // Only send the settings fields we want to update
      const settingsToSave = {
        admin_tabs: settings.admin_tabs,
        enable_image_upload: settings.enable_image_upload,
        admin_otp_enabled: settings.admin_otp_enabled,
        debtor_features: settings.debtor_features,
        notification_email: settings.notification_email,
        bank_account: settings.bank_account,
        admin_filters: settings.admin_filters,
        table_actions: settings.table_actions,
        table_columns: settings.table_columns,
        maintenance_mode: settings.maintenance_mode,
      };
      await superAdminApi.updateSystemSettings(settingsToSave);
      setSaveMessage({ type: 'success', text: 'Settings saved successfully!' });
      // Refresh settings to confirm save
      await fetchSettings();
    } catch (error) {
      console.error('Save error:', error);
      setSaveMessage({ type: 'error', text: 'Failed to save settings: ' + error.message });
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationEmailChange = (event) => {
    setSettings((prev) => ({
      ...prev,
      notification_email: event.target.value,
    }));
  };

  const handleAdminTabChange = (tabKey) => {
    setSettings((prev) => ({
      ...prev,
      admin_tabs: {
        ...(prev?.admin_tabs || {}),
        [tabKey]: !(prev?.admin_tabs?.[tabKey] ?? true),
      },
    }));
  };

  const handleDebtorFeatureChange = (featureKey) => {
    setSettings((prev) => ({
      ...prev,
      debtor_features: {
        ...(prev?.debtor_features || {}),
        [featureKey]: !(prev?.debtor_features?.[featureKey] ?? true),
      },
    }));
  };

  const handleImageUploadChange = () => {
    setSettings((prev) => ({
      ...prev,
      enable_image_upload: !(prev?.enable_image_upload ?? false),
    }));
  };

  const handleAdminOtpChange = () => {
    setSettings((prev) => ({
      ...prev,
      admin_otp_enabled: !(prev?.admin_otp_enabled ?? false),
    }));
  };

  const handleMaintenanceModeChange = (field) => (event) => {
    setSettings((prev) => ({
      ...prev,
      maintenance_mode: {
        ...(prev?.maintenance_mode || {}),
        [field]: field === 'enabled' ? event.target.checked : event.target.value,
      },
    }));
  };

  const handleBankAccountChange = (field) => (event) => {
    setSettings((prev) => ({
      ...prev,
      bank_account: {
        ...(prev?.bank_account || {}),
        [field]: event.target.value,
      },
    }));
  };

  const handleAdminFilterChange = (filterKey) => {
    setSettings((prev) => ({
      ...prev,
      admin_filters: {
        ...(prev?.admin_filters || {}),
        [filterKey]: !(prev?.admin_filters?.[filterKey] ?? true),
      },
    }));
  };

  const handleTableActionChange = (tableKey) => {
    setSettings((prev) => ({
      ...prev,
      table_actions: {
        ...(prev?.table_actions || {}),
        [tableKey]: !(prev?.table_actions?.[tableKey] ?? true),
      },
    }));
  };

  const handleTableColumnChange = (tableKey, columnKey) => {
    setSettings((prev) => ({
      ...prev,
      table_columns: {
        ...(prev?.table_columns || {}),
        [tableKey]: {
          ...(prev?.table_columns?.[tableKey] || {}),
          [columnKey]: !(prev?.table_columns?.[tableKey]?.[columnKey] ?? true),
        },
      },
    }));
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%)',
        }}
      >
        <CircularProgress sx={{ color: 'white' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%)',
          color: 'white',
          borderRadius: 0,
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" maxWidth="lg" mx="auto">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
              <SuperAdminIcon />
            </Avatar>
            <Box>
              <Typography variant="h5" fontWeight="bold">
                Super Admin Panel
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                System Configuration & Feature Management
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              onClick={onSwitchToAdmin}
              startIcon={<DashboardIcon />}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
              }}
            >
              Admin Portal
            </Button>
            <Button
              variant="outlined"
              onClick={onLogout}
              startIcon={<LogoutIcon />}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' },
              }}
            >
              Logout
            </Button>
          </Box>
        </Box>
      </Paper>

      <Box sx={{ maxWidth: 'lg', mx: 'auto', px: 3, pb: 4 }}>
        {saveMessage && (
          <Alert severity={saveMessage.type} sx={{ mb: 3 }} onClose={() => setSaveMessage(null)}>
            {saveMessage.text}
          </Alert>
        )}

        {/* Maintenance Mode Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <MaintenanceIcon color={settings?.maintenance_mode?.enabled ? 'warning' : 'primary'} />
              <Typography variant="h6" fontWeight="bold">
                Site Maintenance Mode
              </Typography>
              {settings?.maintenance_mode?.enabled && (
                <Box
                  sx={{
                    ml: 2,
                    px: 1.5,
                    py: 0.5,
                    bgcolor: 'warning.main',
                    color: 'warning.contrastText',
                    borderRadius: 1,
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                  }}
                >
                  ACTIVE
                </Box>
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Alert severity={settings?.maintenance_mode?.enabled ? 'warning' : 'info'} sx={{ mb: 3 }}>
              {settings?.maintenance_mode?.enabled
                ? 'Maintenance mode is currently ACTIVE. Customers will see the maintenance page instead of the debtor portal.'
                : 'Enable maintenance mode to show a maintenance page to customers during updates or modifications.'}
            </Alert>
            <Box display="flex" flexDirection="column" gap={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.maintenance_mode?.enabled ?? false}
                    onChange={handleMaintenanceModeChange('enabled')}
                    color="warning"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="bold">Enable Maintenance Mode</Typography>
                    <Typography variant="caption" color="text.secondary">
                      When enabled, customers will see a maintenance page instead of the debtor portal.
                    </Typography>
                  </Box>
                }
              />

              <TextField
                fullWidth
                label="Maintenance Title"
                placeholder="e.g., System Maintenance in Progress"
                value={settings?.maintenance_mode?.title || ''}
                onChange={handleMaintenanceModeChange('title')}
                helperText="The main heading shown on the maintenance page"
              />

              <TextField
                fullWidth
                label="Maintenance Message"
                placeholder="e.g., We are currently performing scheduled maintenance. Please check back later."
                value={settings?.maintenance_mode?.message || ''}
                onChange={handleMaintenanceModeChange('message')}
                multiline
                rows={3}
                helperText="A detailed message explaining the maintenance to customers"
              />

              <TextField
                fullWidth
                label="Estimated Return Time (Optional)"
                placeholder="e.g., 2:00 PM Bangkok Time"
                value={settings?.maintenance_mode?.estimated_time || ''}
                onChange={handleMaintenanceModeChange('estimated_time')}
                helperText="Let customers know when the site will be back (leave empty to hide)"
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Admin Portal Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <SettingsIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Admin Portal Tabs
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Control which tabs are visible in the Admin Portal. Disabled tabs will be hidden from admin users.
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_tabs?.upload_data ?? true}
                    onChange={() => handleAdminTabChange('upload_data')}
                    color="primary"
                  />
                }
                label="Upload Data Tab"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_tabs?.view_accounts ?? true}
                    onChange={() => handleAdminTabChange('view_accounts')}
                    color="primary"
                  />
                }
                label="View Accounts Tab"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_tabs?.debtor_requests ?? true}
                    onChange={() => handleAdminTabChange('debtor_requests')}
                    color="primary"
                  />
                }
                label="Debtor Requests Tab"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_tabs?.upload_history ?? true}
                    onChange={() => handleAdminTabChange('upload_history')}
                    color="primary"
                  />
                }
                label="Upload History Tab"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_tabs?.settings ?? true}
                    onChange={() => handleAdminTabChange('settings')}
                    color="primary"
                  />
                }
                label="Settings Tab"
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Admin Security Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <SecurityIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Admin Security Settings
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configure security settings for admin login. Note: Super Admin login always uses password-only authentication.
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_otp_enabled ?? false}
                    onChange={handleAdminOtpChange}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Enable OTP for Admin Login</Typography>
                    <Typography variant="caption" color="text.secondary">
                      When enabled, admin users must verify their login with a one-time password sent to the notification email.
                      Super Admin login is not affected by this setting.
                    </Typography>
                  </Box>
                }
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Admin User Management */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <GroupIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Admin User Management
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="body2" color="text.secondary">
                Manage admin user accounts. Reset passwords for users who leave the organization or forget their credentials.
              </Typography>
              <IconButton onClick={fetchAdminUsers} disabled={loadingAdmins} size="small">
                <RefreshIcon />
              </IconButton>
            </Box>
            {loadingAdmins ? (
              <Box display="flex" justifyContent="center" py={3}>
                <CircularProgress size={24} />
              </Box>
            ) : adminUsers.length === 0 ? (
              <Alert severity="info">No admin users found.</Alert>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'grey.100' }}>
                      <TableCell><strong>Username</strong></TableCell>
                      <TableCell><strong>Role</strong></TableCell>
                      <TableCell><strong>Email</strong></TableCell>
                      <TableCell align="center"><strong>Actions</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {adminUsers.map((admin) => (
                      <TableRow key={admin.username} hover>
                        <TableCell>{admin.username}</TableCell>
                        <TableCell>
                          <Chip
                            label={admin.role === 'super_admin' ? 'Super Admin' : 'Admin'}
                            size="small"
                            color={admin.role === 'super_admin' ? 'secondary' : 'primary'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>{admin.email || '-'}</TableCell>
                        <TableCell align="center">
                          {admin.role !== 'super_admin' && (
                            <Button
                              size="small"
                              startIcon={<LockResetIcon />}
                              onClick={() => handleOpenResetDialog(admin)}
                              color="warning"
                            >
                              Reset Password
                            </Button>
                          )}
                          {admin.role === 'super_admin' && (
                            <Typography variant="caption" color="text.secondary">
                              Change via .env
                            </Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Admin Filters Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <SettingsIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Debtor Requests Filters
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Control which filters are visible in the "Debtor Payments and Requests" tab.
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_filters?.type_filter ?? true}
                    onChange={() => handleAdminFilterChange('type_filter')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Type Filter</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Filter requests by type (Payment Submitted, Not Ready to Pay)
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.admin_filters?.status_filter ?? true}
                    onChange={() => handleAdminFilterChange('status_filter')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Status Filter</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Filter requests by status (Read, Unread)
                    </Typography>
                  </Box>
                }
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Table Action Columns Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <SettingsIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Table Action Columns
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Control which tables show the "Actions" column. When disabled, the entire action column will be hidden for that table.
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.table_actions?.view_accounts ?? true}
                    onChange={() => handleTableActionChange('view_accounts')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">View Accounts Table</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Show actions column (View, Delete) in the View Accounts tab
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.table_actions?.debtor_requests ?? true}
                    onChange={() => handleTableActionChange('debtor_requests')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Debtor Requests Table</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Show actions column (View, Mark Read, Download) in Debtor Requests tab
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.table_actions?.upload_history ?? true}
                    onChange={() => handleTableActionChange('upload_history')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Upload History Table</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Show actions column (Download) in Upload History tab
                    </Typography>
                  </Box>
                }
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Table Columns Visibility */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <TableChartIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Table Columns Visibility
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Control which columns are visible in each table. Disabled columns will be hidden from admin users.
            </Typography>

            {/* View Accounts Table Columns */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="primary">
                View Accounts Table
              </Typography>
              <Grid container spacing={1}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.case_id ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'case_id')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Case ID</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.upload_id ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'upload_id')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Upload ID</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.account_number ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'account_number')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Account Number</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.national_id ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'national_id')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">National ID</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.name ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'name')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Name</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.debt_type ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'debt_type')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Debt Type</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.loan_contract_date ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'loan_contract_date')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Loan Contract Date</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.outstanding_balance ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'outstanding_balance')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Outstanding Balance</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.created_at ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'created_at')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Created At</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.updated_at ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'updated_at')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Updated At</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.view_accounts?.qr_code ?? true}
                        onChange={() => handleTableColumnChange('view_accounts', 'qr_code')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">QR Code</Typography>}
                  />
                </Grid>
              </Grid>
            </Paper>

            {/* Debtor Requests Table Columns */}
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="primary">
                Debtor Requests Table
              </Typography>
              <Grid container spacing={1}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.type ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'type')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Request Type</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.debtor_name ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'debtor_name')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Debtor Name</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.account_number ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'account_number')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Account Number</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.outstanding_balance ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'outstanding_balance')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Outstanding Balance</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.payment_amount ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'payment_amount')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Payment Amount</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.transaction_number ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'transaction_number')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Transaction Number</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.receipt ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'receipt')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Receipt</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.message ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'message')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Message</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.created_at ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'created_at')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Received At</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.debtor_requests?.read ?? true}
                        onChange={() => handleTableColumnChange('debtor_requests', 'read')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Status</Typography>}
                  />
                </Grid>
              </Grid>
            </Paper>

            {/* Upload History Table Columns */}
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom color="primary">
                Upload History Table
              </Typography>
              <Grid container spacing={1}>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.upload_id ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'upload_id')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Upload ID</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.uploaded_at ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'uploaded_at')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Date/Time</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.filename ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'filename')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Filename</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.file_size ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'file_size')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">File Size</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.total_records ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'total_records')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Total Records</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.inserted_count ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'inserted_count')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Inserted</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.updated_count ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'updated_count')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Updated</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.uploaded_by ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'uploaded_by')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Uploaded By</Typography>}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        size="small"
                        checked={settings?.table_columns?.upload_history?.status ?? true}
                        onChange={() => handleTableColumnChange('upload_history', 'status')}
                        color="primary"
                      />
                    }
                    label={<Typography variant="body2">Status</Typography>}
                  />
                </Grid>
              </Grid>
            </Paper>
          </AccordionDetails>
        </Accordion>

        {/* Image Upload Feature */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <ImageIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Image Upload Feature
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Enable or disable the image upload feature in the Admin Portal's Upload Data tab.
              When enabled, admins can upload images for debtor accounts (filename must match account number).
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={settings?.enable_image_upload ?? false}
                  onChange={handleImageUploadChange}
                  color="primary"
                />
              }
              label={
                <Box>
                  <Typography variant="body1">Enable Image Upload</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Allow admins to upload images for debtor accounts
                  </Typography>
                </Box>
              }
            />
          </AccordionDetails>
        </Accordion>

        {/* Debtor Portal Features */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <PersonIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Debtor Portal Features
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Control which features are available to customers in the Customer Self-Service Portal.
            </Typography>
            <Box display="flex" flexDirection="column" gap={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.debtor_features?.make_payment ?? true}
                    onChange={() => handleDebtorFeatureChange('make_payment')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Make a Payment Button</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Allow debtors to submit payment requests
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.debtor_features?.not_ready_to_pay ?? true}
                    onChange={() => handleDebtorFeatureChange('not_ready_to_pay')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Not Ready to Pay Button</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Allow debtors to indicate they cannot pay
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.debtor_features?.line_qr_support ?? true}
                    onChange={() => handleDebtorFeatureChange('line_qr_support')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">LINE QR Support Section</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Show LINE QR code for customer support
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={settings?.debtor_features?.update_contact ?? true}
                    onChange={() => handleDebtorFeatureChange('update_contact')}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1">Update Contact Information</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Allow debtors to update their phone and email
                    </Typography>
                  </Box>
                }
              />
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Notification Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <EmailIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Notification Settings
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configure email notifications for payment requests and other debtor actions.
            </Typography>
            <TextField
              fullWidth
              label="Notification Email Address"
              type="email"
              value={settings?.notification_email || ''}
              onChange={handleNotificationEmailChange}
              placeholder="collections@example.com"
              helperText="Payment notifications and debtor requests will be sent to this email address"
              sx={{ maxWidth: 500 }}
            />
          </AccordionDetails>
        </Accordion>

        {/* Bank Account Settings */}
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={1}>
              <BankIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">
                Bank Account Settings (Thai Bank Transfer)
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configure bank account details for payment transfers. These details will be shown to debtors in the payment dialog.
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Bank Name"
                  value={settings?.bank_account?.bank_name || ''}
                  onChange={handleBankAccountChange('bank_name')}
                  placeholder="e.g., Bangkok Bank, Kasikornbank, SCB"
                  helperText="Name of the bank"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Account Name"
                  value={settings?.bank_account?.account_name || ''}
                  onChange={handleBankAccountChange('account_name')}
                  placeholder="Beneficiary name"
                  helperText="Name on the bank account"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Account Number"
                  value={settings?.bank_account?.account_number || ''}
                  onChange={handleBankAccountChange('account_number')}
                  placeholder="e.g., 123-4-56789-0"
                  helperText="Bank account number"
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="PromptPay ID"
                  value={settings?.bank_account?.promptpay_id || ''}
                  onChange={handleBankAccountChange('promptpay_id')}
                  placeholder="Phone number or National ID"
                  helperText="PromptPay ID for instant transfers"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Save Button */}
        <Box display="flex" justifyContent="flex-end" mt={3}>
          <Button
            variant="contained"
            size="large"
            startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
            onClick={handleSave}
            disabled={saving}
            sx={{
              background: 'linear-gradient(135deg, #4a148c 0%, #7b1fa2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #6a1b9a 0%, #9c27b0 100%)',
              },
            }}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </Box>

        {/* Info Card */}
        <Card sx={{ mt: 4, bgcolor: 'grey.50' }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Super Admin Credentials
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2">
              <strong>Username:</strong> superadmin
            </Typography>
            <Typography variant="body2">
              <strong>Password:</strong> superadmin123
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Note: Change these credentials in your .env file for production.
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Password Reset Dialog */}
      <Dialog open={resetDialogOpen} onClose={handleCloseResetDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <LockResetIcon color="warning" />
            Reset Password for {selectedAdmin?.username}
          </Box>
        </DialogTitle>
        <DialogContent>
          {resetMessage && (
            <Alert severity={resetMessage.type} sx={{ mb: 2 }}>
              {resetMessage.text}
            </Alert>
          )}
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Enter a new password for this admin user. The user will need to use this new password to log in.
          </Typography>
          <TextField
            fullWidth
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                    {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <TextField
            fullWidth
            label="Confirm Password"
            type={showPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={confirmPassword && newPassword !== confirmPassword}
            helperText={confirmPassword && newPassword !== confirmPassword ? 'Passwords do not match' : ''}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button onClick={handleCloseResetDialog} disabled={resetting}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleResetPassword}
            disabled={resetting || !newPassword || !confirmPassword}
            startIcon={resetting ? <CircularProgress size={16} color="inherit" /> : <LockResetIcon />}
          >
            {resetting ? 'Resetting...' : 'Reset Password'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SuperAdminPortal;
