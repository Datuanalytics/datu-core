/**
 * RightPanelTabs
 * Renders the right panel with chart dashboard and manages data fetching for selected queries.
 *
 * Props:
 *   queries (array): List of query objects
 *   selectedQueryIndices (array): Indices of selected queries
 *   setSelectedQueryIndices (function): Setter for selectedQueryIndices
 *   previewDataMap (object): Map of query id to preview data
 *   setPreviewDataMap (function): Setter for previewDataMap
 *   qualityMap (object): Map of query id to quality info
 *   onSQLUpdate (function): Callback to update SQL
 *   isEditMode (boolean): Whether dashboard is in edit mode
 *   setIsEditMode (function): Setter for isEditMode
 */
// src/components/RightPanelTabs.js
import React from 'react';
import { Box } from '@mui/material';
import VisualizationDashboard from './VisualizationDashboard';
import axios from 'axios';

/**
 * RightPanelTabs now expects a prop "selectedTab" from the top bar.
 */
function RightPanelTabs({
  queries,
  selectedQueryIndices,
  setSelectedQueryIndices,
  previewDataMap,
  setPreviewDataMap,
  qualityMap,
  onSQLUpdate,
  isEditMode,
  setIsEditMode,
}) {
  // Function to sanitize preview data ensuring primitive values only.
  const sanitizeData = (dataArray) => {
    return (dataArray || []).map((row) => {
      const sanitizedRow = {};
      Object.keys(row).forEach((key) => {
        const val = row[key];
        if (val !== null && typeof val === 'object' && val.$$typeof) {
          sanitizedRow[key] = JSON.stringify(val);
        } else if (val !== null && typeof val === 'object') {
          try {
            sanitizedRow[key] = JSON.stringify(val);
          } catch (e) {
            sanitizedRow[key] = '[Error]';
          }
        } else {
          sanitizedRow[key] = val;
        }
      });
      return sanitizedRow;
    });
  };

  // Always fetch full data for each selected query if not already loaded
  React.useEffect(() => {
    selectedQueryIndices.forEach(async (idx) => {
      const query = queries[idx];
      const data = previewDataMap[query.id];
      // If not loaded, fetch full data
      if (!data) {
        try {
          const resp = await axios.post('/api/transform/download/', {
            sql_code: query.sql,
          });
          setPreviewDataMap((prev) => ({ ...prev, [query.id]: resp.data.data }));
        } catch (err) {
          // Optionally handle error
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedQueryIndices, queries]);

  // Build chart objects for all selected queries
  const charts = selectedQueryIndices.map((idx) => {
    const query = queries[idx];
    const fullData = previewDataMap[query.id] || [];
    const sanitizedData = sanitizeData(fullData);
    return {
      id: query.id,
      title: query.title,
      data: sanitizedData, // Always full data
      sql: query.sql,
      previewData: sanitizedData, // Always full data for preview
      qualityData: qualityMap ? qualityMap[query.id] : undefined,
    };
  });

  return (
    <Box>
      <VisualizationDashboard
        charts={charts}
        onRemoveChart={(chartId) => {
          const newIndices = selectedQueryIndices.filter(
            (idx) => queries[idx].id !== chartId
          );
          setSelectedQueryIndices(newIndices);
        }}
        onTitleChange={(chartId, newTitle) => {
          const queryIndex = queries.findIndex((q) => q.id === chartId);
          if (queryIndex !== -1) {
            queries[queryIndex].title = newTitle;
          }
        }}
        onSQLUpdate={onSQLUpdate}
        previewDataMap={previewDataMap}
        qualityMap={qualityMap}
        isEditMode={isEditMode}
        setIsEditMode={setIsEditMode}
      />
    </Box>
  );
}

export default RightPanelTabs;
