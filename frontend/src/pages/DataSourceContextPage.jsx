/**
 * DataSourceContextPage
 * Page for managing data sources, uploading context files, and editing domain knowledge for LLM context.
 *
 * Features:
 *   - List, add, update, and delete data sources (files and databases)
 *   - Upload, list, and delete context files
 *   - Edit domain knowledge and apply templates
 *   - Snackbar notifications for user feedback
 *   - Modal dialog for connecting databases
 */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import MenuItem from '@mui/material/MenuItem';
import {
  Box, Typography, Tabs, Tab, Card, CardContent, CardHeader,
  Button, Checkbox, TextField, Chip, LinearProgress, Divider, IconButton, Snackbar, Alert
} from '@mui/material';
import {
  fetchDataSources, updateDataSource, deleteDataSource, uploadDataSourceFile, addDatabaseSource
} from '../api/dataSources';
import {
  fetchContextFiles, uploadContextFile, deleteContextFile,
  fetchDomainKnowledge, updateDomainKnowledge, fetchTemplates, applyTemplate
} from '../api/llmContext';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import StorageIcon from '@mui/icons-material/Storage';
import DescriptionIcon from '@mui/icons-material/Description';
import ImageIcon from '@mui/icons-material/Image';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import PsychologyIcon from '@mui/icons-material/Psychology';
import HomeIcon from '@mui/icons-material/Home';

export default function DataSourceContextPage() {
  // --- Navigation and Tab State ---
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  // --- Data Sources State ---
  const [dataSources, setDataSources] = useState([]);
  const [selectedDataSources, setSelectedDataSources] = useState([]);
  const [dataSourceDragActive, setDataSourceDragActive] = useState(false);
  const dataSourceInputRef = useRef();

  // --- Context Files State ---
  const [contextFiles, setContextFiles] = useState([]);
  const [contextDragActive, setContextDragActive] = useState(false);
  const contextInputRef = useRef();
  const [domainContext, setDomainContext] = useState('');
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- Snackbar State ---
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // --- Domain Knowledge Save Status ---
  const [domainSaveStatus, setDomainSaveStatus] = useState('idle'); // idle | saving | saved | error

  // --- Connect Database Modal State ---
  const [dbModalOpen, setDbModalOpen] = useState(false);
  const [dbType, setDbType] = useState('postgres');
  const [dbForm, setDbForm] = useState({ host: '', port: '', user: '', password: '', database: '', schema: '' });
  const [dbError, setDbError] = useState('');
  const [dbLoading, setDbLoading] = useState(false);
  // --- Handlers for Database Modal ---
  // Handle changes in DB connection form fields
  const handleDbFormChange = (e) => {
    const { name, value } = e.target;
    setDbForm((prev) => ({ ...prev, [name]: value }));
    setDbError('');
  };

  // Handle changes in DB type dropdown
  const handleDbTypeChange = (e) => {
    setDbType(e.target.value);
    setDbError('');
  };

  // Attempt to connect to a database and add as a data source
  const handleDbConnect = async () => {
    // Validate required fields
    const required = ['host', 'port', 'user', 'password', 'database', 'schema'];
    for (const field of required) {
      if (!dbForm[field]) {
        setDbError('Please fill all fields.');
        return;
      }
    }
    setDbLoading(true);
    try {
      const payload = {
        type: 'database',
        dbType,
        ...dbForm,
        name: `${dbType === 'postgres' ? 'Postgres' : 'SQLServer'}:${dbForm.database}`,
        size: 'N/A',
        status: 'active',
        lastModified: 'just now',
      };
      const newSource = await addDatabaseSource(payload);
      setDataSources([...dataSources, newSource]);
      setSelectedDataSources([...selectedDataSources, newSource.id]);
      setSnackbarMessage(`Database ${payload.name} connected!`);
      setSnackbarOpen(true);
      setDbModalOpen(false);
      setDbForm({ host: '', port: '', user: '', password: '', database: '', schema: '' });
      setDbType('postgres');
    } catch (err) {
      setDbError('Failed to connect database.');
    }
    setDbLoading(false);
  };

  // --- Initial Data Fetching ---
  // Fetch data sources, context files, domain knowledge, and templates on mount
  useEffect(() => {
    setLoading(true);
    fetchDataSources().then((data) => {
      setDataSources(data);
      setSelectedDataSources(data.filter(ds => ds.status === 'active').map(ds => ds.id));
    });
    fetchContextFiles().then(setContextFiles);
    fetchDomainKnowledge().then(setDomainContext);
    fetchTemplates().then(setTemplates);
    setLoading(false);
  }, []);

  // --- Data Source Handlers ---
  // Toggle a data source's active/inactive status
  const handleToggleDataSource = async (id, newStatus) => {
    // Update local state immediately
    setDataSources((prev) => prev.map(ds => ds.id === id ? { ...ds, status: newStatus } : ds));
    setSelectedDataSources((prev) => newStatus === 'active'
      ? [...prev, id]
      : prev.filter((sourceId) => sourceId !== id)
    );
    // Call backend to update status
    try {
      await updateDataSource(id, { status: newStatus });
    } catch (err) {
      setSnackbarMessage('Failed to update status');
      setSnackbarOpen(true);
    }
  };
  // Delete a data source by id
  const handleDeleteDataSource = async (id) => {
    await deleteDataSource(id);
    setDataSources(dataSources.filter(ds => ds.id !== id));
    setSelectedDataSources(selectedDataSources.filter(sid => sid !== id));
  };
  // --- Drag-and-drop for Data Sources ---
  // Handle drag events for data source upload area
  const handleDataSourceDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDataSourceDragActive(true);
    } else if (e.type === 'dragleave') {
      setDataSourceDragActive(false);
    }
  };
  // Handle file drop for data source upload
  const handleDataSourceDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDataSourceDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setLoading(true);
      const file = e.dataTransfer.files[0];
      try {
        const newSource = await uploadDataSourceFile(file);
        setDataSources([...dataSources, newSource]);
        setSelectedDataSources([...selectedDataSources, newSource.id]);
      } catch (err) {
        setSnackbarMessage(`Failed to upload ${file.name}`);
        setSnackbarOpen(true);
      }
      setLoading(false);
      e.dataTransfer.clearData();
    }
  };
  // Trigger file input for data source upload
  const handleDataSourceBrowse = () => {
    if (dataSourceInputRef.current) {
      dataSourceInputRef.current.click();
    }
  };
  // Handle file selection for data source upload
  const handleDataSourceFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setLoading(true);
      try {
        const newSource = await uploadDataSourceFile(file);
        setDataSources([...dataSources, newSource]);
        setSelectedDataSources([...selectedDataSources, newSource.id]);
        setSnackbarMessage(`Uploaded ${file.name} successfully!`);
        setSnackbarOpen(true);
      } catch (err) {
        setSnackbarMessage(`Failed to upload ${file.name}`);
        setSnackbarOpen(true);
      }
      setLoading(false);
    }
  };

  // --- Context File Handlers ---
  // Delete a context file by id
  const handleDeleteContextFile = async (id) => {
    await deleteContextFile(id);
    setContextFiles(contextFiles.filter(cf => cf.id !== id));
  };
  // --- Drag-and-drop for Context Files ---
  // Handle drag events for context file upload area
  const handleContextDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setContextDragActive(true);
    } else if (e.type === 'dragleave') {
      setContextDragActive(false);
    }
  };
  // Handle file drop for context file upload
  const handleContextDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setContextDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setLoading(true);
      const file = e.dataTransfer.files[0];
      try {
        const newFile = await uploadContextFile({ name: file.name, type: 'pdf', size: `${(file.size/1024/1024).toFixed(2)} MB`, status: 'processing' });
        setContextFiles([...contextFiles, newFile]);
        setSnackbarMessage(`Uploaded ${file.name} successfully!`);
        setSnackbarOpen(true);
      } catch (err) {
        setSnackbarMessage(`Failed to upload ${file.name}`);
        setSnackbarOpen(true);
      }
      setLoading(false);
      e.dataTransfer.clearData();
    }
  };
  // Trigger file input for context file upload
  const handleContextBrowse = () => {
    contextInputRef.current.click();
  };
  // Handle file selection for context file upload
  const handleContextFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      setLoading(true);
      try {
        const newFile = await uploadContextFile({ name: file.name, type: 'pdf', size: `${(file.size/1024/1024).toFixed(2)} MB`, status: 'processing' });
        setContextFiles([...contextFiles, newFile]);
        setSnackbarMessage(`Uploaded ${file.name} successfully!`);
        setSnackbarOpen(true);
      } catch (err) {
        setSnackbarMessage(`Failed to upload ${file.name}`);
        setSnackbarOpen(true);
      }
      setLoading(false);
    }
  };

  // --- Domain Knowledge Handlers ---
  // Handle changes in domain knowledge text area
  const handleDomainContextChange = (e) => {
    setDomainContext(e.target.value);
    setDomainSaveStatus('idle');
  };

  // Save domain knowledge to backend
  const handleDomainSave = async () => {
    setDomainSaveStatus('saving');
    try {
      await updateDomainKnowledge({ text: domainContext });
      setDomainSaveStatus('saved');
      setSnackbarMessage('Domain knowledge saved');
      setSnackbarOpen(true);
    } catch (err) {
      setDomainSaveStatus('error');
      setSnackbarMessage('Failed to save domain knowledge');
      setSnackbarOpen(true);
    }
  };

  // --- Template Handlers ---
  // Apply a quick template to the domain knowledge text area
  const handleApplyTemplate = async (template) => {
    const result = await applyTemplate({ template });
    setDomainContext(result);
  };

  // --- Helper Functions ---
  // Return an icon component based on file type
  const getFileIcon = (type) => {
    switch (type) {
      case 'csv':
      case 'excel':
        return <StorageIcon fontSize="small" />;
      case 'pdf':
      case 'document':
        return <DescriptionIcon fontSize="small" />;
      case 'image':
        return <ImageIcon fontSize="small" />;
      case 'database':
        return <StorageIcon fontSize="small" />;
      default:
        return <DescriptionIcon fontSize="small" />;
    }
  };
  // Return a color string for a given status
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
      case 'ready':
        return 'success';
      case 'inactive':
        return 'default';
      case 'processing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 4, maxWidth: '1200px', mx: 'auto', position: 'relative' }}>
      {/* Home Button */}
      <Button
        variant="outlined"
        startIcon={<HomeIcon />}
        sx={{ mb: 2 }}
        onClick={() => navigate('/')}
      >
        Home
      </Button>
      {/* Loading Spinner Overlay */}
      {loading && (
        <Box sx={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', bgcolor: 'rgba(255,255,255,0.6)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <LinearProgress sx={{ width: '50%', height: 8, borderRadius: 4 }} />
        </Box>
      )}
      <Typography variant="h4" sx={{ mb: 2, fontWeight: 600 }}>
        LLM Configuration
      </Typography>
      <Typography variant="subtitle1" sx={{ mb: 4 }}>
        Set up your data sources and context to enhance your AI model's capabilities
      </Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} aria-label="Data Source & Context Tabs" sx={{ mb: 3 }}>
        <Tab label="Data Sources" />
        <Tab label="Context & Knowledge" />
      </Tabs>
      {tab === 0 && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 2fr' }, gap: 3 }}>
          {/* Upload Section */}
          <Card>
            <CardHeader title={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><CloudUploadIcon /><span>Upload Data</span></Box>} subheader="Add CSV, Excel files, or connect to databases" />
            <CardContent>
              <Box
                sx={{ border: '2px dashed #e0e0e0', borderRadius: 2, p: 4, textAlign: 'center', mb: 2, cursor: 'pointer', transition: 'border-color 0.2s', '&:hover': { borderColor: '#bdbdbd' }, bgcolor: dataSourceDragActive ? '#e3f2fd' : undefined }}
                onDragEnter={handleDataSourceDrag}
                onDragOver={handleDataSourceDrag}
                onDragLeave={handleDataSourceDrag}
                onDrop={handleDataSourceDrop}
                onClick={handleDataSourceBrowse}
              >
                <input
                  type="file"
                  ref={dataSourceInputRef}
                  style={{ display: 'none' }}
                  onChange={handleDataSourceFileChange}
                  accept=".csv,.xlsx"
                />
                <CloudUploadIcon sx={{ fontSize: 32, color: '#bdbdbd', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">Drop files here or click to browse</Typography>
                <Typography variant="caption" color="text.secondary">Supports CSV, XLSX, and database connections</Typography>
              </Box>
      <Button variant="outlined" fullWidth startIcon={<StorageIcon />} onClick={() => setDbModalOpen(true)}>Connect Database</Button>

      {/* Connect Database Modal */}
      <Dialog open={dbModalOpen} onClose={() => setDbModalOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Connect Database</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              select
              label="Database Type"
              value={dbType}
              onChange={handleDbTypeChange}
              fullWidth
              size="small"
            >
              <MenuItem value="postgres">Postgres</MenuItem>
              <MenuItem value="sqlserver">SQL Server</MenuItem>
            </TextField>
            <TextField label="Host" name="host" value={dbForm.host} onChange={handleDbFormChange} fullWidth size="small" required />
            <TextField label="Port" name="port" value={dbForm.port} onChange={handleDbFormChange} fullWidth size="small" required />
            <TextField label="User" name="user" value={dbForm.user} onChange={handleDbFormChange} fullWidth size="small" required />
            <TextField label="Password" name="password" type="password" value={dbForm.password} onChange={handleDbFormChange} fullWidth size="small" required />
            <TextField label="Database Name" name="database" value={dbForm.database} onChange={handleDbFormChange} fullWidth size="small" required />
            <TextField label="Schema" name="schema" value={dbForm.schema} onChange={handleDbFormChange} fullWidth size="small" required />
            {dbError && <Alert severity="error">{dbError}</Alert>}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDbModalOpen(false)} disabled={dbLoading}>Cancel</Button>
          <Button onClick={handleDbConnect} variant="contained" disabled={dbLoading}>{dbLoading ? 'Connecting...' : 'Connect'}</Button>
        </DialogActions>
      </Dialog>
            </CardContent>
          </Card>
      {/* Data Sources List */}
      <Card>
        <CardHeader title="Available Data Sources" subheader="Select which data sources to include in your LLM context" />
        <CardContent>
          {dataSources.map((source) => (
            <Box key={source.id} sx={{ display: 'flex', alignItems: 'center', p: 1, border: '1px solid #e0e0e0', borderRadius: 2, mb: 1, gap: 2, '&:hover': { background: '#f9fafb' } }}>
              <Checkbox checked={selectedDataSources.includes(source.id)} onChange={() => handleToggleDataSource(source.id, source.status === 'active' ? 'inactive' : 'active')} />
              {getFileIcon(source.type)}
              <Box sx={{ flex: 1 }}>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{source.name}</Typography>
                <Typography variant="caption" color="text.secondary">{source.size} • {source.lastModified}</Typography>
              </Box>
              <Chip label={source.status} color={getStatusColor(source.status)} size="small" />
              <IconButton size="small" onClick={() => handleDeleteDataSource(source.id)}><DeleteIcon /></IconButton>
            </Box>
          ))}
          <Box sx={{ mt: 2, p: 2, background: '#e3f2fd', borderRadius: 2 }}>
            <Typography variant="body2" color="primary"><CheckCircleIcon fontSize="small" sx={{ mr: 1 }} />{selectedDataSources.length} data sources selected</Typography>
          </Box>
        </CardContent>
      </Card>
        </Box>
      )}
      {tab === 1 && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
      {/* File Upload for Context */}
      <Card>
        <CardHeader title={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><DescriptionIcon /><span>Document Context</span></Box>} subheader="Upload PDFs, images, Word documents, and other files to provide context" />
        <CardContent>
          <Box
            sx={{ border: '2px dashed #e0e0e0', borderRadius: 2, p: 4, textAlign: 'center', mb: 2, cursor: 'pointer', transition: 'border-color 0.2s', '&:hover': { borderColor: '#bdbdbd' }, bgcolor: contextDragActive ? '#e3f2fd' : undefined }}
            onDragEnter={handleContextDrag}
            onDragOver={handleContextDrag}
            onDragLeave={handleContextDrag}
            onDrop={handleContextDrop}
            onClick={handleContextBrowse}
          >
            <input
              type="file"
              ref={contextInputRef}
              style={{ display: 'none' }}
              onChange={handleContextFileChange}
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.zip"
            />
            <DescriptionIcon sx={{ fontSize: 28, color: '#bdbdbd', mr: 1 }} />
            <ImageIcon sx={{ fontSize: 28, color: '#bdbdbd', mr: 1 }} />
            <Typography variant="body2" color="text.secondary">Drop your context files here</Typography>
            <Typography variant="caption" color="text.secondary">PDF, DOCX, images, and more</Typography>
          </Box>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Document Files</Typography>
          {contextFiles.map((file) => (
            <Box key={file.id} sx={{ display: 'flex', alignItems: 'center', p: 1, border: '1px solid #e0e0e0', borderRadius: 2, mb: 1, gap: 2, '&:hover': { background: '#f9fafb' } }}>
              <Checkbox checked={false} disabled />
              {getFileIcon(file.type)}
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{file.name}</Typography>
                <Typography variant="caption" color="text.secondary">{file.size}</Typography>
              </Box>
              <Chip label={file.status} color={getStatusColor(file.status)} size="small" />
              <IconButton size="small" onClick={() => handleDeleteContextFile(file.id)}><DeleteIcon /></IconButton>
            </Box>
          ))}
        </CardContent>
      </Card>
      {/* Domain Knowledge Text Input */}
      <Card>
        <CardHeader title={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><PsychologyIcon /><span>Domain Knowledge</span></Box>} subheader="Provide textual domain information and instructions for your LLM" />
        <CardContent>
          <TextField
            label="Domain Context & Instructions"
            multiline
            minRows={8}
            fullWidth
            value={domainContext}
            onChange={handleDomainContextChange}
            placeholder="Describe your domain, business rules, specific terminology, or any other context that will help the LLM understand your use case better..."
            helperText={`${domainContext.length}/2000 characters`}
          />
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
            <Button variant="contained" onClick={handleDomainSave}>Save</Button>
            {domainSaveStatus === 'saving' && <Typography color="text.secondary">Saving...</Typography>}
            {domainSaveStatus === 'saved' && <Typography color="success.main">Saved</Typography>}
            {domainSaveStatus === 'error' && <Typography color="error.main">Error</Typography>}
          </Box>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Quick Templates</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {templates.map((template) => (
              <Button key={template} variant="outlined" size="small" sx={{ textTransform: 'none' }} onClick={() => handleApplyTemplate(template)}>{template}</Button>
            ))}
          </Box>
        </CardContent>
      </Card>
        </Box>
      )}
      {/* Snackbar for upload feedback */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbarOpen(false)} severity="success" sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}
