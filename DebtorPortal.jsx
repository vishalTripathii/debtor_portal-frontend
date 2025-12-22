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
  Slider,
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
  LinearProgress
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
  Calculate as CalculatorIcon
} from '@mui/icons-material';
import { useActivityLog } from '../../context/ActivityLogContext';

const DebtorPortal = () => {
  const { addLog } = useActivityLog();
  const currentUser = 'Debtor User';
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginStep, setLoginStep] = useState(0);
  const [accountNumber, setAccountNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [paymentDialog, setPaymentDialog] = useState(false);
  const [settlementDialog, setSettlementDialog] = useState(false);
  const [paymentType, setPaymentType] = useState('full');
  const [installmentPlan, setInstallmentPlan] = useState('3');
  const [customAmount, setCustomAmount] = useState('');
  const [notReadyDialog, setNotReadyDialog] = useState(false);
  const [deferralMonths, setDeferralMonths] = useState(1);
  const [showOTP, setShowOTP] = useState(false);
  const [budgetIncome, setBudgetIncome] = useState('');
  const [budgetExpenses, setBudgetExpenses] = useState('');
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizScore, setQuizScore] = useState(null);

  // Update Contact Information states
  const [updateContactDialog, setUpdateContactDialog] = useState(false);
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [phoneOTP, setPhoneOTP] = useState('');
  const [emailOTP, setEmailOTP] = useState('');
  const [phoneOTPSent, setPhoneOTPSent] = useState(false);
  const [emailOTPSent, setEmailOTPSent] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(false);
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
    minimumPayment: 500.00,
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

  // Initialize contact data with mock account data
  useEffect(() => {
    setContactData({
      phone: mockDebtorAccount.phone,
      email: mockDebtorAccount.email
    });
  }, []);

  const handleLogin = () => {
    if (loginStep === 0) {
      // Simulate sending OTP
      console.log('Sending OTP to account:', accountNumber);
      setLoginStep(1);
    } else {
      // Simulate OTP verification
      console.log('Verifying OTP:', otp);
      setIsLoggedIn(true);
    }
  };

  const handleMakePayment = () => {
    console.log('Processing payment:', { paymentType, customAmount, installmentPlan });
    setPaymentDialog(false);
    // Show success message
  };

  const handleAcceptSettlement = () => {
    console.log('Accepting settlement offer');
    setSettlementDialog(false);
    // Show success message
  };

  const handleNotReady = () => {
    console.log('Submitting deferral request for', deferralMonths, 'months');
    setNotReadyDialog(false);
    // Show success message
  };

  const handleResendOTP = () => {
    addLog({
      user: currentUser,
      action: 'OTP Resent',
      entity: 'Debtor Portal',
      entityId: accountNumber,
      entityName: 'Login',
      details: 'OTP resent to registered mobile number',
      category: 'portal',
      status: 'success'
    });
    alert('OTP has been resent to your registered mobile number!\n\nPlease check your SMS.');
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
      alert('Please enter a new phone number');
      return;
    }
    // Simulate sending OTP
    alert(`OTP sent to ${newPhone}\nFor demo: use OTP `);
    setPhoneOTPSent(true);
    addLog({
      user: currentUser,
      action: 'Phone OTP Sent',
      entity: 'Contact Update',
      entityId: mockDebtorAccount.accountNumber,
      entityName: mockDebtorAccount.debtorName,
      details: `OTP sent to ${newPhone}`,
      category: 'security',
      status: 'success'
    });
  };

  const handleVerifyPhoneOTP = () => {
    // Simulate OTP verification (in production, verify with backend)
    if (phoneOTP === '') {
      setPhoneVerified(true);
      alert('Phone number verified successfully!');
      addLog({
        user: currentUser,
        action: 'Phone Verified',
        entity: 'Contact Update',
        entityId: mockDebtorAccount.accountNumber,
        entityName: mockDebtorAccount.debtorName,
        details: `Phone verified: ${newPhone}`,
        category: 'security',
        status: 'success'
      });
    } else {
      alert('Invalid OTP. Please try again.');
    }
  };

  const handleSendEmailOTP = () => {
    if (!newEmail || newEmail === contactData.email) {
      alert('Please enter a new email address');
      return;
    }
    // Simulate sending OTP
    alert(`OTP sent to ${newEmail}\nFor demo: use OTP 654321`);
    setEmailOTPSent(true);
    addLog({
      user: currentUser,
      action: 'Email OTP Sent',
      entity: 'Contact Update',
      entityId: mockDebtorAccount.accountNumber,
      entityName: mockDebtorAccount.debtorName,
      details: `OTP sent to ${newEmail}`,
      category: 'security',
      status: 'success'
    });
  };

  const handleVerifyEmailOTP = () => {
    // Simulate OTP verification (in production, verify with backend)
    if (emailOTP === '654321') {
      setEmailVerified(true);
      alert('Email address verified successfully!');
      addLog({
        user: currentUser,
        action: 'Email Verified',
        entity: 'Contact Update',
        entityId: mockDebtorAccount.accountNumber,
        entityName: mockDebtorAccount.debtorName,
        details: `Email verified: ${newEmail}`,
        category: 'security',
        status: 'success'
      });
    } else {
      alert('Invalid OTP. Please try again.');
    }
  };

  const handleSaveContactInfo = () => {
    let updated = false;
    let changes = [];

    if (newPhone !== contactData.phone && phoneVerified) {
      setContactData(prev => ({ ...prev, phone: newPhone }));
      changes.push(`Phone updated to ${newPhone}`);
      updated = true;
    }

    if (newEmail !== contactData.email && emailVerified) {
      setContactData(prev => ({ ...prev, email: newEmail }));
      changes.push(`Email updated to ${newEmail}`);
      updated = true;
    }

    if (updated) {
      addLog({
        user: currentUser,
        action: 'Contact Information Updated',
        entity: 'Debtor Account',
        entityId: mockDebtorAccount.accountNumber,
        entityName: mockDebtorAccount.debtorName,
        details: changes.join(', '),
        category: 'account',
        status: 'success'
      });
      alert(`Contact information updated successfully!\n\n${changes.join('\n')}`);
      setUpdateContactDialog(false);
    } else {
      alert('No changes to save or verification pending.');
    }
  };

  const handleRequestPaymentPlan = () => {
    alert('Request Payment Plan\n\nYou will be redirected to the payment plan request form.\n\nConnecting to backend API...');
  };

  const handleContactSupport = () => {
    alert('Contact Support\n\nYou can reach us:\n- Email: support@collections.com\n- Phone: 1800-XXX-XXXX\n- Live Chat (9 AM - 6 PM)\n\nConnecting to support system...');
  };

  const handleDownloadStatement = (doc) => {
    addLog({
      user: currentUser,
      action: 'Document Downloaded',
      entity: 'Debtor Portal',
      entityId: accountNumber,
      entityName: doc || 'Account Statement',
      details: `Downloaded: ${doc || 'Account Statement'}`,
      category: 'portal',
      status: 'success'
    });
    alert(`Downloading ${doc || 'document'}...\n\nThis will be connected to document download system.`);
  };

  const handleViewResources = (resource) => {
    addLog({
      user: currentUser,
      action: 'Resource Viewed',
      entity: 'Debtor Portal',
      entityId: accountNumber,
      entityName: resource,
      details: `Viewed educational resource: ${resource}`,
      category: 'portal',
      status: 'success'
    });
    alert(`Opening resource: ${resource}\n\nThis will open the educational content viewer.`);
  };

  const handleViewAllTips = () => {
    alert('View All Financial Tips\n\nOpening comprehensive financial wellness guide...\n\nThis will be connected to the educational resources library.');
  };

  const calculateInstallment = (amount, months) => {
    return (amount / parseInt(months)).toFixed(2);
  };

  // Login Screen
  if (!isLoggedIn) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
          p: 3
        }}
      >
        <Card sx={{ maxWidth: 500, width: '100%' }}>
          <CardContent sx={{ p: 4 }}>
            <Box textAlign="center" mb={4}>
              <Typography variant="h4" gutterBottom>
                Debtor Self-Service Portal
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Access your account to view balance and make payments
              </Typography>
            </Box>

            <Stepper activeStep={loginStep} sx={{ mb: 4 }}>
              <Step>
                <StepLabel>Enter Account Number</StepLabel>
              </Step>
              <Step>
                <StepLabel>Verify OTP</StepLabel>
              </Step>
            </Stepper>

            {loginStep === 0 ? (
              <Box>
                <TextField
                  fullWidth
                  label="Account Number"
                  value={accountNumber}
                  onChange={(e) => setAccountNumber(e.target.value)}
                  placeholder="ACC-XXXXX"
                  sx={{ mb: 2 }}
                />
                <Alert severity="info" sx={{ mb: 3 }}>
                  Enter your account number. We'll send a one-time password (OTP) to your registered phone number.
                </Alert>
              </Box>
            ) : (
              <Box>
                <TextField
                  fullWidth
                  label="Enter OTP"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="6-digit OTP"
                  type={showOTP ? 'text' : 'password'}
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
                <Alert severity="info" sx={{ mb: 3 }}>
                  OTP sent to +1-555-XXXX. Valid for 10 minutes.
                </Alert>
                <Button size="small" sx={{ mb: 2 }} onClick={handleResendOTP}>
                  Resend OTP
                </Button>
              </Box>
            )}

            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handleLogin}
              disabled={loginStep === 0 ? !accountNumber : !otp}
            >
              {loginStep === 0 ? 'Send OTP' : 'Login'}
            </Button>

            <Box mt={3} textAlign="center">
              <Typography variant="caption" color="text.secondary">
                Need help? Contact us at support@collections.com or +1-800-COLLECT
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  // Main Portal Interface
  return (
    <Box sx={{ p: 3 }}>
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Welcome, {mockDebtorAccount.debtorName}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Account Number: {mockDebtorAccount.accountNumber}
            </Typography>
          </Box>
          <Button variant="outlined" onClick={() => setIsLoggedIn(false)}>
            Logout
          </Button>
        </Box>
      </Box>

      {/* Outstanding Balance Card */}
      <Card sx={{ mb: 3, bgcolor: 'error.main', color: 'white' }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Current Outstanding Balance
              </Typography>
              <Typography variant="h3" fontWeight="bold">
                ${mockDebtorAccount.outstandingBalance.toLocaleString()}
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.8, mt: 1 }}>
                Original Amount: ${mockDebtorAccount.originalBalance.toLocaleString()} |
                Days Past Due: {mockDebtorAccount.daysPastDue}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button
                  variant="contained"
                  size="large"
                  sx={{ bgcolor: 'white', color: 'error.main', '&:hover': { bgcolor: 'grey.100' } }}
                  startIcon={<PaymentIcon />}
                  onClick={() => setPaymentDialog(true)}
                >
                  Make a Payment
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  sx={{ borderColor: 'white', color: 'white', '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' } }}
                  onClick={() => setNotReadyDialog(true)}
                >
                  Not Ready to Pay
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Settlement Offer Alert */}
      {mockDebtorAccount.settlementOffer.available && (
        <Alert
          severity="success"
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={() => setSettlementDialog(true)}>
              View Details
            </Button>
          }
        >
          <Typography variant="body2" fontWeight="bold">
            Special Settlement Offer Available!
          </Typography>
          <Typography variant="body2">
            Settle your debt for ${mockDebtorAccount.settlementOffer.settlementAmount.toLocaleString()}
            (Save ${(mockDebtorAccount.outstandingBalance - mockDebtorAccount.settlementOffer.settlementAmount).toLocaleString()})
            - Valid until {mockDebtorAccount.settlementOffer.validUntil}
          </Typography>
        </Alert>
      )}

      {/* Active PTP Alert */}
      {mockDebtorAccount.activePTP && (
        <Alert severity="info" sx={{ mb: 3 }} icon={<ScheduleIcon />}>
          <Typography variant="body2">
            <strong>Active Payment Promise:</strong> ${mockDebtorAccount.activePTP.amount.toLocaleString()}
            due on {mockDebtorAccount.activePTP.date}
          </Typography>
        </Alert>
      )}

      {/* Tabs for Different Sections */}
      <Card>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Account Details" />
          <Tab label="Payment History" />
          <Tab label="Documents" />
          <Tab label="Financial Resources" icon={<EducationIcon />} iconPosition="start" />
        </Tabs>

        <CardContent>
          {/* Account Details Tab */}
          {tabValue === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Account Information
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Account Number</Typography>
                      <Typography variant="body1" fontWeight="bold">{mockDebtorAccount.accountNumber}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Debt Type</Typography>
                      <Typography variant="body1">{mockDebtorAccount.debtType}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Original Creditor</Typography>
                      <Typography variant="body1">{mockDebtorAccount.originalCreditor}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Charge-off Date</Typography>
                      <Typography variant="body1">{mockDebtorAccount.chargeOffDate}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Outstanding Balance</Typography>
                      <Typography variant="h5" color="error.main">
                        ${mockDebtorAccount.outstandingBalance.toLocaleString()}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Minimum Payment Required</Typography>
                      <Typography variant="h6">
                        ${mockDebtorAccount.minimumPayment.toLocaleString()}
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Contact Information
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Name</Typography>
                      <Typography variant="body1" fontWeight="bold">{mockDebtorAccount.debtorName}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Phone</Typography>
                      <Typography variant="body1">{mockDebtorAccount.phone}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Email</Typography>
                      <Typography variant="body1">{mockDebtorAccount.email}</Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Button variant="outlined" size="small" onClick={handleUpdateContact}>
                        Update Contact Information
                      </Button>
                    </Grid>
                  </Grid>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  <List dense>
                    <ListItem>
                      <Button fullWidth variant="outlined" startIcon={<PaymentIcon />} onClick={() => setPaymentDialog(true)}>
                        Make a Payment
                      </Button>
                    </ListItem>
                    <ListItem>
                      <Button fullWidth variant="outlined" startIcon={<ScheduleIcon />} onClick={handleRequestPaymentPlan}>
                        Request Payment Plan
                      </Button>
                    </ListItem>
                    <ListItem>
                      <Button fullWidth variant="outlined" startIcon={<SendIcon />} onClick={handleContactSupport}>
                        Contact Support
                      </Button>
                    </ListItem>
                  </List>
                </Paper>
              </Grid>
            </Grid>
          )}

          {/* Payment History Tab */}
          {tabValue === 1 && (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6">Payment History</Typography>
                <Button startIcon={<DownloadIcon />} variant="outlined" size="small" onClick={() => handleDownloadStatement('Account Statement')}>
                  Download Statement
                </Button>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockDebtorAccount.paymentHistory.map((payment, index) => (
                      <TableRow key={index}>
                        <TableCell>{payment.date}</TableCell>
                        <TableCell>{payment.type}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            ${payment.amount.toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={payment.status}
                            size="small"
                            color="success"
                            icon={<CheckIcon />}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {mockDebtorAccount.paymentHistory.length === 0 && (
                <Box textAlign="center" py={4}>
                  <Typography variant="body1" color="text.secondary">
                    No payment history available
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Documents Tab */}
          {tabValue === 2 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Account Documents
              </Typography>
              <List>
                {mockDebtorAccount.documents.map((doc, index) => (
                  <ListItem
                    key={index}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1
                    }}
                    secondaryAction={
                      <IconButton edge="end" onClick={() => handleDownloadStatement(doc.name)}>
                        <DownloadIcon />
                      </IconButton>
                    }
                  >
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <DocumentIcon />
                          <Typography variant="body1">{doc.name}</Typography>
                        </Box>
                      }
                      secondary={`${doc.type} - ${doc.date}`}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Financial Resources Tab */}
          {tabValue === 3 && (
            <Box>
              <Alert severity="success" sx={{ mb: 3 }}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Build Your Financial Future
                </Typography>
                <Typography variant="body2">
                  Use these resources to improve your financial literacy and manage your money better
                </Typography>
              </Alert>

              {/* Educational Content Cards */}
              <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} md={4}>
                  <Card sx={{ height: '100%', border: '2px solid', borderColor: 'primary.main' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                          <EducationIcon />
                        </Avatar>
                        <Typography variant="h6">
                          Financial Basics
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        Learn the fundamentals of budgeting, saving, and managing debt effectively
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText
                            primary="Understanding Credit Scores"
                            secondary="How credit works and how to improve it"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Creating a Budget"
                            secondary="Track income and expenses effectively"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Debt Management Strategies"
                            secondary="Methods to pay off debt faster"
                          />
                        </ListItem>
                      </List>
                      <Button variant="outlined" fullWidth sx={{ mt: 2 }} onClick={() => handleViewResources('Financial Basics')}>
                        View Resources
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card sx={{ height: '100%', border: '2px solid', borderColor: 'success.main' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                          <GrowthIcon />
                        </Avatar>
                        <Typography variant="h6">
                          Building Wealth
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        Strategies for saving, investing, and growing your financial assets
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText
                            primary="Emergency Fund Essentials"
                            secondary="Why you need one and how to build it"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Smart Saving Habits"
                            secondary="Automated savings and goal setting"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Investment Basics"
                            secondary="Introduction to growing your money"
                          />
                        </ListItem>
                      </List>
                      <Button variant="outlined" fullWidth sx={{ mt: 2 }} onClick={() => handleViewResources('Building Wealth')}>
                        View Resources
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card sx={{ height: '100%', border: '2px solid', borderColor: 'warning.main' }}>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                          <TipIcon />
                        </Avatar>
                        <Typography variant="h6">
                          Quick Tips
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        Practical advice for everyday financial decisions
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemText
                            primary="50/30/20 Rule"
                            secondary="50% needs, 30% wants, 20% savings"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Negotiate Bills"
                            secondary="How to reduce monthly expenses"
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText
                            primary="Avoid Common Traps"
                            secondary="Steer clear of predatory lending"
                          />
                        </ListItem>
                      </List>
                      <Button variant="outlined" fullWidth sx={{ mt: 2 }} onClick={handleViewAllTips}>
                        View All Tips
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Budget Calculator */}
              <Card sx={{ mb: 4 }}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={3}>
                    <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                      <CalculatorIcon />
                    </Avatar>
                    <Typography variant="h6">
                      Simple Budget Calculator
                    </Typography>
                  </Box>

                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Monthly Income"
                        type="number"
                        value={budgetIncome}
                        onChange={(e) => setBudgetIncome(e.target.value)}
                        InputProps={{
                          startAdornment: '$'
                        }}
                        placeholder="3000"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Monthly Expenses"
                        type="number"
                        value={budgetExpenses}
                        onChange={(e) => setBudgetExpenses(e.target.value)}
                        InputProps={{
                          startAdornment: '$'
                        }}
                        placeholder="2500"
                      />
                    </Grid>
                  </Grid>

                  {budgetIncome && budgetExpenses && (
                    <Box mt={3}>
                      <Divider sx={{ mb: 3 }} />
                      <Grid container spacing={3}>
                        <Grid item xs={12} md={4}>
                          <Paper sx={{ p: 2, bgcolor: 'background.paper', border: '2px solid', borderColor: 'primary.main', textAlign: 'center' }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Monthly Income
                            </Typography>
                            <Typography variant="h5" fontWeight="bold">
                              ${parseInt(budgetIncome).toLocaleString()}
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <Paper sx={{ p: 2, bgcolor: 'background.paper', border: '2px solid', borderColor: 'error.main', textAlign: 'center' }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Monthly Expenses
                            </Typography>
                            <Typography variant="h5" fontWeight="bold">
                              ${parseInt(budgetExpenses).toLocaleString()}
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <Paper sx={{
                            p: 2,
                            border: '2px solid',
                            borderColor: (parseInt(budgetIncome) - parseInt(budgetExpenses)) >= 0 ? 'success.main' : 'warning.main',
                            bgcolor: 'background.paper',
                            textAlign: 'center'
                          }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Surplus/Deficit
                            </Typography>
                            <Typography variant="h5" fontWeight="bold">
                              ${Math.abs(parseInt(budgetIncome) - parseInt(budgetExpenses)).toLocaleString()}
                              {(parseInt(budgetIncome) - parseInt(budgetExpenses)) < 0 && ' Deficit'}
                            </Typography>
                          </Paper>
                        </Grid>
                      </Grid>

                      {(parseInt(budgetIncome) - parseInt(budgetExpenses)) < 0 && (
                        <Alert severity="warning" sx={{ mt: 2 }}>
                          Your expenses exceed your income. Consider reviewing your spending or finding ways to increase income.
                        </Alert>
                      )}

                      {(parseInt(budgetIncome) - parseInt(budgetExpenses)) >= 0 && (
                        <Alert severity="success" sx={{ mt: 2 }}>
                          Great job! You have a surplus. Consider saving or using it to pay down debt faster.
                        </Alert>
                      )}

                      {/* Budget Recommendations */}
                      <Box mt={3}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          Recommended Budget Breakdown (50/30/20 Rule)
                        </Typography>
                        <Grid container spacing={2} mt={1}>
                          <Grid item xs={12} md={4}>
                            <Box p={2} border={1} borderColor="divider" borderRadius={1}>
                              <Typography variant="body2" color="text.secondary">
                                Needs (50%)
                              </Typography>
                              <Typography variant="h6" color="primary">
                                ${(parseInt(budgetIncome) * 0.5).toLocaleString()}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Housing, food, utilities, transport
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={4}>
                            <Box p={2} border={1} borderColor="divider" borderRadius={1}>
                              <Typography variant="body2" color="text.secondary">
                                Wants (30%)
                              </Typography>
                              <Typography variant="h6" color="primary">
                                ${(parseInt(budgetIncome) * 0.3).toLocaleString()}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Entertainment, dining, hobbies
                              </Typography>
                            </Box>
                          </Grid>
                          <Grid item xs={12} md={4}>
                            <Box p={2} border={1} borderColor="divider" borderRadius={1}>
                              <Typography variant="body2" color="text.secondary">
                                Savings (20%)
                              </Typography>
                              <Typography variant="h6" color="success.main">
                                ${(parseInt(budgetIncome) * 0.2).toLocaleString()}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Emergency fund, debt, investments
                              </Typography>
                            </Box>
                          </Grid>
                        </Grid>
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Financial Health Quiz */}
              <Card sx={{ mb: 4 }}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={3}>
                    <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                      <AchievementIcon />
                    </Avatar>
                    <Typography variant="h6">
                      Financial Health Quiz
                    </Typography>
                  </Box>

                  <Typography variant="body2" color="text.secondary" paragraph>
                    Test your financial knowledge and get personalized recommendations
                  </Typography>

                  {quizScore === null ? (
                    <Box>
                      {/* Quiz Questions */}
                      <Box mb={3}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          1. What percentage of your income should go to savings?
                        </Typography>
                        <RadioGroup
                          value={quizAnswers.q1 || ''}
                          onChange={(e) => setQuizAnswers({...quizAnswers, q1: e.target.value})}
                        >
                          <FormControlLabel value="5" control={<Radio />} label="5%" />
                          <FormControlLabel value="10" control={<Radio />} label="10%" />
                          <FormControlLabel value="20" control={<Radio />} label="20% (Correct)" />
                          <FormControlLabel value="30" control={<Radio />} label="30%" />
                        </RadioGroup>
                      </Box>

                      <Box mb={3}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          2. What is the debt snowball method?
                        </Typography>
                        <RadioGroup
                          value={quizAnswers.q2 || ''}
                          onChange={(e) => setQuizAnswers({...quizAnswers, q2: e.target.value})}
                        >
                          <FormControlLabel value="highest" control={<Radio />} label="Pay highest interest debt first" />
                          <FormControlLabel value="smallest" control={<Radio />} label="Pay smallest debt first (Correct)" />
                          <FormControlLabel value="oldest" control={<Radio />} label="Pay oldest debt first" />
                          <FormControlLabel value="random" control={<Radio />} label="Pay debts randomly" />
                        </RadioGroup>
                      </Box>

                      <Box mb={3}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          3. How many months of expenses should your emergency fund cover?
                        </Typography>
                        <RadioGroup
                          value={quizAnswers.q3 || ''}
                          onChange={(e) => setQuizAnswers({...quizAnswers, q3: e.target.value})}
                        >
                          <FormControlLabel value="1" control={<Radio />} label="1 month" />
                          <FormControlLabel value="3" control={<Radio />} label="3 months" />
                          <FormControlLabel value="6" control={<Radio />} label="3-6 months (Correct)" />
                          <FormControlLabel value="12" control={<Radio />} label="12 months" />
                        </RadioGroup>
                      </Box>

                      <Box mb={3}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          4. What's a good credit score range?
                        </Typography>
                        <RadioGroup
                          value={quizAnswers.q4 || ''}
                          onChange={(e) => setQuizAnswers({...quizAnswers, q4: e.target.value})}
                        >
                          <FormControlLabel value="500-600" control={<Radio />} label="500-600" />
                          <FormControlLabel value="600-700" control={<Radio />} label="600-700" />
                          <FormControlLabel value="700-850" control={<Radio />} label="700-850 (Correct)" />
                          <FormControlLabel value="850-1000" control={<Radio />} label="850-1000" />
                        </RadioGroup>
                      </Box>

                      <Box mb={3}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                          5. What's the best approach to debt repayment?
                        </Typography>
                        <RadioGroup
                          value={quizAnswers.q5 || ''}
                          onChange={(e) => setQuizAnswers({...quizAnswers, q5: e.target.value})}
                        >
                          <FormControlLabel value="minimum" control={<Radio />} label="Pay minimum on all debts" />
                          <FormControlLabel value="extra" control={<Radio />} label="Pay extra on one debt while minimums on others (Correct)" />
                          <FormControlLabel value="ignore" control={<Radio />} label="Ignore small debts" />
                          <FormControlLabel value="wait" control={<Radio />} label="Wait until you have more money" />
                        </RadioGroup>
                      </Box>

                      <Button
                        variant="contained"
                        size="large"
                        fullWidth
                        onClick={() => {
                          // Calculate score
                          const correctAnswers = {
                            q1: '20',
                            q2: 'smallest',
                            q3: '6',
                            q4: '700-850',
                            q5: 'extra'
                          };
                          let score = 0;
                          Object.keys(correctAnswers).forEach(key => {
                            if (quizAnswers[key] === correctAnswers[key]) {
                              score += 20;
                            }
                          });
                          setQuizScore(score);
                        }}
                        disabled={Object.keys(quizAnswers).length < 5}
                      >
                        Submit Quiz
                      </Button>
                    </Box>
                  ) : (
                    <Box textAlign="center">
                      <Box mb={3}>
                        <Typography variant="h2" color={quizScore >= 80 ? 'success.main' : quizScore >= 60 ? 'warning.main' : 'error.main'}>
                          {quizScore}%
                        </Typography>
                        <Typography variant="h6" gutterBottom>
                          {quizScore >= 80 ? 'Excellent!' : quizScore >= 60 ? 'Good Job!' : 'Keep Learning!'}
                        </Typography>
                      </Box>

                      {quizScore >= 80 && (
                        <Alert severity="success" sx={{ mb: 2 }}>
                          Outstanding! You have a strong understanding of financial basics. Keep up the great work!
                        </Alert>
                      )}

                      {quizScore >= 60 && quizScore < 80 && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                          Good effort! Review the educational resources to strengthen your financial knowledge.
                        </Alert>
                      )}

                      {quizScore < 60 && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                          There's room for improvement. We recommend going through our financial basics course.
                        </Alert>
                      )}

                      <Button
                        variant="outlined"
                        onClick={() => {
                          setQuizScore(null);
                          setQuizAnswers({});
                        }}
                      >
                        Retake Quiz
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Achievement Badges */}
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={3}>
                    <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                      <AchievementIcon />
                    </Avatar>
                    <Typography variant="h6">
                      Your Achievements
                    </Typography>
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper', border: '2px solid', borderColor: 'success.main' }}>
                        <AchievementIcon sx={{ fontSize: 48, color: 'success.dark', mb: 1 }} />
                        <Typography variant="body2" fontWeight="bold">
                          First Payment
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Made your first payment
                        </Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper', border: '2px solid', borderColor: 'info.main' }}>
                        <EducationIcon sx={{ fontSize: 48, color: 'info.dark', mb: 1 }} />
                        <Typography variant="body2" fontWeight="bold">
                          Financial Scholar
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Completed quiz with 80%+
                        </Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'background.paper', border: '2px solid', borderColor: 'primary.main' }}>
                        <BudgetIcon sx={{ fontSize: 48, color: 'primary.dark', mb: 1 }} />
                        <Typography variant="body2" fontWeight="bold">
                          Budget Master
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Used budget calculator
                        </Typography>
                      </Paper>
                    </Grid>

                    <Grid item xs={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'grey.300', opacity: 0.6 }}>
                        <GrowthIcon sx={{ fontSize: 48, color: 'grey.600', mb: 1 }} />
                        <Typography variant="body2" fontWeight="bold">
                          Debt Free
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Clear all outstanding debt
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>

                  <Box mt={3} textAlign="center">
                    <Typography variant="body2" color="text.secondary">
                      Earn more badges by completing payments and learning modules!
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={paymentDialog} onClose={() => setPaymentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Make a Payment</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Choose how you'd like to pay your outstanding balance
          </Alert>

          <FormControl component="fieldset" fullWidth>
            <FormLabel component="legend">Payment Type</FormLabel>
            <RadioGroup value={paymentType} onChange={(e) => setPaymentType(e.target.value)}>
              <FormControlLabel
                value="full"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">Full Payment</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pay entire balance: ${mockDebtorAccount.outstandingBalance.toLocaleString()}
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="settlement"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">Settlement Amount</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pay settlement offer: ${mockDebtorAccount.settlementOffer.settlementAmount.toLocaleString()}
                    </Typography>
                  </Box>
                }
                disabled={!mockDebtorAccount.settlementOffer.available}
              />
              <FormControlLabel
                value="minimum"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="body1">Minimum Payment</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Pay minimum: ${mockDebtorAccount.minimumPayment.toLocaleString()}
                    </Typography>
                  </Box>
                }
              />
              <FormControlLabel
                value="custom"
                control={<Radio />}
                label="Custom Amount"
              />
            </RadioGroup>
          </FormControl>

          {paymentType === 'custom' && (
            <TextField
              fullWidth
              label="Enter Amount"
              type="number"
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              InputProps={{ startAdornment: '$' }}
              sx={{ mt: 2 }}
            />
          )}

          {(paymentType === 'settlement' || paymentType === 'full') && (
            <Box sx={{ mt: 3 }}>
              <FormControl component="fieldset" fullWidth>
                <FormLabel component="legend">Payment Plan</FormLabel>
                <RadioGroup value={installmentPlan} onChange={(e) => setInstallmentPlan(e.target.value)}>
                  <FormControlLabel
                    value="1"
                    control={<Radio />}
                    label="One-time payment (Lump sum)"
                  />
                  <FormControlLabel
                    value="3"
                    control={<Radio />}
                    label={`3 monthly installments (${calculateInstallment(
                      paymentType === 'settlement'
                        ? mockDebtorAccount.settlementOffer.settlementAmount
                        : mockDebtorAccount.outstandingBalance,
                      3
                    )} per month)`}
                  />
                  <FormControlLabel
                    value="6"
                    control={<Radio />}
                    label={`6 monthly installments (${calculateInstallment(
                      paymentType === 'settlement'
                        ? mockDebtorAccount.settlementOffer.settlementAmount
                        : mockDebtorAccount.outstandingBalance,
                      6
                    )} per month)`}
                  />
                </RadioGroup>
              </FormControl>
            </Box>
          )}

          <Alert severity="warning" sx={{ mt: 3 }}>
            You will be redirected to a secure payment gateway to complete your payment
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPaymentDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleMakePayment}>
            Proceed to Payment
          </Button>
        </DialogActions>
      </Dialog>

      {/* Settlement Dialog */}
      <Dialog open={settlementDialog} onClose={() => setSettlementDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Settlement Offer Details</DialogTitle>
        <DialogContent>
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight="bold">
              Limited Time Offer!
            </Typography>
            <Typography variant="body2">
              This settlement offer is valid until {mockDebtorAccount.settlementOffer.validUntil}
            </Typography>
          </Alert>

          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Current Balance</Typography>
              <Typography variant="h6" color="error.main">
                ${mockDebtorAccount.outstandingBalance.toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Settlement Amount</Typography>
              <Typography variant="h6" color="success.main">
                ${mockDebtorAccount.settlementOffer.settlementAmount.toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Discount</Typography>
              <Typography variant="h6" color="primary.main">
                {mockDebtorAccount.settlementOffer.discountPercent}%
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">You Save</Typography>
              <Typography variant="h6" color="success.main">
                ${(mockDebtorAccount.outstandingBalance - mockDebtorAccount.settlementOffer.settlementAmount).toLocaleString()}
              </Typography>
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Typography variant="subtitle2" gutterBottom>
            Payment Options
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {mockDebtorAccount.settlementOffer.terms}
          </Typography>

          <Alert severity="info">
            <Typography variant="body2">
              By accepting this settlement, you agree to pay the settlement amount and the account will be marked as "Settled" on your credit report.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettlementDialog(false)}>Maybe Later</Button>
          <Button variant="contained" onClick={handleAcceptSettlement}>
            Accept & Pay Now
          </Button>
        </DialogActions>
      </Dialog>

      {/* Not Ready to Pay Dialog */}
      <Dialog open={notReadyDialog} onClose={() => setNotReadyDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Not Ready to Pay?</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            We understand. Let us know when you'll be ready and we'll follow up with you then.
          </Alert>

          <Typography variant="subtitle2" gutterBottom>
            When do you expect to be ready?
          </Typography>
          <Box sx={{ px: 2, mb: 3 }}>
            <Slider
              value={deferralMonths}
              onChange={(e, v) => setDeferralMonths(v)}
              min={1}
              max={12}
              marks
              valueLabelDisplay="on"
              valueLabelFormat={(value) => `${value} month${value > 1 ? 's' : ''}`}
            />
          </Box>

          <TextField
            fullWidth
            label="Additional Information (Optional)"
            multiline
            rows={3}
            placeholder="Tell us about your situation..."
            sx={{ mb: 2 }}
          />

          <Alert severity="warning">
            <Typography variant="body2">
              Please note: Interest and fees may continue to accrue during this period.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotReadyDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleNotReady}>
            Submit Request
          </Button>
        </DialogActions>
      </Dialog>

      {/* Update Contact Information Dialog */}
      <Dialog open={updateContactDialog} onClose={() => setUpdateContactDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Update Contact Information</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3, mt: 2 }}>
            <Typography variant="body2">
              For security purposes, you need to verify each change with an OTP sent to your new contact information.
            </Typography>
          </Alert>

          <Grid container spacing={3}>
            {/* Phone Number Update */}
            <Grid item xs={12}>
              <Divider sx={{ mb: 2 }}>
                <Chip label="Phone Number" />
              </Divider>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Current Phone: <strong>{contactData.phone}</strong>
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Phone Number"
                value={newPhone}
                onChange={(e) => {
                  setNewPhone(e.target.value);
                  setPhoneOTPSent(false);
                  setPhoneVerified(false);
                }}
                placeholder="+1-555-0000"
                disabled={phoneVerified}
                InputProps={{
                  endAdornment: phoneVerified && (
                    <InputAdornment position="end">
                      <CheckIcon color="success" />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>

            {!phoneVerified && newPhone !== contactData.phone && (
              <>
                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={handleSendPhoneOTP}
                    disabled={!newPhone || phoneOTPSent}
                    startIcon={<SendIcon />}
                  >
                    {phoneOTPSent ? 'OTP Sent' : 'Send OTP to New Phone'}
                  </Button>
                </Grid>

                {phoneOTPSent && (
                  <>
                    <Grid item xs={12} sm={8}>
                      <TextField
                        fullWidth
                        label="Enter OTP"
                        value={phoneOTP}
                        onChange={(e) => setPhoneOTP(e.target.value)}
                        placeholder=""
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Button
                        variant="contained"
                        fullWidth
                        onClick={handleVerifyPhoneOTP}
                        disabled={!phoneOTP}
                        sx={{ height: '56px' }}
                      >
                        Verify
                      </Button>
                    </Grid>
                  </>
                )}
              </>
            )}

            {phoneVerified && (
              <Grid item xs={12}>
                <Alert severity="success">
                  Phone number verified successfully!
                </Alert>
              </Grid>
            )}

            {/* Email Address Update */}
            <Grid item xs={12} sx={{ mt: 2 }}>
              <Divider sx={{ mb: 2 }}>
                <Chip label="Email Address" />
              </Divider>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Current Email: <strong>{contactData.email}</strong>
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Email Address"
                type="email"
                value={newEmail}
                onChange={(e) => {
                  setNewEmail(e.target.value);
                  setEmailOTPSent(false);
                  setEmailVerified(false);
                }}
                placeholder="email@example.com"
                disabled={emailVerified}
                InputProps={{
                  endAdornment: emailVerified && (
                    <InputAdornment position="end">
                      <CheckIcon color="success" />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>

            {!emailVerified && newEmail !== contactData.email && (
              <>
                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={handleSendEmailOTP}
                    disabled={!newEmail || emailOTPSent}
                    startIcon={<SendIcon />}
                  >
                    {emailOTPSent ? 'OTP Sent' : 'Send OTP to New Email'}
                  </Button>
                </Grid>

                {emailOTPSent && (
                  <>
                    <Grid item xs={12} sm={8}>
                      <TextField
                        fullWidth
                        label="Enter OTP"
                        value={emailOTP}
                        onChange={(e) => setEmailOTP(e.target.value)}
                        placeholder="654321"
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <Button
                        variant="contained"
                        fullWidth
                        onClick={handleVerifyEmailOTP}
                        disabled={!emailOTP}
                        sx={{ height: '56px' }}
                      >
                        Verify
                      </Button>
                    </Grid>
                  </>
                )}
              </>
            )}

            {emailVerified && (
              <Grid item xs={12}>
                <Alert severity="success">
                  Email address verified successfully!
                </Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdateContactDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveContactInfo}
            disabled={
              (!phoneVerified || newPhone === contactData.phone) &&
              (!emailVerified || newEmail === contactData.email)
            }
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DebtorPortal;
