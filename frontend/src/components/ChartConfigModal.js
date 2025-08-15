/**
 * ChartConfigModal
 * Modal dialog for configuring chart options (type, axes, aggregation, formatting, highlights, etc.).
 * Reflects default aggregation & groupBy coming from parent.
 *
 * Props:
 *   open (bool): Whether the modal is open
 *   currentType (string): Initial chart type
 *   xCol (string): Initial X column
 *   yCol (string|array): Initial Y column(s)
 *   aggregation (string): Initial aggregation type
 *   groupBy (string): Initial group by column
 *   seriesCol (string): Initial series column
 *   data (array): Chart data
 *   chartId (string): Chart identifier
 *   onClose (func): Callback to close modal
 *   onApply (func): Callback to apply/save config
 *   decimalPlaces (number): Initial decimal places
 *   useThousandsSeparator (bool): Initial thousands separator
 *   highlightCategory (string): Initial highlight category
 *   highlightValue (string): Initial highlight value
 *   secondaryYKey (string): Initial secondary Y axis key
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Checkbox,
  ListItemText,
  Grid,
} from '@mui/material';
import BarChartIcon from '@mui/icons-material/BarChart';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import AreaChartIcon from '@mui/icons-material/Timeline';
import PieChartIcon from '@mui/icons-material/PieChart';
import ActivityIcon from '@mui/icons-material/AutoGraph';
import { styled } from '@mui/system';

const modalStyle = {
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: 420,
  maxHeight: '80vh', // Limit modal height to 80% of viewport
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 3,
  borderRadius: 2,
  display: 'flex',
  flexDirection: 'column',
};

// Styled button for chart type selection
const ChartTypeButton = styled(Button)(({ theme, selected }) => ({
  flexDirection: 'column',
  padding: 12,
  borderRadius: 8,
  minWidth: 70,
  border: selected
    ? `2px solid ${theme.palette.primary.main}`
    : `1px solid ${theme.palette.divider}`,
  backgroundColor: selected
    ? theme.palette.background.default
    : theme.palette.background.paper,
  '&:hover': { backgroundColor: theme.palette.action.hover },
}));

/**
 * ChartConfigModal component
 * @param {object} props
 */
function ChartConfigModal({
  open,
  currentType,
  xCol,
  yCol,
  aggregation: currentAggregation,
  groupBy: currentGroupBy,
  seriesCol: currentSeriesCol,
  data,
  chartId,
  onClose,
  onApply,
  decimalPlaces: initialDecimalPlaces = 2,
  useThousandsSeparator: initialUseThousandsSeparator = true,
  highlightCategory: initialHighlightCategory = '',
  highlightValue: initialHighlightValue = '',
  secondaryYKey: initialSecondaryYKey = '',
}) {
  const [chartType,    setChartType]    = useState(currentType);
  const [xColumn,      setXColumn]      = useState(xCol);
  const [yKeys,        setYKeys]        = useState(
    Array.isArray(yCol) ? yCol : yCol ? [yCol] : []
  );
  const [aggregation,  setAggregation]  = useState(currentAggregation || 'none');
  const [groupBy,      setGroupBy]      = useState(currentGroupBy || '');
  const [seriesCol,    setSeriesCol]    = useState(currentSeriesCol || '');
  const [decimalPlaces, setDecimalPlaces] = useState(initialDecimalPlaces);
  const [useThousandsSeparator, setUseThousandsSeparator] = useState(initialUseThousandsSeparator);
  // Highlight category state
  const [highlightCategory, setHighlightCategory] = useState(initialHighlightCategory);
  const [highlightValue, setHighlightValue] = useState(initialHighlightValue);
  // Secondary Y-axis state
  const [secondaryYKey, setSecondaryYKey] = useState(initialSecondaryYKey);

  // Track previous chartId and data reference
  const prevChartId = useRef(chartId);
  const prevDataRef = useRef(data);

  // Reset state when relevant props change
  useEffect(() => {
    setChartType(currentType);
    setXColumn(xCol);
    setYKeys(Array.isArray(yCol) ? yCol : yCol ? [yCol] : []);
    setAggregation(currentAggregation || 'none');
    setGroupBy(currentGroupBy || '');
    // Only reset seriesCol if chartId or data reference changes
    if (prevChartId.current !== chartId || prevDataRef.current !== data) {
      setSeriesCol(currentSeriesCol || '');
      prevChartId.current = chartId;
      prevDataRef.current = data;
    }
    setDecimalPlaces(initialDecimalPlaces);
    setUseThousandsSeparator(initialUseThousandsSeparator);
    setHighlightCategory(initialHighlightCategory);
    setHighlightValue(initialHighlightValue);
    setSecondaryYKey(initialSecondaryYKey);
  }, [currentType, xCol, yCol, currentAggregation, currentGroupBy, currentSeriesCol, data, chartId, initialDecimalPlaces, initialUseThousandsSeparator, initialHighlightCategory, initialHighlightValue, initialSecondaryYKey]);

  // Get unique values for highlight value dropdown
  // Memoized list of unique values for highlight value dropdown
  const highlightValuesList = React.useMemo(() => {
    if (!highlightCategory || !data.length) return [];
    return Array.from(new Set(data.map(row => row[highlightCategory]).filter(v => v !== undefined && v !== null)));
  }, [highlightCategory, data]);

  // List of columns in the data
  const columns = data.length ? Object.keys(data[0]) : [];

  // Handle Y axis selection (multi-select)
  const handleYKeyChange = (e) => {
    const value = e.target.value;
    setYKeys(typeof value === 'string' ? value.split(',') : value);
  };

  // Save/apply chart configuration
  const handleSave = () => {
    onApply({
      chartType,
      xCol: xColumn,
      yCol: yKeys.length === 1 ? yKeys[0] : yKeys,
      aggregation,
      groupBy,
      seriesCol,
      decimalPlaces,
      useThousandsSeparator,
      highlightCategory,
      highlightValue,
      secondaryYKey,
    });
  };

  // Chart type options
  const chartTypes = [
    { key: 'bar',  label: 'Bar',  icon: <BarChartIcon aria-label="Bar chart" />   },
    { key: 'line', label: 'Line', icon: <ShowChartIcon aria-label="Line chart" />  },
    { key: 'area', label: 'Area', icon: <AreaChartIcon aria-label="Area chart" />  },
    { key: 'pie',  label: 'Pie',  icon: <PieChartIcon aria-label="Pie chart" />   },
    { key: 'kpi',  label: 'KPI',  icon: <ActivityIcon aria-label="KPI" />   },
  ];

  return (
    <Modal open={open} onClose={onClose} aria-labelledby="chart-config-modal-title">
      <Box sx={modalStyle}>
        <Typography id="chart-config-modal-title" variant="h6" sx={{ mb: 3 }}>
          Configure Chart
        </Typography>
        {/* Scrollable content container */}
        <Box sx={{ flex: 1, overflowY: 'auto', mb: 2 }}>
          <Grid container spacing={1} sx={{ mb: 2 }}>
            {chartTypes.map((ct) => (
              <Grid key={ct.key}>
                <ChartTypeButton
                  variant="outlined"
                  selected={chartType === ct.key ? 1 : 0}
                  onClick={() => setChartType(ct.key)}
                  aria-label={ct.label + ' chart type'}
                >
                  {ct.icon}
                  <Typography variant="caption" sx={{ mt: 1 }}>
                    {ct.label}
                  </Typography>
                </ChartTypeButton>
              </Grid>
            ))}
          </Grid>

          {chartType !== 'kpi' && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>X Axis</InputLabel>
              <Select
                value={xColumn || ''}
                label="X Axis"
                onChange={(e) => setXColumn(e.target.value)}
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

          {chartType !== 'kpi' && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Series (Split by)</InputLabel>
              <Select
                value={seriesCol}
                label="Series (Split by)"
                onChange={(e) => setSeriesCol(e.target.value)}
                inputProps={{ 'aria-label': 'Series (split by)' }}
              >
                <MenuItem value=""><em>None</em></MenuItem>
                {columns.map((col) => (
                  <MenuItem key={col} value={col}>
                    {col}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>
              Measure {chartType !== 'kpi' && chartType !== 'pie' ? '(select multiple)' : ''}
            </InputLabel>
            <Select
              multiple={chartType !== 'kpi' && chartType !== 'pie'}
              value={yKeys}
              label="Measure"
              onChange={handleYKeyChange}
              renderValue={(sel) => (Array.isArray(sel) ? sel.join(', ') : sel)}
              inputProps={{ 'aria-label': 'Measure (Y axis)' }}
            >
              {columns.map((col) => (
                <MenuItem key={col} value={col}>
                  <Checkbox checked={yKeys.indexOf(col) > -1} />
                  <ListItemText primary={col} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Secondary Y-axis dropdown (only for line/area charts) */}
          {(chartType === 'line' || chartType === 'area') && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Secondary Y Axis</InputLabel>
              <Select
                value={secondaryYKey}
                label="Secondary Y Axis"
                onChange={(e) => setSecondaryYKey(e.target.value)}
                inputProps={{ 'aria-label': 'Secondary Y axis' }}
              >
                <MenuItem value=""><em>None</em></MenuItem>
                {columns.filter(col => !yKeys.includes(col)).map((col) => (
                  <MenuItem key={col} value={col}>{col}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Aggregation</InputLabel>
            <Select
              value={aggregation}
              label="Aggregation"
              onChange={(e) => setAggregation(e.target.value)}
              inputProps={{ 'aria-label': 'Aggregation' }}
            >
              <MenuItem value="none">None</MenuItem>
              <MenuItem value="sum">Sum</MenuItem>
              <MenuItem value="average">Average</MenuItem>
              <MenuItem value="count">Count</MenuItem>
              <MenuItem value="median">Median</MenuItem>
            </Select>
          </FormControl>

          {aggregation !== 'none' && (
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Group By</InputLabel>
              <Select
                value={groupBy}
                label="Group By"
                onChange={(e) => setGroupBy(e.target.value)}
                inputProps={{ 'aria-label': 'Group by' }}
              >
                {columns.map((col) => (
                  <MenuItem key={col} value={col}>
                    {col}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Decimal Places</InputLabel>
            <Select
              value={decimalPlaces}
              label="Decimal Places"
              onChange={e => setDecimalPlaces(Number(e.target.value))}
              inputProps={{ 'aria-label': 'Decimal places' }}
            >
              {[0, 1, 2, 3, 4].map((n) => (
                <MenuItem key={n} value={n}>{n}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', pl: 1 }}>
              <Checkbox
                checked={useThousandsSeparator}
                onChange={e => setUseThousandsSeparator(e.target.checked)}
                inputProps={{ 'aria-label': 'Thousands separator' }}
              />
              <Typography variant="body2">Thousands Separator</Typography>
            </Box>
          </FormControl>

          {/* Highlight Category dropdown */}
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Highlight Category</InputLabel>
            <Select
              value={highlightCategory}
              label="Highlight Category"
              onChange={(e) => {
                setHighlightCategory(e.target.value);
                setHighlightValue('');
              }}
              inputProps={{ 'aria-label': 'Highlight category' }}
            >
              <MenuItem value=""><em>None</em></MenuItem>
              {columns.map((col) => (
                <MenuItem key={col} value={col}>{col}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Highlight Value dropdown (only if category selected) */}
          {highlightCategory && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Highlight Value</InputLabel>
              <Select
                value={highlightValue}
                label="Highlight Value"
                onChange={(e) => setHighlightValue(e.target.value)}
                inputProps={{ 'aria-label': 'Highlight value' }}
              >
                <MenuItem value=""><em>None</em></MenuItem>
                {highlightValuesList.map((val) => (
                  <MenuItem key={val} value={val}>{val}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>
        {/* Buttons always visible at bottom */}
        <Box sx={{ textAlign: 'right', pt: 1 }}>
          <Button variant="outlined" onClick={onClose} sx={{ mr: 2 }} aria-label="Cancel">
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave} aria-label="Save chart configuration">
            Save
          </Button>
        </Box>
      </Box>
    </Modal>
  );
}

export default ChartConfigModal;
