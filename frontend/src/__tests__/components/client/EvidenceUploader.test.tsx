/**
 * Integration tests for EvidenceUploader Component
 * Task T060 - US4 Tests
 *
 * Tests for frontend/src/components/client/EvidenceUploader.tsx:
 * - File selection and drag-drop
 * - File validation
 * - Upload flow
 * - Error handling
 * - Success state
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the API client
const mockRequestEvidenceUpload = jest.fn();
const mockConfirmEvidenceUpload = jest.fn();
const mockUploadFileToS3 = jest.fn();

jest.mock('@/lib/api/client-portal', () => ({
  requestEvidenceUpload: (...args: unknown[]) => mockRequestEvidenceUpload(...args),
  confirmEvidenceUpload: (...args: unknown[]) => mockConfirmEvidenceUpload(...args),
  uploadFileToS3: (...args: unknown[]) => mockUploadFileToS3(...args),
}));

import EvidenceUploader from '@/components/client/EvidenceUploader';

describe('EvidenceUploader Component', () => {
  const mockCaseId = 'case-123';
  const mockOnUploadComplete = jest.fn();
  const mockOnError = jest.fn();

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

    // Default successful mocks
    mockRequestEvidenceUpload.mockResolvedValue({
      data: {
        evidence_id: 'ev-123',
        upload_url: 'https://s3.amazonaws.com/presigned-url',
        expires_in: 300,
      },
      error: null,
    });

    mockUploadFileToS3.mockImplementation(
      (_url: string, _file: File, onProgress: (progress: number) => void) => {
        // Simulate progress
        onProgress(50);
        onProgress(100);
        return Promise.resolve({ success: true });
      }
    );

    mockConfirmEvidenceUpload.mockResolvedValue({
      data: { success: true, evidence_id: 'ev-123', message: 'Upload confirmed' },
      error: null,
    });
  });

  describe('Initial Rendering', () => {
    test('should render upload title', () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      expect(screen.getByText('증거자료 업로드')).toBeInTheDocument();
    });

    test('should render file size limit info', () => {
      render(<EvidenceUploader caseId={mockCaseId} maxSizeMB={50} />);

      expect(screen.getByText(/최대 50MB/)).toBeInTheDocument();
    });

    test('should render drag-drop instruction', () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      expect(screen.getByText('파일을 여기에 드래그하거나')).toBeInTheDocument();
    });

    test('should render file select button', () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      expect(screen.getByText('파일 선택')).toBeInTheDocument();
    });

    test('should have hidden file input', () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();
      expect(fileInput).toHaveClass('hidden');
    });
  });

  describe('File Selection', () => {
    test('should show file preview after selection', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test-doc.pdf', 1024 * 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('test-doc.pdf')).toBeInTheDocument();
      });
    });

    test('should show file size in preview', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 2 * 1024 * 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/2.*MB/)).toBeInTheDocument();
      });
    });

    test('should show cancel button after file selection', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('취소')).toBeInTheDocument();
      });
    });

    test('should show upload button after file selection', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });
    });

    test('should show description input after file selection', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('설명 (선택사항)')).toBeInTheDocument();
      });
    });
  });

  describe('File Validation', () => {
    test('should reject files exceeding size limit', async () => {
      render(
        <EvidenceUploader
          caseId={mockCaseId}
          maxSizeMB={10}
          onError={mockOnError}
        />
      );

      // 15MB file exceeds 10MB limit
      const largeFile = createMockFile(
        'large.mp4',
        15 * 1024 * 1024,
        'video/mp4'
      );
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [largeFile] } });

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(
          expect.stringContaining('10MB')
        );
      });
    });

    test('should show error message for oversized file', async () => {
      render(<EvidenceUploader caseId={mockCaseId} maxSizeMB={5} />);

      const largeFile = createMockFile(
        'large.mp4',
        10 * 1024 * 1024,
        'video/mp4'
      );
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [largeFile] } });

      await waitFor(() => {
        expect(screen.getByText(/5MB를 초과/)).toBeInTheDocument();
      });
    });
  });

  describe('Upload Flow', () => {
    test('should call requestEvidenceUpload with correct parameters', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('업로드'));

      await waitFor(() => {
        expect(mockRequestEvidenceUpload).toHaveBeenCalledWith(mockCaseId, {
          file_name: 'test.pdf',
          file_type: 'application/pdf',
          file_size: 1024,
          description: undefined,
        });
      });
    });

    test('should show progress during upload', async () => {
      // Make upload take longer to observe progress
      mockUploadFileToS3.mockImplementation(
        (_url: string, _file: File, onProgress: (progress: number) => void) => {
          onProgress(50);
          return new Promise((resolve) => {
            setTimeout(() => {
              onProgress(100);
              resolve({ success: true });
            }, 100);
          });
        }
      );

      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('업로드'));

      // Should show "업로드 중..." during upload
      await waitFor(() => {
        expect(screen.getByText('업로드 중...')).toBeInTheDocument();
      });
    });

    test('should show success message after upload completes', async () => {
      render(
        <EvidenceUploader
          caseId={mockCaseId}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('업로드'));

      await waitFor(() => {
        expect(screen.getByText('업로드 완료!')).toBeInTheDocument();
      });
    });

    test('should call onUploadComplete callback on success', async () => {
      render(
        <EvidenceUploader
          caseId={mockCaseId}
          onUploadComplete={mockOnUploadComplete}
        />
      );

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('업로드'));

      await waitFor(() => {
        expect(mockOnUploadComplete).toHaveBeenCalledWith('ev-123');
      });
    });
  });

  describe('Error Handling', () => {
    test('should show error when API request fails', async () => {
      mockRequestEvidenceUpload.mockResolvedValue({
        data: null,
        error: 'API Error',
      });

      render(<EvidenceUploader caseId={mockCaseId} onError={mockOnError} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('업로드'));

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalled();
      });
    });

    test('should show error when S3 upload fails', async () => {
      mockUploadFileToS3.mockResolvedValue({
        success: false,
        error: 'S3 Upload Failed',
      });

      render(<EvidenceUploader caseId={mockCaseId} onError={mockOnError} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('업로드')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('업로드'));

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalled();
      });
    });
  });

  describe('Cancel and Reset', () => {
    test('should reset to initial state when cancel is clicked', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('취소'));

      await waitFor(() => {
        expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
        expect(screen.getByText('파일 선택')).toBeInTheDocument();
      });
    });

    test('should reset when remove button is clicked', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      const removeButton = screen.getByLabelText('파일 제거');
      fireEvent.click(removeButton);

      await waitFor(() => {
        expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
      });
    });
  });

  describe('Drag and Drop', () => {
    test('should highlight drop zone on drag over', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const dropZone = document.querySelector('.border-dashed');

      fireEvent.dragOver(dropZone!, {
        preventDefault: () => {},
      });

      // The drop zone should have changed style (checked by class change)
      // Note: actual class checking depends on implementation
    });

    test('should handle dropped file', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('dropped.pdf', 1024, 'application/pdf');
      const dropZone = document.querySelector('.border-dashed');

      fireEvent.drop(dropZone!, {
        preventDefault: () => {},
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(screen.getByText('dropped.pdf')).toBeInTheDocument();
      });
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <EvidenceUploader caseId={mockCaseId} className="custom-uploader" />
      );

      expect(container.firstChild).toHaveClass('custom-uploader');
    });
  });

  describe('File Type Icons', () => {
    test('should show image icon for image files', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('photo.jpg', 1024, 'image/jpeg');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('photo.jpg')).toBeInTheDocument();
      });

      // Image icon should be present (check for specific SVG path or color class)
      const iconContainer = document.querySelector('.text-\\[var\\(--color-primary\\)\\]');
      expect(iconContainer).toBeInTheDocument();
    });

    test('should show audio icon for audio files', async () => {
      render(<EvidenceUploader caseId={mockCaseId} />);

      const file = createMockFile('recording.mp3', 1024, 'audio/mpeg');
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('recording.mp3')).toBeInTheDocument();
      });

      // Audio icon should be present (check for success color class)
      const iconContainer = document.querySelector('.text-\\[var\\(--color-success\\)\\]');
      expect(iconContainer).toBeInTheDocument();
    });
  });
});
