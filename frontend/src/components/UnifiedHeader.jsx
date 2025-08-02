// src/components/UnifiedHeader.jsx
import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, Tooltip, Switch } from '@mui/material';
import { styled } from '@mui/material/styles';
import WysiwygIcon from '@mui/icons-material/Wysiwyg';
import SparklesIcon from '@mui/icons-material/AutoAwesome';
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

const LeftContainer = styled(Box)(() => ({
  display: 'flex',
  alignItems: 'center',
  gap: '0.4rem',
  flexShrink: 0,
}));

const CenterContainer = styled(Box)(() => ({
  flexGrow: 1,
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
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
  return (
    <StyledAppBar position="sticky" elevation={0}>
      <StyledToolbar>
        {/* Left: Logo */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Tooltip title={leftPanelVisible ? 'Hide sidebar' : 'Show sidebar'}>
            <IconButton onClick={toggleLeftPanel} size="small" sx={{ fontSize: 20, p: 0.9 }}>
              <WysiwygIcon sx={{ fontSize: 20 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title={isEditMode ? 'Disable chart size editing' : 'Enable chart size editing'}>
            <IconButton
              onClick={() => setIsEditMode(!isEditMode)}
              size="small"
              color={isEditMode ? 'primary' : 'default'}
              aria-label="Toggle design mode"
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
        </Box>
      </StyledToolbar>
    </StyledAppBar>
  );
}
