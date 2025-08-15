/**
 * MultiQuerySelector
 * Dropdown selector for choosing multiple SQL queries, with data preview fetching.
 *
 * Props:
 *   queries (array): List of query objects with id, sql, and title
 *   selectedQueryIndices (array): Indices of selected queries
 *   setSelectedQueryIndices (function): Setter for selectedQueryIndices
 *   previewDataMap (object): Map of query id to preview data
 *   setPreviewDataMap (function): Setter for previewDataMap
 *   qualityMap (object): Map of query id to quality info
 *   setQualityMap (function): Setter for qualityMap
 */
import React, { useEffect } from 'react';
import { Box, FormControl, InputLabel, Select, MenuItem, Checkbox, ListItemText } from '@mui/material';
import axios from 'axios';

function MultiQuerySelector({
  queries,
  selectedQueryIndices,
  setSelectedQueryIndices,
  previewDataMap,
  setPreviewDataMap,
  qualityMap,
  setQualityMap,
}) {
  useEffect(() => {
    selectedQueryIndices.forEach(async (idx) => {
      const id = queries[idx].id;
      if (!previewDataMap.hasOwnProperty(id)) {
        setPreviewDataMap(prev => ({ ...prev, [id]: undefined }));
        if (queries[idx]) {
          const sql = queries[idx].sql;
          try {
            const resp = await axios.post('/api/transform/preview/', { sql_code: sql, limit: 10 });
             setPreviewDataMap(prev => ({ ...prev, [queries[idx].id]: resp.data.preview }))
          } catch (err) {
             setPreviewDataMap((prev) => ({ ...prev, [id]: [] }));
          }
        }
      }
    });
  }, [selectedQueryIndices, queries, previewDataMap, setPreviewDataMap]);

  const handleChange = (e) => {
    setSelectedQueryIndices(e.target.value);
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <FormControl
        size="small"
        variant="outlined"
        sx={{
          m: 1,
          width: 160,
          fontSize: 8,
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        }}
      >
        <InputLabel id="multi-query-label">SQL request</InputLabel>
        <Select
          labelId="multi-query-label"
          multiple
          label="SQL request"
          value={selectedQueryIndices}
          onChange={handleChange}
          renderValue={(selected) =>
            selected.map((idx) => queries[idx]?.title).join(', ')
          }
          aria-label="Select SQL requests"
        >
          {queries.map((q, index) => (
            <MenuItem key={index} value={index}>
              <Checkbox checked={selectedQueryIndices.indexOf(index) > -1} size="small" inputProps={{ 'aria-label': `Select query ${q.title}` }} />
              <ListItemText primary={q.title} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}

export default MultiQuerySelector;
