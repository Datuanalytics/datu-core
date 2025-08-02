// src/components/VisualizationDashboard.jsx
import React, { useState, useLayoutEffect, useRef, useEffect } from 'react';
import { Box } from '@mui/material';
import { Responsive, WidthProvider } from 'react-grid-layout';
import ChartTile from './ChartTile';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import ErrorBoundary from './ErrorBoundary';

const ResponsiveGridLayout = WidthProvider(Responsive);
const LOCAL_STORAGE_KEY = 'myDashboardLayouts';

// Default dimensions for a new chart layout item.
const DEFAULT_W = 12; // full width (this could be adjusted if you want different default widths).
const DEFAULT_H = 1;  // one grid unit high.

function getMaxY(layoutItems) {
  // Compute the bottom-most edge of the current grid.
  let maxY = 0;
  layoutItems.forEach(item => {
    const bottomY = item.y + item.h;
    if (bottomY > maxY) maxY = bottomY;
  });
  return maxY;
}

// Modified generator: 
// - currentLayouts: current array of layout objects already assigned.
// - charts: full list of charts.
function generateLayouts(charts, currentLayouts = null) {
  // Start with existing layout if provided, otherwise an empty array.
  const layout = currentLayouts ? [...currentLayouts] : [];

  // Create a Set of IDs already positioned.
  const positionedChartIds = new Set(layout.map(item => item.i));

  // Determine the next available y coordinate (start new charts at this row).
  // Use 'let' here because we want to update it.
  let nextAvailableY = getMaxY(layout);

  // For each chart in the list of charts:
  charts.forEach((chart) => {
    if (!positionedChartIds.has(chart.id)) {
      // Chart is new — add it at the next available position.
      layout.push({
        i: chart.id,
        x: 0,       // default x position; user can reposition this later.
        y: nextAvailableY, // position at the next available row.
        w: DEFAULT_W,
        h: DEFAULT_H,
        minW: DEFAULT_W,
        minH: DEFAULT_H,
      });
      // If you want each new chart on its own row, then increment for subsequent charts.
      nextAvailableY += DEFAULT_H;
    }
  });

  return layout;
}

function VisualizationDashboard({ charts, onRemoveChart, onTitleChange, onSQLUpdate, previewDataMap, qualityMap, isEditMode }) {
  const [layouts, setLayouts] = useState({});
  const containerRef = useRef(null);

  // Define the minimum grid row height (in pixels)
  const MIN_CHART_HEIGHT = 150;
  const [computedRowHeight, setComputedRowHeight] = useState(MIN_CHART_HEIGHT);

  useLayoutEffect(() => {
    if (containerRef.current) {
      const containerHeight = containerRef.current.clientHeight - 64;
      if (charts.length === 1) {
        setComputedRowHeight(containerHeight);
      } else if (charts.length > 1) {
        const idealHeight = containerHeight / charts.length;
        setComputedRowHeight(idealHeight < MIN_CHART_HEIGHT ? MIN_CHART_HEIGHT : idealHeight);
      }
    }
  }, [charts]);

  // When charts change, merge new charts into the existing layout only if chart IDs have changed.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    const currentLayouts = layouts.lg || [];
    const currentIds = new Set(currentLayouts.map(item => item.i));
    const chartIds = new Set(charts.map(chart => chart.id));
    // Only update layout if chart IDs have changed (added/removed)
    const idsAreEqual = currentIds.size === chartIds.size && [...currentIds].every(id => chartIds.has(id));
    if (!idsAreEqual) {
      const newLayout = generateLayouts(charts, currentLayouts);
      const newLayouts = {
        lg: newLayout,
        md: newLayout,
        sm: newLayout,
        xs: newLayout,
        xxs: newLayout,
      };
      setLayouts(newLayouts);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newLayouts));
    }
    // else: do not update layout, preserve user changes
  }, [charts]);

  // Style for grid container – ensures the grid does not exceed container height.
  const gridContainerStyle = {
    height: '100%',
    maxHeight: '100%',
    overflowY: 'auto',
  };

  // Layout change handler persists layout changes.
  const handleLayoutChange = (currentLayout, allLayouts) => {
    setLayouts(allLayouts);
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(allLayouts));
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        minHeight: 'calc(100vh - 64px)',
        maxHeight: 'calc(100vh - 64px)',
        width: '100%',
        mx: 'auto',
        overflowY: 'auto',
      }}
    >
      {/* Design Mode toggle removed, now controlled from header */}
      <ErrorBoundary>
        <div style={gridContainerStyle}>
          <ResponsiveGridLayout
            className="layout"
            layouts={layouts}
            breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
            cols={{ lg: 12, md: 12, sm: 12, xs: 12, xxs: 12 }}
            rowHeight={computedRowHeight}
            isDraggable={isEditMode}
            isResizable={isEditMode}
            onLayoutChange={handleLayoutChange}
            compactType="vertical"
            preventCollision={!isEditMode}
          >
            {charts.map((chart) => (
              <div key={chart.id}>
                <ChartTile
                  chartId={chart.id}
                  title={chart.title}
                  data={chart.data}
                  sql={chart.sql}
                  previewData={chart.previewData}
                  onRemove={onRemoveChart}
                  onTitleChange={onTitleChange}
                  onSQLUpdate={onSQLUpdate}
                  qualityData={chart.qualityData}
                />
              </div>
            ))}
          </ResponsiveGridLayout>
        </div>
      </ErrorBoundary>
    </Box>
  );
}

export default VisualizationDashboard;
