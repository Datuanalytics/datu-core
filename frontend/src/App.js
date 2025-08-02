// src/App.js
import React, { useState } from 'react';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import theme from './theme';
import UnifiedHeader from './components/UnifiedHeader';
import FrontPage from './components/FrontPage';
import ChatPanel from './components/ChatPanel';
import RightPanelTabs from './components/RightPanelTabs';

function App() {
  const [started, setStarted] = useState(false);
  const [initialUserMessage, setInitialUserMessage] = useState('');
  const [queries, setQueries] = useState([]);
  const [selectedQueryIndices, setSelectedQueryIndices] = useState([]);
  const [previewDataMap, setPreviewDataMap] = useState({});
  const [qualityMap, setQualityMap] = useState({});

  // State for the selected tab in the header
  const [selectedTab, setSelectedTab] = useState(0);

  // NEW: State for left panel visibility (to implement "hide left panel" button)
  const [leftPanelVisible, setLeftPanelVisible] = useState(true);

  const [conversation, setConversation] = useState([]);
  const [isEditMode, setIsEditMode] = useState(false);

  const hasQueries = queries.length > 0;

  const handleStart = (userMessage) => {
    setInitialUserMessage(userMessage);
    setStarted(true);
  };

  const handleTabChange = (e, newValue) => {
    setSelectedTab(newValue);
  };

  // NEW: Toggle callback for left panel visibility
  const toggleLeftPanel = () => {
    setLeftPanelVisible((prev) => !prev);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <UnifiedHeader
        selectedTab={selectedTab}
        onTabChange={handleTabChange}
        hasQueries={hasQueries}
        queries={queries}
        selectedQueryIndices={selectedQueryIndices}
        setSelectedQueryIndices={setSelectedQueryIndices}
        previewDataMap={previewDataMap}
        setPreviewDataMap={setPreviewDataMap}
        qualityMap={qualityMap}
        setQualityMap={setQualityMap}
        toggleLeftPanel={toggleLeftPanel}
        leftPanelVisible={leftPanelVisible}
        isEditMode={isEditMode}
        setIsEditMode={setIsEditMode}
      />
      {!started ? (
        <FrontPage onStart={handleStart} />
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'row', height: 'calc(100vh - 64px)' }}>
          { leftPanelVisible && (
            <Box
              sx={{
                borderRight: '1px solid #e5e7eb',
                width: 400,
                display: 'flex',
                flexDirection: 'column',
              }}
              data-testid="chat-panel-container"
            >
              <ChatPanel
                setQueries={setQueries}
                initialUserMessage={initialUserMessage}
                conversation={conversation}
                setConversation={setConversation}
                selectedQueryIndices={selectedQueryIndices} // NEW: pass selection
                setSelectedQueryIndices={setSelectedQueryIndices} // NEW: pass setter
              />
            </Box>
          )}
          <Box sx={{ flex: 1, overflowY: 'auto', p: 1 }}>
            {/* MultiQuerySelector is moved to the top bar */}
            <RightPanelTabs
              selectedTab={selectedTab}
              queries={queries}
              selectedQueryIndices={selectedQueryIndices}
              setSelectedQueryIndices={setSelectedQueryIndices}
              previewDataMap={previewDataMap}
              setPreviewDataMap={setPreviewDataMap}
              qualityMap={qualityMap}
              isEditMode={isEditMode}
              setIsEditMode={setIsEditMode}
            />
          </Box>
        </Box>
      )}
    </ThemeProvider>
  );
}

export default App;
