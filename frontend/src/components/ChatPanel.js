/**
 * ChatPanel
 * Main chat interface for user/assistant conversation, message sending, and SQL block rendering.
 *
 * Props:
 *   setQueries (func): Callback to set queries
 *   initialUserMessage (string): Initial user message
 *   onNewQuery (func): Callback for new query
 *   conversation (array): Conversation history
 *   setConversation (func): Setter for conversation
 *   selectedQueryIndices (array): Selected query indices
 *   setSelectedQueryIndices (func): Setter for selected query indices
 */
import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, IconButton, InputBase, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import axios from 'axios';
import { useTheme } from '@mui/material/styles';
import CollapsibleSQLBlockInline from './CollapsibleSQLBlockInline';

let ID_TITLE = 0; // Initialize ID_TITLE for unique query identification

function ChatPanel({ setQueries, initialUserMessage, onNewQuery, conversation, setConversation, selectedQueryIndices, setSelectedQueryIndices }) {
  const theme = useTheme();
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatContainerRef = useRef(null);

  // When the component mounts (or initialUserMessage changes), if provided, prepend the user message.
  useEffect(() => {
    if (initialUserMessage && conversation.length === 0) {
      const userMsg = { role: 'user', content: initialUserMessage };
  
      // Use a local variable to ensure the correct conversation is passed
      const updatedConversation = [userMsg];
      setConversation(updatedConversation);
      sendMessageWithAPI(updatedConversation); // Use the local variable
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialUserMessage]);

  // Auto-scroll to bottom when conversation changes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [conversation, isTyping]);

  // Helper to generate a unique query ID.
  const generateQueryId = () =>
    `query-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Combined sendMessageWithAPI: processes backend response.
  const sendMessageWithAPI = async (conv) => {
    setIsTyping(true);
    try {
      const response = await axios.post('/api/chat/', { messages: conv });
      const data = response.data;

      // Process queries from the assistant's response.
      function parseTitle(rawText) {
        // 1) Try “Query name: …”
        const queryRx = /Query\s*name\s*:\s*([^\n]+)/i;
        let match = rawText.match(queryRx);
        if (match) {
          return match[1].trim();
        }
      
        // 2) Otherwise look for “<number>. **Title**:” on any line
        const numberedBoldRx = /^\s*\d+\.\s*\*\*([^*]+)\*\*\s*:/m;
        match = rawText.match(numberedBoldRx);
        if (match) {
          return match[1].trim();
        }
      
        // 3) Fallback: just return the whole trimmed text
        return rawText.trim();
      }
      
      // assume ID_TITLE starts at 0 (or whatever your current counter is)
      const sanitizedQueries = (data.queries || []).map((q) => {
        const hasSql = typeof q.sql === 'string' && q.sql.trim() !== '';
        
        // decide on title:
        let title = q.title
        if (typeof q.rawText === 'string' && title === null) {
          title = parseTitle(q.rawText);
        } else if (hasSql && title === null) {
          // bump the counter *and* use the new value
          title = `Query ${++ID_TITLE}`;
        }
        return {
          ...q,
          title,
          sql: hasSql ? q.sql : '',
          id: q.id || generateQueryId(),
          active: q.active !== undefined ? q.active : true,
          createdAt: Date.now(),
        };
      });

      // Prepend new queries.
      setQueries((prevQueries) => {
        const newQueries = [...sanitizedQueries, ...prevQueries];
        // After updating queries, select all new queries (indices 0..N-1)
        if (sanitizedQueries.length > 0 && setSelectedQueryIndices) {
          setSelectedQueryIndices(Array.from({ length: sanitizedQueries.length }, (_, i) => i));
        }
        return newQueries;
      });

      // Notify parent that a new query was added.
      onNewQuery && onNewQuery();

      // Append the assistant's message.
      setConversation((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.assistant_response || '',
          sqlCode: typeof data.sql === 'string' ? data.sql : '',
        },
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  // sendMessage: triggered when the user sends a new message.
  const sendMessage = async () => {
    if (!message.trim()) return;
    const userMessage = { role: 'user', content: message.trim() };
    const newConv = [...conversation, userMessage];
    setConversation(newConv);
    setMessage('');
    await sendMessageWithAPI(newConv);
  };

  // Helper to parse assistant's message for inline SQL code blocks.
  const renderAssistantMessage = (content) => {
    const regex = /```(?:sql)?([\s\S]*?)```/g;
    const elements = [];
    let lastIndex = 0;
    let match;
    let key = 0;
    while ((match = regex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        elements.push(<span key={key++}>{content.substring(lastIndex, match.index)}</span>);
      }
      const codeText = match[1].trim();
      elements.push(<CollapsibleSQLBlockInline key={key++} code={codeText} />);
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < content.length) {
      elements.push(<span key={key++}>{content.substring(lastIndex)}</span>);
    }
    return elements;
  };

  return (
    <Box 
    data-testid="chat-panel"
    sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Scrollable conversation area */}
      <Box
        ref={chatContainerRef}
        sx={{ flex: 1, overflowY: 'auto', p: 2 }}
      >
        {conversation.map((msg, idx) => {
          const isUser = msg.role === 'user';
          return (
            <Box
              key={idx}
              sx={{
                mb: 1.5,
                p: 1.5,
                borderRadius: 2,
                bgcolor: isUser ? theme.palette.userBubble : 'grey.200',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                ml: isUser ? 'auto' : 0,
                mr: isUser ? 0 : 'auto',
                maxWidth: '80%',
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                {isUser ? 'You' : 'Assistant'}
              </Typography>
              <Typography variant="body2" style={{ whiteSpace: 'pre-line' }}>
                {msg.role === 'assistant'
                  ? renderAssistantMessage(msg.content)
                  : msg.content}
              </Typography>
            </Box>
          );
        })}

        {/* Typing indicator */}
        {isTyping && (
          <Box
            sx={{
              mb: 1.5,
              p: 1.5,
              borderRadius: 2,
              bgcolor: 'grey.200',
              alignSelf: 'flex-start',
              maxWidth: '80%',
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
              Assistant
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2">Typing...</Typography>
            </Box>
          </Box>
        )}
      </Box>

      {/* Input area pinned at the bottom */}
      <Box
        sx={{
          borderTop: '1px solid #e5e7eb',
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#fff',
            borderRadius: 4,
            border: '1px solid #ddd',
            px: 2,
          }}
        >
          <InputBase
            sx={{ flex: 1 }}
            placeholder="Ask anything..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault();
              }
            }}
            disabled={isTyping}
          />
        </Box>
        <IconButton
          onClick={sendMessage}
          disabled={isTyping}
          aria-label="Send"
          sx={{
            bgcolor: 'primary.main',
            color: '#fff',
            '&:hover': { bgcolor: 'primary.dark' },
            borderRadius: '50%',
            width: 25,
            height: 25,
          }}
        >
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  );
}

export default ChatPanel;
