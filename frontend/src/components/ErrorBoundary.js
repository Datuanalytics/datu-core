// src/components/ErrorBoundary.js
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render shows fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // Log error details.
    console.error('Error caught in ErrorBoundary:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return <h2>Something went wrong with the visualizations.</h2>;
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
