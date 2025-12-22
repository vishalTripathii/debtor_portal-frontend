import React from 'react';
import { Box, Typography, Paper, LinearProgress } from '@mui/material';
import { Build as BuildIcon, Schedule as ScheduleIcon } from '@mui/icons-material';
import { useLanguage } from '../context/LanguageContext';

const MaintenancePage = ({ title, message, estimatedTime }) => {
  const { t, language } = useLanguage();

  const defaultTitle = language === 'th'
    ? 'ระบบอยู่ระหว่างการปรับปรุง'
    : 'System Under Maintenance';

  const defaultMessage = language === 'th'
    ? 'เรากำลังปรับปรุงระบบเพื่อให้บริการคุณได้ดียิ่งขึ้น กรุณากลับมาใหม่ในภายหลัง ขออภัยในความไม่สะดวก'
    : 'We are currently performing scheduled maintenance to serve you better. Please check back later. We apologize for any inconvenience.';

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a237e 0%, #0d47a1 50%, #01579b 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated background elements */}
      <Box
        sx={{
          position: 'absolute',
          top: '10%',
          left: '5%',
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.05)',
          animation: 'float 6s ease-in-out infinite',
          '@keyframes float': {
            '0%, 100%': { transform: 'translateY(0px)' },
            '50%': { transform: 'translateY(-30px)' },
          },
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: '15%',
          right: '10%',
          width: 200,
          height: 200,
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.03)',
          animation: 'float 8s ease-in-out infinite',
          animationDelay: '1s',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          right: '25%',
          width: 150,
          height: 150,
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.04)',
          animation: 'float 7s ease-in-out infinite',
          animationDelay: '2s',
        }}
      />

      <Paper
        elevation={24}
        sx={{
          maxWidth: 600,
          width: '90%',
          p: { xs: 4, md: 6 },
          textAlign: 'center',
          borderRadius: 4,
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(10px)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Top accent bar */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 6,
            background: 'linear-gradient(90deg, #ff9800, #f57c00, #ff9800)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 2s linear infinite',
            '@keyframes shimmer': {
              '0%': { backgroundPosition: '200% 0' },
              '100%': { backgroundPosition: '-200% 0' },
            },
          }}
        />

        {/* Logo */}
        <Box sx={{ mb: 4 }}>
          <img
            src="/poweramclogo.avif"
            alt="PowerAMC Logo"
            style={{
              height: 80,
              objectFit: 'contain',
            }}
          />
        </Box>

        {/* Animated icon */}
        <Box
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 100,
            height: 100,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #ff9800, #f57c00)',
            mb: 4,
            boxShadow: '0 8px 32px rgba(255, 152, 0, 0.3)',
            animation: 'pulse 2s ease-in-out infinite',
            '@keyframes pulse': {
              '0%, 100%': { transform: 'scale(1)', boxShadow: '0 8px 32px rgba(255, 152, 0, 0.3)' },
              '50%': { transform: 'scale(1.05)', boxShadow: '0 12px 48px rgba(255, 152, 0, 0.4)' },
            },
          }}
        >
          <BuildIcon
            sx={{
              fontSize: 50,
              color: 'white',
              animation: 'rotate 4s linear infinite',
              '@keyframes rotate': {
                '0%': { transform: 'rotate(0deg)' },
                '25%': { transform: 'rotate(-15deg)' },
                '75%': { transform: 'rotate(15deg)' },
                '100%': { transform: 'rotate(0deg)' },
              },
            }}
          />
        </Box>

        {/* Title */}
        <Typography
          variant="h4"
          fontWeight="bold"
          color="text.primary"
          gutterBottom
          sx={{ mb: 2 }}
        >
          {title || defaultTitle}
        </Typography>

        {/* Message */}
        <Typography
          variant="body1"
          color="text.secondary"
          sx={{ mb: 4, lineHeight: 1.8, px: 2 }}
        >
          {message || defaultMessage}
        </Typography>

        {/* Progress indicator */}
        <Box sx={{ mb: 4, px: 4 }}>
          <LinearProgress
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(255, 152, 0, 0.2)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                background: 'linear-gradient(90deg, #ff9800, #f57c00)',
                animation: 'indeterminate 1.5s ease-in-out infinite',
              },
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {language === 'th' ? 'กำลังดำเนินการ...' : 'Work in progress...'}
          </Typography>
        </Box>

        {/* Estimated time */}
        {estimatedTime && (
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 1,
              px: 3,
              py: 1.5,
              bgcolor: 'primary.50',
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'primary.200',
            }}
          >
            <ScheduleIcon color="primary" fontSize="small" />
            <Typography variant="body2" color="primary.main" fontWeight="500">
              {language === 'th' ? 'เวลาโดยประมาณ: ' : 'Estimated return: '}
              {estimatedTime}
            </Typography>
          </Box>
        )}

        {/* Footer */}
        <Box sx={{ mt: 5, pt: 3, borderTop: '1px solid', borderColor: 'divider' }}>
          <Typography variant="body2" color="text.secondary">
            {language === 'th'
              ? 'ขอบคุณที่เข้าใจและรอคอย'
              : 'Thank you for your patience and understanding.'}
          </Typography>
        </Box>
      </Paper>

      {/* Bottom wave decoration */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 100,
          background: 'linear-gradient(180deg, transparent, rgba(0,0,0,0.2))',
        }}
      />
    </Box>
  );
};

export default MaintenancePage;
