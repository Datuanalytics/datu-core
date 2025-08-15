/**
 * index.js
 * Entry point for the React application. Wraps the App in the MUI ThemeProvider.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider } from '@mui/material/styles';
import App from './App';
import theme from './theme'; // import our custom theme

// Create the root and render the App with theme
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <ThemeProvider theme={theme}>
    <App />
  </ThemeProvider>
);
