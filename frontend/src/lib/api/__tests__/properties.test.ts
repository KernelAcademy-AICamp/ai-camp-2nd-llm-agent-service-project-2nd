/**
 * Properties API Tests
 * TDD: Red phase - 테스트 먼저 작성
 */

import { analyzeImpact } from '../properties';
import { ImpactDirection, ConfidenceLevel } from '@/types/property';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

describe('Properties API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('test-token');
  });

  describe('analyzeImpact', () => {
    it('should call correct endpoint with POST method', async () => {
      const mockResponse = {
        status: 'success',
        result: {
          plaintiff_ratio: 60,
          defendant_ratio: 40,
          evidence_impacts: [],
          confidence_level: 'high',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockResponse)),
      });

      await analyzeImpact({ case_id: 'test-case', evidences: [] });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];

      expect(url).toContain('/l-demo/analyze/impact');
      expect(options.method).toBe('POST');
    });

    it('should send case_id and evidences in request body', async () => {
      const mockResponse = {
        status: 'success',
        result: {
          plaintiff_ratio: 50,
          defendant_ratio: 50,
          evidence_impacts: [],
          confidence_level: 'medium',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockResponse)),
      });

      const testEvidences = [
        { id: 'ev-001', type: '카카오톡', content: '대화 내용' },
      ];
      await analyzeImpact({ case_id: 'case-123', evidences: testEvidences });

      const [, options] = mockFetch.mock.calls[0];
      const body = JSON.parse(options.body as string);

      expect(body.case_id).toBe('case-123');
      expect(body.evidences).toEqual(testEvidences);
    });

    it('should return DivisionPrediction on success', async () => {
      const mockResult = {
        plaintiff_ratio: 60.5,
        defendant_ratio: 39.5,
        evidence_impacts: [
          {
            evidence_id: 'ev-001',
            evidence_type: '카카오톡',
            impact_percent: 8.5,
            direction: ImpactDirection.PLAINTIFF_FAVOR,
            reason: '외도 증거',
          },
        ],
        confidence_level: ConfidenceLevel.HIGH,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              status: 'success',
              result: mockResult,
            })
          ),
      });

      const response = await analyzeImpact({ case_id: 'test', evidences: [] });

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.plaintiff_ratio).toBe(60.5);
      expect(response.data?.defendant_ratio).toBe(39.5);
      expect(response.data?.evidence_impacts).toHaveLength(1);
      expect(response.data?.confidence_level).toBe(ConfidenceLevel.HIGH);
    });

    it('should return error on API failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              detail: '분석 중 오류가 발생했습니다.',
            })
          ),
      });

      const response = await analyzeImpact({ case_id: 'test', evidences: [] });

      expect(response.status).toBe(500);
      expect(response.error).toBe('분석 중 오류가 발생했습니다.');
      expect(response.data).toBeUndefined();
    });

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const response = await analyzeImpact({ case_id: 'test', evidences: [] });

      expect(response.status).toBe(0);
      expect(response.error).toBe('Network error');
    });

    it('should handle similar_cases in response', async () => {
      const mockResult = {
        plaintiff_ratio: 55,
        defendant_ratio: 45,
        evidence_impacts: [],
        confidence_level: ConfidenceLevel.MEDIUM,
        similar_cases: [
          {
            case_id: 'similar-001',
            case_name: '유사 판례',
            similarity_score: 0.85,
            plaintiff_ratio: 55,
            defendant_ratio: 45,
            summary: '비슷한 사건',
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              status: 'success',
              result: mockResult,
            })
          ),
      });

      const response = await analyzeImpact({ case_id: 'test', evidences: [] });

      expect(response.data?.similar_cases).toHaveLength(1);
      expect(response.data?.similar_cases?.[0].similarity_score).toBe(0.85);
    });
  });
});
