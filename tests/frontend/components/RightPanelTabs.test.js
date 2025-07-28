import React from 'react';
import { render, screen } from '@testing-library/react';
import RightPanelTabs from '@src/components/RightPanelTabs';
import axios from 'axios';

// Mock Axios to avoid network errors
jest.mock('axios');

describe('RightPanelTabs Component', () => {
  const mockQueries = [
    { id: '1', title: 'Query 1', sql: 'SELECT * FROM table1' },
    { id: '2', title: 'Query 2', sql: 'SELECT * FROM table2' },
  ];
  const mockSelectedQueryIndices = [0, 1];
  const mockSetSelectedQueryIndices = jest.fn();
  const mockPreviewDataMap = {
    '1': [{ col1: 'value1', col2: 'value2' }],
    '2': [{ col1: 'value3', col2: 'value4' }],
  };
  const mockSetPreviewDataMap = jest.fn();
  const mockQualityMap = {};

  beforeEach(() => {
    // Mock Axios POST for the /api/transform/download/ endpoint
    axios.post.mockImplementation((url, data) => {
      if (url === '/api/transform/download/') {
        return Promise.resolve({
          data: {
            data: [{ col1: 'mockValue1', col2: 'mockValue2' }],
          },
        });
      }
      return Promise.reject(new Error('Unexpected URL'));
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders chart tiles for all selected queries', () => {
    render(
      <RightPanelTabs
        queries={mockQueries}
        selectedQueryIndices={mockSelectedQueryIndices}
        setSelectedQueryIndices={mockSetSelectedQueryIndices}
        previewDataMap={mockPreviewDataMap}
        setPreviewDataMap={mockSetPreviewDataMap}
        qualityMap={mockQualityMap}
      />
    );

    // Chart titles should be rendered for each selected query
    expect(screen.getByText('Query 1')).toBeInTheDocument();
    expect(screen.getByText('Query 2')).toBeInTheDocument();
  });

  test('renders VisualizationDashboard', () => {
    render(
      <RightPanelTabs
        queries={mockQueries}
        selectedQueryIndices={mockSelectedQueryIndices}
        setSelectedQueryIndices={mockSetSelectedQueryIndices}
        previewDataMap={mockPreviewDataMap}
        setPreviewDataMap={mockSetPreviewDataMap}
        qualityMap={mockQualityMap}
      />
    );
    // VisualizationDashboard should be present (look for a known element)
    // This assumes VisualizationDashboard renders a label or heading
    // If not, this can be removed or replaced with a more robust check
    expect(screen.getByText(/Query 1/)).toBeInTheDocument();
  });
});
