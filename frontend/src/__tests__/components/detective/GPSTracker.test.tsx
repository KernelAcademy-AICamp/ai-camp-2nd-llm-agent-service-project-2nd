/**
 * Integration tests for GPSTracker Component
 * Task T083 - US5 Tests
 *
 * Tests for frontend/src/components/detective/GPSTracker.tsx:
 * - GPS coordinate display
 * - Map display
 * - Location tracking
 * - Save location functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock navigator.geolocation
const mockGeolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn(),
};

Object.defineProperty(global.navigator, 'geolocation', {
  value: mockGeolocation,
  writable: true,
});

// Mock Kakao Maps
jest.mock('@/lib/kakao-maps', () => ({
  initKakaoMap: jest.fn(),
  createMarker: jest.fn(),
  setCenter: jest.fn(),
}));

// Import component after mocks
import GPSTracker from '@/components/detective/GPSTracker';

describe('GPSTracker Component', () => {
  const mockOnLocationSave = jest.fn();
  const mockOnError = jest.fn();

  const defaultProps = {
    onLocationSave: mockOnLocationSave,
    onError: mockOnError,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Default successful geolocation mock
    mockGeolocation.getCurrentPosition.mockImplementation((success) =>
      success({
        coords: {
          latitude: 37.5665,
          longitude: 126.978,
          accuracy: 10,
        },
        timestamp: Date.now(),
      })
    );

    mockGeolocation.watchPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 37.5665,
          longitude: 126.978,
          accuracy: 10,
        },
        timestamp: Date.now(),
      });
      return 1; // watch ID
    });
  });

  describe('Initial Rendering', () => {
    test('should render component title', () => {
      render(<GPSTracker {...defaultProps} />);

      expect(screen.getByText('GPS 위치 추적')).toBeInTheDocument();
    });

    test('should render map container', () => {
      render(<GPSTracker {...defaultProps} />);

      const mapContainer = document.querySelector('#gps-map');
      expect(mapContainer).toBeInTheDocument();
    });

    test('should render get location button', () => {
      render(<GPSTracker {...defaultProps} />);

      expect(screen.getByText('현재 위치 가져오기')).toBeInTheDocument();
    });

    test('should show loading state initially', () => {
      render(<GPSTracker {...defaultProps} />);

      // May show "위치 확인 중..." or similar loading text
      expect(
        screen.getByText(/위치|GPS/i)
      ).toBeInTheDocument();
    });
  });

  describe('GPS Coordinates Display', () => {
    test('should display latitude after getting location', async () => {
      render(<GPSTracker {...defaultProps} />);

      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(screen.getByText(/37\.5665/)).toBeInTheDocument();
      });
    });

    test('should display longitude after getting location', async () => {
      render(<GPSTracker {...defaultProps} />);

      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(screen.getByText(/126\.978/)).toBeInTheDocument();
      });
    });

    test('should display accuracy information', async () => {
      render(<GPSTracker {...defaultProps} />);

      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(screen.getByText(/정확도|accuracy/i)).toBeInTheDocument();
      });
    });
  });

  describe('Location Tracking', () => {
    test('should start tracking when track button is clicked', async () => {
      render(<GPSTracker {...defaultProps} />);

      const trackButton = screen.getByText('위치 추적 시작');
      fireEvent.click(trackButton);

      expect(mockGeolocation.watchPosition).toHaveBeenCalled();
    });

    test('should stop tracking when stop button is clicked', async () => {
      render(<GPSTracker {...defaultProps} />);

      // Start tracking
      const trackButton = screen.getByText('위치 추적 시작');
      fireEvent.click(trackButton);

      await waitFor(() => {
        expect(screen.getByText('추적 중지')).toBeInTheDocument();
      });

      // Stop tracking
      fireEvent.click(screen.getByText('추적 중지'));

      expect(mockGeolocation.clearWatch).toHaveBeenCalled();
    });

    test('should show tracking indicator when active', async () => {
      render(<GPSTracker {...defaultProps} />);

      const trackButton = screen.getByText('위치 추적 시작');
      fireEvent.click(trackButton);

      await waitFor(() => {
        expect(screen.getByText(/추적 중/)).toBeInTheDocument();
      });
    });
  });

  describe('Save Location', () => {
    test('should call onLocationSave when save button is clicked', async () => {
      render(<GPSTracker {...defaultProps} />);

      // Get location first
      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(screen.getByText(/37\.5665/)).toBeInTheDocument();
      });

      // Save location
      fireEvent.click(screen.getByText('위치 저장'));

      expect(mockOnLocationSave).toHaveBeenCalledWith({
        latitude: 37.5665,
        longitude: 126.978,
        accuracy: 10,
        timestamp: expect.any(Number),
      });
    });

    test('should show success message after saving', async () => {
      render(<GPSTracker {...defaultProps} />);

      // Get location first
      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(screen.getByText(/37\.5665/)).toBeInTheDocument();
      });

      // Save location
      fireEvent.click(screen.getByText('위치 저장'));

      await waitFor(() => {
        expect(screen.getByText(/저장|완료/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('should show error when geolocation fails', async () => {
      mockGeolocation.getCurrentPosition.mockImplementation((_, error) =>
        error({ code: 1, message: 'User denied Geolocation' })
      );

      render(<GPSTracker {...defaultProps} />);

      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalled();
      });
    });

    test('should display error message in UI', async () => {
      mockGeolocation.getCurrentPosition.mockImplementation((_, error) =>
        error({ code: 1, message: 'User denied Geolocation' })
      );

      render(<GPSTracker {...defaultProps} />);

      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        expect(screen.getByText(/위치.*허용|접근.*거부/)).toBeInTheDocument();
      });
    });

    test('should handle geolocation unavailable', async () => {
      // Temporarily remove geolocation
      const originalGeolocation = navigator.geolocation;
      Object.defineProperty(navigator, 'geolocation', {
        value: undefined,
        writable: true,
      });

      render(<GPSTracker {...defaultProps} />);

      expect(screen.getByText(/GPS.*지원|위치.*사용/i)).toBeInTheDocument();

      // Restore geolocation
      Object.defineProperty(navigator, 'geolocation', {
        value: originalGeolocation,
        writable: true,
      });
    });
  });

  describe('Map Integration', () => {
    test('should have map container with correct id', () => {
      render(<GPSTracker {...defaultProps} />);

      const mapContainer = document.getElementById('gps-map');
      expect(mapContainer).toBeInTheDocument();
    });

    test('should apply correct dimensions to map', () => {
      render(<GPSTracker {...defaultProps} />);

      const mapContainer = document.getElementById('gps-map');
      expect(mapContainer).toHaveClass('h-64');
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <GPSTracker {...defaultProps} className="custom-tracker" />
      );

      expect(container.firstChild).toHaveClass('custom-tracker');
    });
  });

  describe('Timestamp Display', () => {
    test('should show timestamp when location is retrieved', async () => {
      render(<GPSTracker {...defaultProps} />);

      fireEvent.click(screen.getByText('현재 위치 가져오기'));

      await waitFor(() => {
        // Should display time in some format
        expect(screen.getByText(/\d{2}:\d{2}/)).toBeInTheDocument();
      });
    });
  });
});
