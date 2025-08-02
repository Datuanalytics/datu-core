import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '@src/App';
import { waitFor } from '@testing-library/react';
import axios from 'axios';

// Mock Axios to avoid network errors
jest.mock('axios', () => ({
  post: jest.fn(() =>
    Promise.resolve({
      data: {
        queries: [],
        assistant_response: 'Mocked response',
      },
    })
  ),
}));

describe('App Component', () => {
    test('renders FrontPage initially', () => {
      render(<App />);
      const frontPageElement = screen.getByText(/Meet AI Analyst, your data assistant/i);
      expect(frontPageElement).toBeInTheDocument();
    });

    test('renders ChatPanel after starting', async () => {
    render(<App />);

    // Find the input and "Send" button in FrontPage
    const input = screen.getByPlaceholderText(/Ask a question about your data.../i);
    const sendButton = screen.getByRole('button', { name: /Send/i });

    // Simulate entering a question and clicking "Send"
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    // Wait for the FrontPage to be removed and ChatPanel to appear
    const chatPanelElement = await waitFor(() => screen.getByTestId('chat-panel-container'));
    expect(chatPanelElement).toBeInTheDocument();
    });
  });