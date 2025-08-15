/**
 * UnifiedHeader
 * Application header bar with navigation, design mode toggle, and query selector.
 *
 * Props:
 *   hasQueries (boolean): Whether there are queries to select
 *   queries (array): List of query objects
 *   selectedQueryIndices (array): Indices of selected queries
 *   setSelectedQueryIndices (function): Setter for selectedQueryIndices
 *   previewDataMap (object): Map of query id to preview data
 *   setPreviewDataMap (function): Setter for previewDataMap
 *   qualityMap (object): Map of query id to quality info
 *   setQualityMap (function): Setter for qualityMap
 *   toggleLeftPanel (function): Toggle sidebar visibility
 *   leftPanelVisible (boolean): Whether sidebar is visible
 *   isEditMode (boolean): Whether dashboard is in edit mode
 *   setIsEditMode (function): Setter for isEditMode
 */
// src/components/UnifiedHeader.jsx
import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, Tooltip } from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import { useNavigate } from 'react-router-dom';
import { styled } from '@mui/material/styles';
import WysiwygIcon from '@mui/icons-material/Wysiwyg';

import MultiQuerySelector from './MultiQuerySelector';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';

const StyledAppBar = styled(AppBar)(() => ({
  backgroundColor: '#ffffff',
  color: '#000000',
  borderBottom: '1px solid #e5e7eb',
}));

const StyledToolbar = styled(Toolbar)(() => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  height: 45,
  minHeight: 45,
  paddingLeft: 4,
  paddingRight: 4,
}));



const RightContainer = styled(Box)(() => ({
  display: 'flex',
  alignItems: 'center',
  gap: '0.4rem',
  flexShrink: 0,
}));

export default function UnifiedHeader({
  hasQueries,
  queries,
  selectedQueryIndices,
  setSelectedQueryIndices,
  previewDataMap,
  setPreviewDataMap,
  qualityMap,
  setQualityMap,
  toggleLeftPanel,
  leftPanelVisible,
  isEditMode, 
  setIsEditMode, 
}) {
  const navigate = useNavigate();
  return (
    <StyledAppBar position="sticky" elevation={0}>
      <StyledToolbar>
        {/* Left: Logo */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Tooltip title={leftPanelVisible ? 'Hide sidebar' : 'Show sidebar'}>
            <IconButton onClick={toggleLeftPanel} size="small" sx={{ fontSize: 20, p: 0.9 }} aria-label={leftPanelVisible ? 'Hide sidebar' : 'Show sidebar'}>
              <WysiwygIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title={isEditMode ? 'Disable chart size editing' : 'Enable chart size editing'}>
            <IconButton
              onClick={() => setIsEditMode(!isEditMode)}
              size="small"
              color={isEditMode ? 'primary' : 'default'}
              aria-label={isEditMode ? 'Disable chart size editing' : 'Enable chart size editing'}
              sx={{ fontSize: 20, p: 0.9 }}
            >
              <DeveloperModeIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
          <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1.2rem' }}>
            AI Analyst
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '1.2rem' }}>
          {/* MultiQuerySelector first */}
          {hasQueries && (
            <>
              <RightContainer>
                <MultiQuerySelector
                  queries={queries}
                  selectedQueryIndices={selectedQueryIndices}
                  setSelectedQueryIndices={setSelectedQueryIndices}
                  previewDataMap={previewDataMap}
                  setPreviewDataMap={setPreviewDataMap}
                  qualityMap={qualityMap}
                  setQualityMap={setQualityMap}
                  sx={{ fontSize: '0.8rem' }}
                />
              </RightContainer>
            </>
          )}
          {/* Settings Icon for navigation to Data Source & Context page */}
          <Tooltip title="Settings & LLM Context">
            <IconButton
              size="small"
              sx={{ fontSize: 20, p: 0.9 }}
              onClick={() => navigate('/settings')}
              aria-label="Settings & LLM Context"
            >
              <SettingsIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
        </Box>
      </StyledToolbar>
    </StyledAppBar>
  );
}
