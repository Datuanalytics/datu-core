/**
 * AddChartDialog
 * Dialog for creating a new chart/visualization. Lets user select chart type, data source, axes, and measure(s).
 *
 * Props:
 *   open (bool): Whether the dialog is open
 *   onClose (func): Callback to close dialog
 *   onAddChart (func): Callback to add chart, receives chart config
 *   dataSources (object): Map of data source names to data arrays
 */
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
} from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import PieChartIcon from '@mui/icons-material/PieChart';
import ActivityIcon from '@mui/icons-material/AutoAwesomeMotion';

function AddChartDialog({
  open,
  onClose,
  onAddChart,
  dataSources,
}) {
  // State for form fields
  const [title, setTitle] = useState('');
  const [chartType, setChartType] = useState('');
  const [dataSource, setDataSource] = useState('');
  const [xAxis, setXAxis] = useState('');
  const [yAxes, setYAxes] = useState([]); // multi-select
  const [errorMsg, setErrorMsg] = useState('');

  // Reset all fields and close dialog
  const handleClose = () => {
    setTitle('');
    setChartType('');
    setDataSource('');
    setXAxis('');
    setYAxes([]);
    setErrorMsg('');
    onClose();
  };

  // Validate and submit chart config
  const handleAddChart = () => {
    if (!title.trim() || !chartType || !dataSource) {
      setErrorMsg('Please fill all required fields');
      return;
    }
    if (chartType !== 'kpi' && !xAxis && chartType !== 'pie') {
      setErrorMsg('Please select an X axis for this chart type');
      return;
    }
    if (chartType !== 'kpi' && yAxes.length === 0) {
      setErrorMsg('Please select at least one Y axis/measure');
      return;
    }
    onAddChart({
      id: `chart-${Date.now()}`,
      title,
      chartType,
      dataSource,
      xKey: xAxis,
      yKeys: yAxes,
    });
    handleClose();
  };

  // Get columns for selected data source
  const columns = dataSource && dataSources[dataSource] && dataSources[dataSource].length > 0
    ? Object.keys(dataSources[dataSource][0])
    : [];

  // Handle Y axis selection (multi-select)
  const handleYAxesChange = (e) => {
    const value = e.target.value;
    setYAxes(typeof value === 'string' ? value.split(',') : value);
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>Add Visualization</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            label="Title"
            variant="outlined"
            fullWidth
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            inputProps={{ 'aria-label': 'Chart title' }}
          />

          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Chart Type
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              color={chartType === 'bar' ? 'primary' : 'default'}
              onClick={() => setChartType('bar')}
              aria-label="Bar chart"
            >
              <BarChartIcon />
            </IconButton>
            <IconButton
              color={chartType === 'line' ? 'primary' : 'default'}
              onClick={() => setChartType('line')}
              aria-label="Line chart"
            >
              <ShowChartIcon />
            </IconButton>
            <IconButton
              color={chartType === 'area' ? 'primary' : 'default'}
              onClick={() => setChartType('area')}
              aria-label="Area chart"
            >
              <TimelineIcon />
            </IconButton>
            <IconButton
              color={chartType === 'pie' ? 'primary' : 'default'}
              onClick={() => setChartType('pie')}
              aria-label="Pie chart"
            >
              <PieChartIcon />
            </IconButton>
            <IconButton
              color={chartType === 'kpi' ? 'primary' : 'default'}
              onClick={() => setChartType('kpi')}
              aria-label="KPI"
            >
              <ActivityIcon />
            </IconButton>
          </Box>

          <FormControl fullWidth>
            <InputLabel>Data Source</InputLabel>
            <Select
              value={dataSource}
              label="Data Source"
              onChange={(e) => setDataSource(e.target.value)}
              inputProps={{ 'aria-label': 'Data source' }}
            >
              {Object.keys(dataSources).map((ds) => (
                <MenuItem key={ds} value={ds}>
                  {ds}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {chartType !== 'kpi' && chartType !== 'pie' && (
            <FormControl fullWidth>
              <InputLabel>X Axis</InputLabel>
              <Select
                value={xAxis}
                label="X Axis"
                onChange={(e) => setXAxis(e.target.value)}
                inputProps={{ 'aria-label': 'X axis' }}
              >
                {columns.map((col) => (
                  <MenuItem key={col} value={col}>
                    {col}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {/* Multi-select for Y axes (for bar/line/area).
              For pie or KPI, we only select a single measure. */}
          <FormControl fullWidth>
            <InputLabel>
              {chartType === 'pie' || chartType === 'kpi' ? 'Measure' : 'Y Axis (select multiple)'}
            </InputLabel>
            <Select
              multiple={chartType !== 'pie' && chartType !== 'kpi'}
              value={yAxes}
              label="Y Axis"
              onChange={handleYAxesChange}
              renderValue={(selected) => (Array.isArray(selected) ? selected.join(', ') : selected)}
              inputProps={{ 'aria-label': 'Y axis' }}
            >
              {columns.map((col) => (
                <MenuItem key={col} value={col}>
                  {chartType !== 'pie' && chartType !== 'kpi' && (
                    <Checkbox checked={yAxes.indexOf(col) > -1} />
                  )}
                  <ListItemText primary={col} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {errorMsg && (
            <Typography variant="body2" color="error">
              {errorMsg}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} variant="outlined">
          Cancel
        </Button>
        <Button onClick={handleAddChart} variant="contained">
          Add Chart
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default AddChartDialog;
