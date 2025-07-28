// src/components/MultiQuerySelector.js
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
          console.log(`[MultiQuerySelector] Fetching preview for query index ${idx} with SQL:`, sql);
          try {
            const resp = await axios.post('/api/transform/preview/', { sql_code: sql, limit: 10 });
            console.log(`[MultiQuerySelector] Preview fetched for query index ${id}:`, resp.data.preview);
            setPreviewDataMap(prev => ({ ...prev, [queries[idx].id]: resp.data.preview }))
          } catch (err) {
            console.error('Error fetching data preview for query', idx, err);
            // In case of error, mark as loaded (empty array) so the UI shows "No data returned"
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
        <InputLabel>SQL request</InputLabel>
        <Select
          multiple
          label="SQL request"
          value={selectedQueryIndices}
          onChange={handleChange}
          renderValue={(selected) =>
            selected.map((idx) => queries[idx]?.title).join(', ')
          }
        >
          {queries.map((q, index) => (
            <MenuItem key={index} value={index}>
              <Checkbox checked={selectedQueryIndices.indexOf(index) > -1} size="small" />
              <ListItemText primary={q.title} />
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}

export default MultiQuerySelector;
