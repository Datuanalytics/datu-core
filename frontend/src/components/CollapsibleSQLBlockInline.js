// src/components/CollapsibleSQLBlockInline.js
import React, { useState } from 'react';
import { Box, Button } from '@mui/material';

const CollapsibleSQLBlockInline = ({ code }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);

  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    alert('Code copied to clipboard!');
  };

  return (
    <Box
      component="span"
      sx={{
        display: 'inline-block',
        mx: 1,
        border: '1px dashed #ccc',
        borderRadius: 1,
        p: 0.5,
        verticalAlign: 'middle',
      }}
    >
      <Button onClick={toggleCollapse} size="small">
        {isCollapsed ? 'Show Code' : 'Hide Code'}
      </Button>
      {!isCollapsed && (
        <Box sx={{ mt: 1 }}>
          <pre style={{ maxWidth: '100%', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
            <code>{code}</code>
          </pre>
          <Button onClick={handleCopy} size="small">
            Copy
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default CollapsibleSQLBlockInline;
