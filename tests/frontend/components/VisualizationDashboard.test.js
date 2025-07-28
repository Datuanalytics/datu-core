import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import VisualizationDashboard from '@src/components/VisualizationDashboard';

describe('VisualizationDashboard Component', () => {
  const mockCharts = [
    { id: '1', title: 'Chart 1', data: [{ x: 1, y: 2 }] },
    { id: '2', title: 'Chart 2', data: [{ x: 3, y: 4 }] },
  ];
  const mockOnRemoveChart = jest.fn();
  const mockOnTitleChange = jest.fn();

  const theme = createTheme(); // Create a default Material-UI theme

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders charts correctly', () => {
    render(
      <ThemeProvider theme={theme}>
        <VisualizationDashboard
          charts={mockCharts}
          onRemoveChart={mockOnRemoveChart}
          onTitleChange={mockOnTitleChange}
          isEditMode={false}
        />
      </ThemeProvider>
    );

    expect(screen.getByText(/Chart 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Chart 2/i)).toBeInTheDocument();
  });

  test('calls onRemoveChart when a chart is removed', () => {
    render(
      <ThemeProvider theme={theme}>
        <VisualizationDashboard
          charts={mockCharts}
          onRemoveChart={mockOnRemoveChart}
          onTitleChange={mockOnTitleChange}
          isEditMode={false}
        />
      </ThemeProvider>
    );

    const removeButtons = screen.getAllByRole('button', { name: /Remove Chart/i });
    expect(removeButtons.length).toBe(2);

    fireEvent.click(removeButtons[0]);
    expect(mockOnRemoveChart).toHaveBeenCalledWith('1');
  });

  test('calls onTitleChange when a chart title is updated', () => {
    render(
      <ThemeProvider theme={theme}>
        <VisualizationDashboard
          charts={mockCharts}
          onRemoveChart={mockOnRemoveChart}
          onTitleChange={mockOnTitleChange}
          isEditMode={false}
        />
      </ThemeProvider>
    );

    const editButtons = screen.getAllByRole('button', { name: /Configure Chart/i });
    expect(editButtons.length).toBe(2);

    fireEvent.click(editButtons[0]);
    mockOnTitleChange('1', 'Updated Chart 1');
    expect(mockOnTitleChange).toHaveBeenCalledWith('1', 'Updated Chart 1');
  });
});
