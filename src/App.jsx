import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import { ActivityLogProvider } from './context/ActivityLogContext';
import { LanguageProvider } from './context/LanguageContext';
import DebtorPortal from './components/DebtorPortal';
import AdminPortal from './components/AdminPortal';
import './index.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#e3f2fd',
    },
    secondary: {
      main: '#9c27b0',
    },
    error: {
      main: '#d32f2f',
    },
    success: {
      main: '#2e7d32',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h3: {
      fontWeight: 700,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 20px',
        },
        sizeLarge: {
          padding: '14px 28px',
          fontSize: '1rem',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        outlined: {
          borderRadius: 12,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 10,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          fontSize: '0.95rem',
          minHeight: 56,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          backgroundColor: '#fafafa',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 600,
          backgroundColor: '#f5f5f5',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LanguageProvider>
        <Router>
          <ActivityLogProvider>
            <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
              <Routes>
                <Route path="/" element={<DebtorPortal />} />
                <Route path="/admin" element={<AdminPortal />} />
              </Routes>
            </Box>
          </ActivityLogProvider>
        </Router>
      </LanguageProvider>
    </ThemeProvider>
  );
}

export default App;
