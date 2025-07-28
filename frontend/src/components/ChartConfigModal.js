// --------------------------------------------------------------------
//  ChartConfigModal
//  – reflects default aggregation & groupBy coming from parent
// --------------------------------------------------------------------
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
  bgcolor: 'background.paper',
  boxShadow: 24,
  p: 3,
  borderRadius: 2,
};

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

function ChartConfigModal({
  open,
  currentType,
  xCol,
  yCol,
  aggregation: currentAggregation,
  groupBy: currentGroupBy,
  seriesCol: currentSeriesCol,
  data,
  chartId, // <-- Pass chartId from parent ChartTile
  onClose,
  onApply,
  decimalPlaces: initialDecimalPlaces = 2,
  useThousandsSeparator: initialUseThousandsSeparator = true,
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

  // Track previous chartId and data reference
  const prevChartId = useRef(chartId);
  const prevDataRef = useRef(data);

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
  }, [currentType, xCol, yCol, currentAggregation, currentGroupBy, currentSeriesCol, data, chartId, initialDecimalPlaces, initialUseThousandsSeparator]);

  const columns = data.length ? Object.keys(data[0]) : [];

  const handleYKeyChange = (e) => {
    const value = e.target.value;
    setYKeys(typeof value === 'string' ? value.split(',') : value);
  };

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
    });
  };

  const chartTypes = [
    { key: 'bar',  label: 'Bar',  icon: <BarChartIcon />   },
    { key: 'line', label: 'Line', icon: <ShowChartIcon />  },
    { key: 'area', label: 'Area', icon: <AreaChartIcon />  },
    { key: 'pie',  label: 'Pie',  icon: <PieChartIcon />   },
    { key: 'kpi',  label: 'KPI',  icon: <ActivityIcon />   },
  ];

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={modalStyle}>
        <Typography variant="h6" sx={{ mb: 3 }}>
          Configure Chart
        </Typography>

        <Grid container spacing={1} sx={{ mb: 2 }}>
          {chartTypes.map((ct) => (
            <Grid key={ct.key}>
              <ChartTypeButton
                variant="outlined"
                selected={chartType === ct.key ? 1 : 0}
                onClick={() => setChartType(ct.key)}
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
          >
            {columns.map((col) => (
              <MenuItem key={col} value={col}>
                <Checkbox checked={yKeys.indexOf(col) > -1} />
                <ListItemText primary={col} />
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Aggregation</InputLabel>
          <Select
            value={aggregation}
            label="Aggregation"
            onChange={(e) => setAggregation(e.target.value)}
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
            />
            <Typography variant="body2">Thousands Separator</Typography>
          </Box>
        </FormControl>

        <Box sx={{ textAlign: 'right' }}>
          <Button variant="outlined" onClick={onClose} sx={{ mr: 2 }}>
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

export default ChartConfigModal;
