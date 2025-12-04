/**
 * Integration tests for FieldRecorder Component
 * Task T084 - US5 Tests
 *
 * Tests for frontend/src/components/detective/FieldRecorder.tsx:
 * - Record type selection
 * - Content input
 * - Photo attachment
 * - GPS integration
 * - Submit functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the API client
const mockCreateFieldRecord = jest.fn();
const mockUploadPhoto = jest.fn();

jest.mock('@/lib/api/detective-portal', () => ({
  createFieldRecord: (...args: unknown[]) => mockCreateFieldRecord(...args),
  uploadPhoto: (...args: unknown[]) => mockUploadPhoto(...args),
}));

// Mock GPSTracker component
jest.mock('@/components/detective/GPSTracker', () => {
  return function MockGPSTracker({
    onLocationSave,
  }: {
    onLocationSave: (location: {
      latitude: number;
      longitude: number;
    }) => void;
  }) {
    return (
      <div data-testid="gps-tracker">
        <button
          onClick={() =>
            onLocationSave({ latitude: 37.5665, longitude: 126.978 })
          }
        >
          Save Location
        </button>
      </div>
    );
  };
});

import FieldRecorder from '@/components/detective/FieldRecorder';

describe('FieldRecorder Component', () => {
  const mockCaseId = 'case-123';
  const mockOnRecordSaved = jest.fn();
  const mockOnError = jest.fn();

  const defaultProps = {
    caseId: mockCaseId,
    onRecordSaved: mockOnRecordSaved,
    onError: mockOnError,
  };

  // Create a mock file
  const createMockFile = (
    name: string,
    size: number,
    type: string
  ): File => {
    const file = new File(['content'], name, { type });
    Object.defineProperty(file, 'size', { value: size });
    return file;
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockCreateFieldRecord.mockResolvedValue({
      data: { id: 'record-123', success: true },
      error: null,
    });

    mockUploadPhoto.mockResolvedValue({
      data: { url: 'https://s3.amazonaws.com/photo.jpg' },
      error: null,
    });
  });

  describe('Initial Rendering', () => {
    test('should render component title', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('현장 기록')).toBeInTheDocument();
    });

    test('should render record type selector', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('기록 유형')).toBeInTheDocument();
    });

    test('should render content input', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByPlaceholderText(/내용|기록/i)).toBeInTheDocument();
    });

    test('should render GPS tracker', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByTestId('gps-tracker')).toBeInTheDocument();
    });

    test('should render submit button', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('기록 저장')).toBeInTheDocument();
    });
  });

  describe('Record Type Selection', () => {
    test('should have observation option', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('관찰 기록')).toBeInTheDocument();
    });

    test('should have photo option', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('사진 기록')).toBeInTheDocument();
    });

    test('should have note option', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('메모')).toBeInTheDocument();
    });

    test('should select record type on click', async () => {
      render(<FieldRecorder {...defaultProps} />);

      const observationOption = screen.getByText('관찰 기록');
      fireEvent.click(observationOption);

      await waitFor(() => {
        expect(observationOption.closest('button')).toHaveClass('bg-[var(--color-primary)]');
      });
    });
  });

  describe('Content Input', () => {
    test('should allow typing content', async () => {
      render(<FieldRecorder {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 관찰 내용');

      expect(textarea).toHaveValue('테스트 관찰 내용');
    });

    test('should show character count', async () => {
      render(<FieldRecorder {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트');

      expect(screen.getByText(/3.*자/)).toBeInTheDocument();
    });
  });

  describe('Photo Attachment', () => {
    test('should render photo upload area', () => {
      render(<FieldRecorder {...defaultProps} />);

      expect(screen.getByText('사진 추가')).toBeInTheDocument();
    });

    test('should show preview after selecting photo', async () => {
      render(<FieldRecorder {...defaultProps} />);

      const file = createMockFile('photo.jpg', 1024 * 1024, 'image/jpeg');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('photo.jpg')).toBeInTheDocument();
      });
    });

    test('should allow removing photo', async () => {
      render(<FieldRecorder {...defaultProps} />);

      const file = createMockFile('photo.jpg', 1024 * 1024, 'image/jpeg');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('photo.jpg')).toBeInTheDocument();
      });

      const removeButton = screen.getByLabelText('사진 제거');
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(screen.queryByText('photo.jpg')).not.toBeInTheDocument();
      });
    });
  });

  describe('GPS Integration', () => {
    test('should display GPS coordinates when saved', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Click the mock GPS save button
      fireEvent.click(screen.getByText('Save Location'));

      await waitFor(() => {
        expect(screen.getByText(/37\.5665/)).toBeInTheDocument();
        expect(screen.getByText(/126\.978/)).toBeInTheDocument();
      });
    });

    test('should show location saved indicator', async () => {
      render(<FieldRecorder {...defaultProps} />);

      fireEvent.click(screen.getByText('Save Location'));

      await waitFor(() => {
        expect(screen.getByText(/위치 저장됨/i)).toBeInTheDocument();
      });
    });
  });

  describe('Submit Functionality', () => {
    test('should call createFieldRecord with correct data', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Select record type
      fireEvent.click(screen.getByText('관찰 기록'));

      // Enter content
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 관찰 내용');

      // Save GPS location
      fireEvent.click(screen.getByText('Save Location'));

      // Submit
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(mockCreateFieldRecord).toHaveBeenCalledWith(mockCaseId, {
          record_type: 'observation',
          content: '테스트 관찰 내용',
          gps_lat: 37.5665,
          gps_lng: 126.978,
        });
      });
    });

    test('should call onRecordSaved on success', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Fill required fields
      fireEvent.click(screen.getByText('메모'));
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 메모');

      // Submit
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(mockOnRecordSaved).toHaveBeenCalledWith('record-123');
      });
    });

    test('should show success message after submission', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Fill required fields
      fireEvent.click(screen.getByText('메모'));
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 메모');

      // Submit
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(screen.getByText(/저장 완료|성공/i)).toBeInTheDocument();
      });
    });

    test('should disable submit button while saving', async () => {
      mockCreateFieldRecord.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(<FieldRecorder {...defaultProps} />);

      // Fill required fields
      fireEvent.click(screen.getByText('메모'));
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 메모');

      // Submit
      const submitButton = screen.getByText('기록 저장');
      fireEvent.click(submitButton);

      expect(submitButton).toBeDisabled();
    });
  });

  describe('Validation', () => {
    test('should require record type selection', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Try to submit without selecting type
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(screen.getByText(/기록 유형.*선택/i)).toBeInTheDocument();
      });
    });

    test('should require content', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Select type but no content
      fireEvent.click(screen.getByText('메모'));
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(screen.getByText(/내용.*입력/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('should call onError when API fails', async () => {
      mockCreateFieldRecord.mockResolvedValue({
        data: null,
        error: 'API Error',
      });

      render(<FieldRecorder {...defaultProps} />);

      // Fill required fields
      fireEvent.click(screen.getByText('메모'));
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 메모');

      // Submit
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalled();
      });
    });

    test('should display error message in UI', async () => {
      mockCreateFieldRecord.mockResolvedValue({
        data: null,
        error: 'Failed to save record',
      });

      render(<FieldRecorder {...defaultProps} />);

      // Fill required fields
      fireEvent.click(screen.getByText('메모'));
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 메모');

      // Submit
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(screen.getByText(/오류|실패/i)).toBeInTheDocument();
      });
    });
  });

  describe('Reset After Save', () => {
    test('should clear form after successful save', async () => {
      render(<FieldRecorder {...defaultProps} />);

      // Fill form
      fireEvent.click(screen.getByText('메모'));
      const textarea = screen.getByPlaceholderText(/내용|기록/i);
      await userEvent.type(textarea, '테스트 메모');

      // Submit
      fireEvent.click(screen.getByText('기록 저장'));

      await waitFor(() => {
        expect(textarea).toHaveValue('');
      });
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <FieldRecorder {...defaultProps} className="custom-recorder" />
      );

      expect(container.firstChild).toHaveClass('custom-recorder');
    });
  });
});
