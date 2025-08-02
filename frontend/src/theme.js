// src/theme.js
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      dark: '#0E253E',
      main: '#23395B',
      light: '#4C6F91',
    },
    background: {
      default: '#F9FAFB',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#111827',
      secondary: '#6B7280',
    },
    // Custom additions
    userBubble: '#E5ECF9', // Color for user's chat bubble
    chartColors: [
      '#5C7285',
      '#A7B49E',
      '#818C78',
      '#E2E0C8',
      '#332E3C',
      '#F95D6A',
      '#FF7C43',
      '#FFA600',
      '#00876C',
      '#8FBC8F',
    ],
  },
  typography: {
    fontFamily: 'Segoe UI',
    h4: { fontSize: '1.75rem', fontWeight: 600 },
    h5: { fontSize: '1.5rem', fontWeight: 600 },
    h6: { fontSize: '1.25rem', fontWeight: 600 },
    subtitle1: { fontSize: '1rem', fontWeight: 500 },
    body1: { fontSize: '0.95rem' },
    body2: { fontSize: '0.85rem' },
  },
});

export default theme;
