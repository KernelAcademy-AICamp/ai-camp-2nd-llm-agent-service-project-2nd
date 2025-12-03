import '@testing-library/jest-dom';

// Use mocked evidence API across tests to avoid network calls from CaseDetail flows
jest.mock('@/lib/api/evidence', () => {
  const mockEvidenceList = [
    {
      id: 'evidence-1',
      case_id: 'case-123',
      type: 'audio',
      filename: '녹취록_20240501.mp3',
      s3_key: 'cases/case-123/raw/evidence-1.mp3',
      timestamp: '2024-05-01T10:00:00Z',
      ai_summary: '상대방의 협박성 발언이 포함된 녹취.',
      labels: ['폭언', '협박'],
      created_at: '2024-05-02T00:00:00Z',
    },
    {
      id: 'evidence-2',
      case_id: 'case-123',
      type: 'text',
      filename: '카카오톡_대화내역.txt',
      s3_key: 'cases/case-123/raw/evidence-2.txt',
      timestamp: '2024-05-01T12:00:00Z',
      ai_summary: '돌봄 소홀을 인정하는 메시지.',
      labels: ['돌봄소홀'],
      created_at: '2024-05-02T00:10:00Z',
    },
  ];

  return {
    getEvidence: jest.fn(async () => ({
      data: { evidence: mockEvidenceList, total: mockEvidenceList.length },
      error: null,
      status: 200,
    })),
    getEvidenceById: jest.fn(async (id) => ({
      data: mockEvidenceList.find((item) => item.id === id),
      error: null,
      status: 200,
    })),
    getPresignedUploadUrl: jest.fn(async (caseId, filename, contentType) => ({
      data: {
        upload_url: 'https://example.com/upload',
        evidence_temp_id: 'temp-123',
        s3_key: `cases/${caseId}/raw/${filename}`,
        fields: { 'Content-Type': contentType },
      },
      error: null,
      status: 200,
    })),
    uploadToS3: jest.fn(async (_url, _file, onProgress) => {
      if (onProgress) {
        onProgress({ loaded: 100, total: 100, percent: 100 });
      }
      return true;
    }),
    notifyUploadComplete: jest.fn(async (request) => ({
      data: {
        evidence_id: 'evidence-new',
        case_id: request.case_id,
        filename: request.s3_key.split('/').pop() || 'uploaded-file',
        s3_key: request.s3_key,
        status: 'queued',
        created_at: new Date().toISOString(),
      },
      error: null,
      status: 200,
    })),
    deleteEvidence: jest.fn(async () => ({
      data: undefined,
      error: null,
      status: 200,
    })),
  };
});
