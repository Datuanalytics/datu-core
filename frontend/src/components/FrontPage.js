// src/components/FrontPage.jsx
import React, { useState } from 'react';
import { Box, Container, Typography, Card, CardContent, InputBase, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { Message } from '@mui/icons-material'; // Use appropriate icons

export default function FrontPage({ onStart }) {
  // Local state for the input value.
  const [inputValue, setInputValue] = useState('');
  
  const sampleQuestions = [
    "Generate a report about our company's financial situation",
    "Show me sales performance by product category for different months",
    "What were our top 5 performing products?"
  ];

  // When user submits (via form submission) we call onStart with the input value.
  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onStart(inputValue.trim());
    }
  };

  // When a sample question card is clicked, pass that text to onStart.
  const handleSampleClick = (question) => {
    onStart(question);
  };

  return (
    <Box>
      {/* The unified header is rendered globally (see App.js) so we remove any duplicate header here */}
      {/* Hero Section */}
      <Container maxWidth="md" sx={{ textAlign: 'center', mt: 8, mb: 8 }}>
        <Typography variant="h3" sx={{ fontWeight: 'bold', mb: 2 }}>
          Meet AI Analyst, your data assistant
        </Typography>
        <Typography variant="body1" sx={{ color: '#666', maxWidth: 600, mx: 'auto', mb: 4, lineHeight: 1.6 }}>
          AI Analyst can answer questions you have about your data source and help you find insights quickly.
          To start analyzing, ask a business question about your data.
        </Typography>

        {/* Sample Questions */}
        <Typography variant="body2" sx={{ color: '#888', mb: 1 }}>
          Sample questions (Business Data)
        </Typography>
        <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, mb: 6 }}>
          {sampleQuestions.map((question, idx) => (
            <Card key={idx} sx={{ textAlign: 'left', cursor: 'pointer' }} onClick={() => handleSampleClick(question)}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Message sx={{ fontSize: 20, color: '#5C7285' }} />
                <Typography variant="body2">{question}</Typography>
              </CardContent>
            </Card>
          ))}
        </Box>

        {/* Ask a Question Input */}
        <Box component="form" onSubmit={handleSubmit}
          sx={{
            display: 'flex',
            alignItems: 'center',
            maxWidth: 600,
            mx: 'auto',
            p: 1,
            border: '1px solid #ccc',
            borderRadius: '9999px'
          }}
        >
          <InputBase
            placeholder="Ask a question about your data..."
            sx={{ flex: 1, ml: 1 }}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <IconButton
            onClick={handleSubmit}
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
      </Container>
    </Box>
  );
}
