import React from 'react';
import { Button, ButtonGroup, Box, Typography } from '@mui/material';
import { Language as LanguageIcon } from '@mui/icons-material';
import { useLanguage } from '../context/LanguageContext';

const LanguageSwitcher = ({ variant = 'default', size = 'small' }) => {
  const { language, setLanguage, t } = useLanguage();

  if (variant === 'minimal') {
    return (
      <Button
        size={size}
        onClick={() => setLanguage(language === 'en' ? 'th' : 'en')}
        startIcon={<LanguageIcon />}
        sx={{
          color: 'inherit',
          minWidth: 'auto',
          textTransform: 'none',
        }}
      >
        {language === 'en' ? 'TH' : 'EN'}
      </Button>
    );
  }

  if (variant === 'outlined-white') {
    return (
      <ButtonGroup size={size} variant="outlined">
        <Button
          onClick={() => setLanguage('en')}
          sx={{
            bgcolor: language === 'en' ? 'rgba(255,255,255,0.2)' : 'transparent',
            color: 'white',
            borderColor: 'rgba(255,255,255,0.5)',
            '&:hover': {
              bgcolor: 'rgba(255,255,255,0.3)',
              borderColor: 'white',
            },
          }}
        >
          EN
        </Button>
        <Button
          onClick={() => setLanguage('th')}
          sx={{
            bgcolor: language === 'th' ? 'rgba(255,255,255,0.2)' : 'transparent',
            color: 'white',
            borderColor: 'rgba(255,255,255,0.5)',
            '&:hover': {
              bgcolor: 'rgba(255,255,255,0.3)',
              borderColor: 'white',
            },
          }}
        >
          TH
        </Button>
      </ButtonGroup>
    );
  }

  // Default variant
  return (
    <Box display="flex" alignItems="center" gap={1}>
      <LanguageIcon fontSize="small" color="action" />
      <ButtonGroup size={size} variant="outlined">
        <Button
          onClick={() => setLanguage('en')}
          variant={language === 'en' ? 'contained' : 'outlined'}
          sx={{ minWidth: 40 }}
        >
          EN
        </Button>
        <Button
          onClick={() => setLanguage('th')}
          variant={language === 'th' ? 'contained' : 'outlined'}
          sx={{ minWidth: 40 }}
        >
          TH
        </Button>
      </ButtonGroup>
    </Box>
  );
};

export default LanguageSwitcher;
