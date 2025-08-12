/**
 * SqlModal
 * Modal dialog for editing SQL code with Monaco editor and save/cancel actions.
 *
 * Props:
 *   open (boolean): Whether the modal is open
 *   handleClose (function): Function to close the modal
 *   initialSQL (string): Initial SQL code to display
 *   onSQLUpdate (function): Callback to update SQL code
 */
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
    <Modal open={open} onClose={handleClose} aria-labelledby="sql-modal-title" aria-describedby="sql-modal-description">
      <Box sx={modalStyle}>
        <Typography id="sql-modal-title" variant="h6" sx={{ mb: 2 }}>
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
          <Button variant="outlined" onClick={handleClose} sx={{ mr: 2 }} aria-label="Cancel editing SQL">
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave} aria-label="Save SQL changes">
            Save
          </Button>
        </Box>
      </Box>
    </Modal>
  );
}

export default SqlModal;
