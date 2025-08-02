// src/components/ChartTile.js
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, IconButton, Box, Typography, TextField, Tabs, Tab } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import EditIcon from '@mui/icons-material/Edit';
import CloseIcon from '@mui/icons-material/Close';
import moment from 'moment';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import ChartConfigModal from './ChartConfigModal';
import SqlModal from './SqlModal';


// Define a list of acceptable date formats.
const DATE_FORMATS = [
  'YYYY-MM-DD',
  'YYYY/MM/DD',
  'DD-MM-YYYY',
  'DD/MM/YYYY',
  'D-MM-YYYY',
  'D/MM/YYYY',
  'DD-M-YYYY',
  'DD/M/YYYY',
  'D-M-YYYY',
  'D/M/YYYY',
  'YYYY-MM-DDTHH:mm:ss',
  'YYYY-MM-DDTHH:mm:ssZ',
  'MM/DD/YYYY', // You can add more formats as needed.
  'MMM D, YYYY', // e.g., "Mar 10, 2018"
];

// Helper: Check if a value is numeric.
function isNumeric(val) {
  return !isNaN(parseFloat(val)) && isFinite(val);
}

// Updated isValidDate using dayjs in strict mode.
function isValidDate(value) {
  if (typeof value !== 'string') return false;
  // Try to parse with the defined formats in strict mode.
  const parsed = moment(value, DATE_FORMATS, true);
  return parsed.isValid();
}
/**
 * Check whether the chosen X column contains duplicate values.
 * @param {Array<Object>} data   – full dataset
 * @param {string}        xCol   – key to inspect
 * @returns {boolean}
 */
function hasDuplicateX(data, xCol) {
  if (!data || data.length === 0 || !xCol) return false;
  const seen = new Set();
  for (const row of data) {
    const val = row[xCol];
    if (seen.has(val)) return true;
    seen.add(val);
  }
  return false;
}

// Updated formatDateValue: if the string is a valid date per dayjs using defined formats, format it; otherwise, return it unchanged.
function formatDateValue(value) {
  if (typeof value === 'string') {
    const parsed = moment(value, DATE_FORMATS, true);
    if (parsed.isValid()) {
      // For example, format as "10 Mar 2018". You can change this format to "Do [of] MMM YYYY" 
      // if you wish to show ordinal numbers (using a plugin such as dayjs/plugin/advancedFormat).
      return parsed.format("D MMM YYYY");
    }
    return value;
  }
  return value;
}


// Extended auto-detection function: chooses default x and y columns, and default chart type.
// If a valid date string is detected, default to "line". If only one row, default to "kpi".
function autoDetectColumns(data) {
  if (!data || data.length === 0) return { defaultX: '', defaultY: '', defaultChartType: 'bar', defaultAggregation: 'none', defaultGroupBy: '' };
  const row = data[0];
  const keys = Object.keys(row);
  let defaultX = '';
  let defaultY = '';
  let defaultChartType = 'bar';
  let defaultAggregation = 'none'; // Always default to 'none'
  let defaultGroupBy     = '';
  
  // Look for a date column: require that the value contains a dash or slash.
  for (const key of keys) {
    if (typeof row[key] === 'string' && isValidDate(row[key]) && !hasDuplicateX(data, key)) {
      defaultX = key;
      defaultChartType = 'line';
      const isConstantDate = data.every(row => row[key] === data[0][key]);
      if (isConstantDate) {
        defaultChartType = 'bar';
      }
      break;
    }
  }
  // If dataset contains only one row, default to KPI.
  if (data.length === 1) {
    defaultChartType = 'kpi';
  }
  // If no date column found, use first available string column.
  if (!defaultX) {
    for (const key of keys) {
      if (typeof row[key] === 'string') {
        defaultX = key;
        break;
      }
    }
  }
  if (!defaultX && keys.length > 0) {
    defaultX = keys[0];
  }
  // For defaultY, select the first numeric column not the same as defaultX.
  for (const key of keys) {
    if (key !== defaultX && isNumeric(row[key])) {
      defaultY = key;
      break;
    }
  }
  if (!defaultY) {
    defaultY = keys.length > 1 ? keys[1] : keys[0];
  }
  return { defaultX, defaultY, defaultChartType, defaultAggregation, defaultGroupBy, };
}

// Updated transformData: For each row, use formatDateValue for the xCol value.
/**
 * Transform raw rows into the shape Recharts expects,
 * performing aggregation & group‑by where requested.
 */
/**
 * Convert raw rows into Recharts‑ready objects,
 * applying grouping / aggregation rules as requested.
 */
function transformData(data, config) {
  const {
    chartType,
    xCol,
    yKeys = [],
    aggregation = 'none',
    groupBy = '',
    seriesCol = '',
  } = config;
  if (!data || data.length === 0) return [];

  // ─── KPI branch ────────────────────────────────────────────────────
  if (chartType === 'kpi') {
    if (data.length === 1) return data;   // nothing to aggregate

    const numericKeys = Object.keys(data[0]).filter((k) => isNumeric(data[0][k]));

    // KPI + groupBy → reuse aggregated branch
    if (groupBy) {
      return transformData(data, {
        chartType: 'bar',      // dummy value to enter aggregated path
        xCol,
        yKeys: numericKeys,
        aggregation,
        groupBy,
      });
    }

    // Aggregate entire dataset into a single KPI row
    const aggregatedRow = {};
    numericKeys.forEach((k) => {
      const vals = data.map((r) => Number(r[k]));
      switch (aggregation) {
        case 'average':
          aggregatedRow[k] = vals.reduce((a, b) => a + b, 0) / vals.length;
          break;
        case 'median': {
          const sorted = [...vals].sort((a, b) => a - b);
          const mid = Math.floor(sorted.length / 2);
          aggregatedRow[k] =
            sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
          break;
        }
        case 'count':
          aggregatedRow[k] = vals.length;
          break;
        case 'sum':
        default:
          aggregatedRow[k] = vals.reduce((a, b) => a + b, 0);
      }
    });
    return [aggregatedRow];
  }

  // ─── Multi-series (seriesCol) branch ────────────────────────────────
  if (seriesCol && chartType !== 'pie' && chartType !== 'kpi') {
    const seriesSet = new Set();
    data.forEach((row) => {
      if (row[seriesCol] !== undefined && row[seriesCol] !== null) {
        seriesSet.add(row[seriesCol]);
      }
    });
    const allSeries = Array.from(seriesSet);
    const grouped = {};
    data.forEach((row) => {
      const xVal = row[xCol] !== undefined ? formatDateValue(row[xCol]) : '';
      if (!grouped[xVal]) grouped[xVal] = {};
      const sVal = row[seriesCol];
      allSeries.forEach((series) => {
        if (!(series in grouped[xVal])) grouped[xVal][series] = [];
      });
      if (sVal !== undefined && sVal !== null) {
        grouped[xVal][sVal].push(row);
      }
    });
    return Object.entries(grouped).map(([x, seriesRows]) => {
      const obj = { x };
      allSeries.forEach((series) => {
        yKeys.forEach((key) => {
          const rows = seriesRows[series] || [];
          let val = null;
          if (rows.length === 0) {
            val = null; // Use null for missing values
          } else if (aggregation === 'none') {
            val = rows.map((r) => Number(r[key])).reduce((a, b) => a + b, 0);
          } else {
            const nums = rows.filter((r) => isNumeric(r[key])).map((r) => Number(r[key]));
            switch (aggregation) {
              case 'average':
                val = nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : null;
                break;
              case 'median': {
                if (nums.length) {
                  const sorted = [...nums].sort((a, b) => a - b);
                  const m = Math.floor(sorted.length / 2);
                  val = sorted.length % 2 ? sorted[m] : (sorted[m - 1] + sorted[m]) / 2;
                } else {
                  val = null;
                }
                break;
              }
              case 'count':
                val = rows.length;
                break;
              case 'sum':
              default:
                val = nums.reduce((a, b) => a + b, 0);
            }
          }
          const outKey = yKeys.length === 1 ? `${series}` : `${series}_${key}`;
          obj[outKey] = val;
        });
      });
      return obj;
    });
  }

  // ─── Aggregated (groupBy) branch ───────────────────────────────────
  if (aggregation !== 'none' && groupBy) {
    // Build groups keyed by groupBy, but capture the *xCol* for axis display
    const grouped = data.reduce((acc, row) => {
      const gKey = row[groupBy];
      if (!acc[gKey]) acc[gKey] = { rows: [], x: formatDateValue(row[xCol]) };
      acc[gKey].rows.push(row);
      return acc;
    }, {});

    // Produce one aggregated object per group
    return Object.values(grouped).map(({ x, rows }) => {
      const obj = { x };
      yKeys.forEach((key) => {
        const nums = rows.filter((r) => isNumeric(r[key])).map((r) => Number(r[key]));
        let val = 0;
        switch (aggregation) {
          case 'average':
            val = nums.reduce((a, b) => a + b, 0) / nums.length;
            break;
          case 'median': {
            const sorted = [...nums].sort((a, b) => a - b);
            const m = Math.floor(sorted.length / 2);
            val = sorted.length % 2 ? sorted[m] : (sorted[m - 1] + sorted[m]) / 2;
            break;
          }
          case 'count':
            val = rows.length;
            break;
          case 'sum':
          default:
            val = nums.reduce((a, b) => a + b, 0);
        }
        obj[key] = val;
      });
      return obj;
    });
  }

  // ─── Pass‑through (no aggregation) branch ──────────────────────────
  return data.map((row) => {
    const xVal = row[xCol] !== undefined ? formatDateValue(row[xCol]) : '';
    const obj = { x: xVal };
    yKeys.forEach((key) => {
      obj[key] = isNumeric(row[key]) ? Number(row[key]) : row[key];
    });
    return obj;
  });
}

// Format a number with decimals and thousands separator
function formatNumber(value, decimalPlaces = 2, useThousandsSeparator = true) {
  if (typeof value !== 'number') value = Number(value);
  if (isNaN(value)) return value;
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
    useGrouping: useThousandsSeparator,
  });
}

function ChartTile({ chartId, title: initialTitle, data, sql, previewData, onRemove, onTitleChange, onSQLUpdate, qualityData }) {
  const theme = useTheme();
  const [title, setTitle] = useState(initialTitle || 'Untitled Chart');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [config, setConfig] = useState({
    chartType: '',
    xCol: '',
    yKeys: [],
    aggregation: 'none',
    groupBy: '',
    seriesCol: '',
    decimalPlaces: 2,
    useThousandsSeparator: true,
  });
  const [chartData, setChartData] = useState([]);
  const [showConfig, setShowConfig] = useState(false);
  const [tab, setTab] = useState(0); // 0: Viz, 1: Data, 2: SQL, 3: Quality
  const [sqlModalOpen, setSqlModalOpen] = useState(false);
  const [expandedPreview, setExpandedPreview] = useState(false);

  // Load saved configuration from localStorage on mount.
  useEffect(() => {
    const savedConfig = localStorage.getItem(`chartConfig-${chartId}`);
    if (savedConfig) {
      setConfig(JSON.parse(savedConfig));
    }
  }, [chartId]);

  // Auto-detect columns only on initial data load or when data changes, not on every config change.
  useEffect(() => {
    if (!data || data.length === 0 || config.chartType === 'kpi') return;
    // Only run auto-detection if config is still at its initial state (all empty/default)
    if (
      !config.xCol &&
      (!config.yKeys || config.yKeys.length === 0) &&
      !config.chartType &&
      config.aggregation === 'none' &&
      !config.groupBy &&
      !config.seriesCol
    ) {
      const {
        defaultX,
        defaultY,
        defaultChartType,
        defaultAggregation,
        defaultGroupBy,
      } = autoDetectColumns(data);
      setConfig((prev) => {
        const next = { ...prev };
        if (!next.xCol) next.xCol = defaultX;
        if (!next.yKeys || next.yKeys.length === 0) next.yKeys = [defaultY];
        if (!next.chartType) next.chartType = defaultChartType;
        // Only set aggregation if auto-detect says so, but prefer 'none' unless needed
        if (next.aggregation === 'none' && defaultAggregation !== 'none') {
          next.aggregation = defaultAggregation;
        }
        if (!next.groupBy && defaultGroupBy) {
          next.groupBy = defaultGroupBy;
        }
        return next;
      });
    }
  }, [data]);

  // Persist configuration.
  useEffect(() => {
    localStorage.setItem(`chartConfig-${chartId}`, JSON.stringify(config));
  }, [chartId, config]);

  // Transform data as per config.
  useEffect(() => {
    setChartData(transformData(data, config));
  }, [data, config]);

/**
 * Persist configuration coming back from ChartConfigModal.
 * – Respects the user's exact Aggregation & Group‑By choices.
 * – Still prevents accidental duplicate bars when the user leaves
 *   Aggregation untouched and duplicates exist.
 */
const handleApplyConfig = (newConfig) => {
  const updatedConfig = {
    ...newConfig,
    yCol: Array.isArray(newConfig.yCol) ? newConfig.yCol : [newConfig.yCol],
  };
  const finalConfig = {
    chartType:   updatedConfig.chartType,
    xCol:        updatedConfig.xCol,
    yKeys:       updatedConfig.yCol,
    aggregation: updatedConfig.aggregation, // ← Do not override user's choice
    groupBy:     updatedConfig.groupBy,
    seriesCol:   updatedConfig.seriesCol || '',
    decimalPlaces: updatedConfig.decimalPlaces ?? 2,
    useThousandsSeparator: updatedConfig.useThousandsSeparator ?? true,
  };
  setConfig(finalConfig);
  setShowConfig(false);
};





  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (onTitleChange) onTitleChange(chartId, title);
  };

  // Calculate x-axis rotation settings based on the first x value.
  const getXAxisRotation = () => {
    const firstX = chartData[0]?.x;
    //if (firstX instanceof Date) return { angle: -45, textAnchor: 'end' };
    //if (typeof firstX === 'string' && firstX.length > 8) return { angle: -45, textAnchor: 'end' };
    return { angle: 0, textAnchor: 'middle' };
  };

  function renderChartOrKpi() {
    if (!chartData || chartData.length === 0) {
      return (
        <Typography variant="body2" color="text.secondary">
          No data available
        </Typography>
      );
    }
    const row = data[0];
    const numericCols = Object.keys(row).filter((k) => isNumeric(row[k]));
    if (config.chartType === 'kpi') {
      return (
      <Box sx={{ display: 'grid',
        gridTemplateColumns: `repeat(auto-fit, minmax(120px, 1fr))`,
        gap: 2,
        width: '100%',
        height: '100%',
        p: 2, }}>
      {numericCols.map((col) => (
        <Box
          key={col}
          sx={{
            backgroundColor: theme.palette.background.default,
            boxShadow: theme.shadows[1],
            borderRadius: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
          }}
        >
          <Typography variant="caption" sx={{ color: theme.palette.text.primary }}>
            {col}
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {formatNumber(row[col], config.decimalPlaces, config.useThousandsSeparator)}
          </Typography>
        </Box>
      ))}
    </Box>);
    }
    return (
      <Box sx={{ width: '100%', height: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart(config, chartData)}
        </ResponsiveContainer>
      </Box>
    );
  }

  const colorByIndex = (index) => {
    const chartColors = theme.palette.chartColors || ['#5C7285', '#FFA600', '#FF7C43', '#F95D6A'];
    return chartColors[index % chartColors.length];
  };

  function renderChart(config, chartData) {
    const { chartType, xCol, yKeys = [], seriesCol = '' } = config;
    const xAxisProps = getXAxisRotation();
    let seriesKeys = [];
    if (seriesCol && chartData.length > 0) {
      seriesKeys = Object.keys(chartData[0]).filter((k) => k !== 'x');
    } else {
      seriesKeys = yKeys;
    }
    switch (chartType) {
      case 'line':
        return (
          <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <CartesianGrid stroke={theme.palette.divider} strokeDasharray="2 2" vertical={false} />
            <XAxis
              dataKey="x"
              axisLine={false}
              tickLine={false}
              tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
              {...xAxisProps}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
            />
            <Tooltip
              contentStyle={{ borderRadius: 4, boxShadow: theme.shadows[1] }}
              itemStyle={{ fontSize: 12 }}
              formatter={(value) =>
                isNumeric(value)
                  ? formatNumber(value, config.decimalPlaces, config.useThousandsSeparator)
                  : value
              }
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, color: theme.palette.text.secondary }}
            />
            {seriesKeys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colorByIndex(index)}
                dot={false}
                activeDot={false}
                strokeWidth={1}
                isAnimationActive
                animationDuration={800}
                animationBegin={index * 200}
                minTickGap={30}
                connectNulls={true}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <CartesianGrid stroke={theme.palette.divider} strokeDasharray="2 2" vertical={false} />
            <XAxis
              dataKey="x"
              axisLine={false}
              tickLine={false}
              tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
              {...xAxisProps}
            />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: theme.palette.text.secondary, fontSize: 11 }} />
            <Tooltip
              contentStyle={{ borderRadius: 4, boxShadow: theme.shadows[1] }}
              itemStyle={{ fontSize: 12 }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, color: theme.palette.text.secondary }}
            />
            {seriesKeys.map((key, index) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colorByIndex(index)}
                fill={colorByIndex(index)}
                fillOpacity={0.2}
                strokeWidth={1}
                isAnimationActive
                animationDuration={800}
                animationBegin={index * 200}
                minTickGap={30}
                connectNulls={true}
              />
            ))}
          </AreaChart>
        );

      case 'pie': {
        const pieKey = yKeys[0] || '';
        const pieData = chartData.map((row) => ({ name: row.x, value: row[pieKey] }));
        return (
          <PieChart margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
            <Tooltip
              contentStyle={{ borderRadius: 4, boxShadow: theme.shadows[1] }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, color: theme.palette.text.secondary }}
            />
            <Pie
              data={pieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              isAnimationActive
              animationDuration={800}
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colorByIndex(index)} />
              ))}
            </Pie>
          </PieChart>
        );
      }

      case 'bar':
      default:
        return (
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 5, bottom: 5, left: 5 }}
            barCategoryGap="20%"
            barGap={4}
          >
            <CartesianGrid stroke={theme.palette.divider} strokeDasharray="2 2" vertical={false} />
            <XAxis
              dataKey="x"
              axisLine={false}
              tickLine={false}
              tick={{ fill: theme.palette.text.secondary, fontSize: 11 }}
              {...xAxisProps}
            />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: theme.palette.text.secondary, fontSize: 11 }} />
            <Tooltip
              contentStyle={{ borderRadius: 4, boxShadow: theme.shadows[1] }}
              itemStyle={{ fontSize: 12 }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              wrapperStyle={{ fontSize: 12, color: theme.palette.text.secondary }}
            />
            {seriesKeys.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colorByIndex(index)}
                name={key}
                radius={[4, 4, 0, 0]}
                isAnimationActive
                animationDuration={800}
                animationBegin={index * 200}
                minTickGap={30}
              />
            ))}
          </BarChart>
        );
    }
  }

  // Data preview logic
  const allData = previewData || data || [];
  const previewRows = expandedPreview ? allData : allData.slice(0, 10);

  // SQL edit logic
  const handleSQLSave = (newSQL) => {
    if (onSQLUpdate) onSQLUpdate(newSQL);
    setSqlModalOpen(false);
  };

  // Tab content renderers
  function renderTabContent() {
    switch (tab) {
      case 0:
        return (
          <Box sx={{ width: '100%', height: '100%' }}>{renderChartOrKpi()}</Box>
        );
      case 1:
        return (
          <Box sx={{ width: '100%', height: '100%', minHeight: 0 }}>
            {previewRows === undefined ? (
              <Typography variant="body2">Loading preview...</Typography>
            ) : previewRows.length === 0 ? (
              <Typography variant="body2">No data returned.</Typography>
            ) : (
              <Box sx={{
                width: '100%',
                height: '100%',
                overflow: 'auto',
                maxHeight: '260px', // or use: '100%' if CardContent is constrained
                borderRadius: 1,
                border: `1px solid ${theme.palette.divider}`,
                background: theme.palette.background.paper,
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.80rem', tableLayout: 'fixed' }}>
                  <thead>
                    <tr>
                      {Object.keys(previewRows[0]).map((col) => (
                        <th key={col} style={{ border: '1px solid #eee', padding: '4px 6px', fontWeight: 600, background: theme.palette.action.hover, fontSize: '0.80rem', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row, rowIdx) => (
                      <tr key={rowIdx}>
                        {Object.values(row).map((val, colIdx) => (
                          <td key={colIdx} style={{ border: '1px solid #eee', padding: '4px 6px', fontSize: '0.80rem', maxWidth: 120, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>{
                            isNumeric(val)
                              ? formatNumber(val, config.decimalPlaces, config.useThousandsSeparator)
                              : val
                          }</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {allData.length > 10 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography
                      variant="body2"
                      color="primary"
                      sx={{ cursor: 'pointer', display: 'inline-block', fontSize: '0.80rem' }}
                      onClick={() => setExpandedPreview((prev) => !prev)}
                    >
                      {expandedPreview ? 'See less' : 'See more'}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Box>
        );
      case 2:
        return (
          <Box>
            <pre style={{ background: '#f3f3f3', padding: '16px', borderRadius: '4px' }}>{sql}</pre>
            <Typography
              variant="body2"
              color="primary"
              sx={{ cursor: 'pointer', mt: 1 }}
              onClick={() => setSqlModalOpen(true)}
            >
              Edit SQL
            </Typography>
            <SqlModal
              open={sqlModalOpen}
              handleClose={() => setSqlModalOpen(false)}
              initialSQL={sql}
              onSQLUpdate={handleSQLSave}
            />
          </Box>
        );
      case 3:
        return (
          <Box>
            <Typography variant="h6">Data Quality</Typography>
            <Typography variant="body2" color="text.secondary">
              {qualityData ? JSON.stringify(qualityData) : 'Placeholder for data quality metrics.'}
            </Typography>
          </Box>
        );
      default:
        return null;
    }
  }

  return (
    <Card
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderRadius: 2,
        border: 1,
        borderColor: 'divider',
        boxShadow: 'none',
        overflow: 'visible',
      }}
    >
      <CardHeader
        sx={{ pb: 0 }}
        title={
          isEditingTitle ? (
            <TextField
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={handleTitleBlur}
              variant="standard"
              autoFocus
              inputProps={{ style: { fontSize: '12px', fontWeight: 500 } }}
            />
          ) : (
            <Typography variant="subtitle1" sx={{ fontSize: '12px', fontWeight: 500, cursor: 'pointer' }} onClick={() => setIsEditingTitle(true)}>
              {title}
            </Typography>
          )
        }
        action={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton size="small" onClick={() => setShowConfig(true)} aria-label="Configure Chart">
              <EditIcon fontSize="inherit" />
            </IconButton>
            <IconButton size="small" onClick={() => onRemove && onRemove(chartId)} aria-label="Remove Chart">
              <CloseIcon fontSize="inherit" />
            </IconButton>
          </Box>
        }
      />
      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        variant="fullWidth"
        sx={{
          minHeight: 28,
          height: 28,
          borderBottom: `1px solid ${theme.palette.divider}`,
          '& .MuiTab-root': {
            fontSize: '0.80rem',
            minHeight: 28,
            height: 28,
            padding: '2px 10px',
            textTransform: 'none',
            fontWeight: 500,
            borderRadius: 2,
            color: theme.palette.text.secondary,
            transition: 'background 0.2s',
          },
          '& .Mui-selected': {
            color: theme.palette.primary.main,
            background: theme.palette.action.hover,
          },
          mb: 0.5,
        }}
        TabIndicatorProps={{ style: { height: 2, borderRadius: 2 } }}
      >
        <Tab label="Visualization" disableRipple />
        <Tab label="Data Preview" disableRipple />
        <Tab label="SQL" disableRipple />
        <Tab label="Data Quality" disableRipple />
      </Tabs>
      <CardContent sx={{ flexGrow: 1, pt: 0, p: 1, height: '100%', minHeight: 0 }}>
        {renderTabContent()}
      </CardContent>
      {showConfig && (
        <ChartConfigModal
          open={showConfig}
          currentType={config.chartType}
          xCol={config.xCol}
          yCol={config.yKeys.length > 1 ? config.yKeys : config.yKeys[0]}
          aggregation={config.aggregation}
          groupBy={config.groupBy}
          seriesCol={config.seriesCol}
          data={data}
          chartId={chartId}
          onClose={() => setShowConfig(false)}
          onApply={handleApplyConfig}
          decimalPlaces={config.decimalPlaces}
          useThousandsSeparator={config.useThousandsSeparator}
        />
      )}
    </Card>
  );
}

export default ChartTile;
