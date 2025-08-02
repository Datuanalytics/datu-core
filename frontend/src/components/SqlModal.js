// src/components/SqlModal.js
import React, { useState } from 'react';
import { Modal, Box, Typography, Button } from '@mui/material';
import MonacoEditor from 'react-monaco-editor';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '70%',
  maxHeight: '80%',
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 3,
  overflowY: 'auto',
};

function SqlModal({ open, handleClose, initialSQL, onSQLUpdate }) {
  const [sql, setSQL] = useState(initialSQL);

  const handleSave = () => {
    onSQLUpdate(sql);
  };

  return (
    <Modal open={open} onClose={handleClose}>
      <Box sx={modalStyle}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Edit SQL
        </Typography>
        <MonacoEditor
          width="100%"
          height="300"
          language="sql"
          theme="vs-light"
          value={sql}
          onChange={(val) => setSQL(val)}
          options={{ automaticLayout: true }}
        />
        <Box sx={{ textAlign: 'right', mt: 2 }}>
          <Button variant="outlined" onClick={handleClose} sx={{ mr: 2 }}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave}>
            Save
          </Button>
        </Box>
      </Box>
    </Modal>
  );
}

export default SqlModal;
