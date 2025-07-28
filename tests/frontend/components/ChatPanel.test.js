import React from 'react';
import { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ChatPanel from '@src/components/ChatPanel';
import { act } from '@testing-library/react';

// Mock Material-UI components
jest.mock('@mui/material', () => ({
  ...jest.requireActual('@mui/material'),
  Box: (props) => <div {...props} />,
  Typography: (props) => <div {...props} />,
  IconButton: (props) => <button {...props} />,
  InputBase: (props) => <input {...props} />,
  CircularProgress: () => <div>Loading...</div>,
}));

// Mock Material-UI styles
jest.mock('@mui/material/styles', () => ({
  useTheme: () => ({
    palette: {
      userBubble: '#E5ECF9',
    },
  }),
  styled: () => (component) => component,
  createTheme: () => ({}),
}));

// Mock Axios
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

// Mock CollapsibleSQLBlockInline
jest.mock('@src/components/CollapsibleSQLBlockInline', () => () => (
  <div>Mocked SQL Block</div>
));

describe('ChatPanel Component', () => {
    const setQueries = jest.fn();
    const onNewQuery = jest.fn();
    const setConversation = jest.fn();
  
    // Test to verify that the ChatPanel component renders without crashing.
    test('renders ChatPanel component', async () => {
      await act(async () => {
        render(
          <ChatPanel
            setQueries={setQueries}
            onNewQuery={onNewQuery}
            conversation={[]} // Provide an empty conversation array
            setConversation={setConversation}
          />
        );
      });
      const chatPanelElement = screen.getByTestId('chat-panel');
      expect(chatPanelElement).toBeInTheDocument();
    });
  
    // Test to check if the initial user message is displayed when provided as a prop.
    test('renders conversation messages', async () => {
        const conversation = [
          { role: 'user', content: 'Hello, this is a test message!' },
          { role: 'assistant', content: 'This is a response.' },
        ];
      
        render(
          <ChatPanel
            setQueries={jest.fn()}
            onNewQuery={jest.fn()}
            conversation={conversation}
            setConversation={jest.fn()}
          />
        );
      
        // Verify that both messages are rendered
        expect(screen.getByText('Hello, this is a test message!')).toBeInTheDocument();
        expect(screen.getByText('This is a response.')).toBeInTheDocument();
      });
  
    // Test to ensure that user input is handled correctly and the send button triggers the appropriate actions.
    test('handles user input and send button click', async () => {
      await act(async () => {
        render(
          <ChatPanel
            setQueries={setQueries}
            onNewQuery={onNewQuery}
            conversation={[]} // Provide an empty conversation array
            setConversation={setConversation}
          />
        );
      });
  
      const input = screen.getByPlaceholderText('Ask anything...');
      const sendButton = screen.getByRole('button');
  
      await act(async () => {
        fireEvent.change(input, { target: { value: 'Test message' } });
        fireEvent.click(sendButton);
      });
  
      expect(setQueries).toHaveBeenCalled();
    });
  });