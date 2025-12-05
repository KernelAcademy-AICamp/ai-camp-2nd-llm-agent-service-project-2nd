/**
 * Relationship API Tests
 * TDD: Red phase - 테스트 먼저 작성
 */

import { analyzeRelationships } from '../relationship';
import { PersonRole, RelationshipType } from '@/types/relationship';

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

describe('Relationship API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('test-token');
  });

  describe('analyzeRelationships', () => {
    it('should call correct endpoint with POST method', async () => {
      const mockResponse = {
        status: 'success',
        result: {
          nodes: [],
          edges: [],
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockResponse)),
      });

      await analyzeRelationships('테스트 텍스트');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];

      expect(url).toContain('/l-demo/analyze/relationships');
      expect(options.method).toBe('POST');
    });

    it('should send text in request body', async () => {
      const mockResponse = {
        status: 'success',
        result: { nodes: [], edges: [] },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockResponse)),
      });

      const testText = '김철수와 이영희는 배우자 관계입니다.';
      await analyzeRelationships(testText);

      const [, options] = mockFetch.mock.calls[0];
      const body = JSON.parse(options.body as string);

      expect(body.text).toBe(testText);
    });

    it('should include auth token in headers', async () => {
      const mockResponse = {
        status: 'success',
        result: { nodes: [], edges: [] },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () => Promise.resolve(JSON.stringify(mockResponse)),
      });

      await analyzeRelationships('테스트');

      const [, options] = mockFetch.mock.calls[0];

      expect(options.headers['Authorization']).toBe('Bearer test-token');
    });

    it('should return RelationshipGraph on success', async () => {
      const mockResult = {
        nodes: [
          {
            id: 'person-0',
            name: '김철수',
            role: PersonRole.PLAINTIFF,
            side: 'plaintiff' as const,
            color: '#4CAF50',
          },
          {
            id: 'person-1',
            name: '이영희',
            role: PersonRole.DEFENDANT,
            side: 'defendant' as const,
            color: '#F44336',
          },
        ],
        edges: [
          {
            source: 'person-0',
            target: 'person-1',
            relationship: RelationshipType.SPOUSE,
            label: '배우자',
            confidence: 0.95,
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

      const response = await analyzeRelationships('테스트');

      expect(response.status).toBe(200);
      expect(response.data).toBeDefined();
      expect(response.data?.nodes).toHaveLength(2);
      expect(response.data?.edges).toHaveLength(1);
      expect(response.data?.nodes[0].name).toBe('김철수');
    });

    it('should return error on API failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              detail: '서버 오류가 발생했습니다.',
            })
          ),
      });

      const response = await analyzeRelationships('테스트');

      expect(response.status).toBe(500);
      expect(response.error).toBe('서버 오류가 발생했습니다.');
      expect(response.data).toBeUndefined();
    });

    it('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const response = await analyzeRelationships('테스트');

      expect(response.status).toBe(0);
      expect(response.error).toBe('Network error');
    });

    it('should return empty graph when no relationships found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        text: () =>
          Promise.resolve(
            JSON.stringify({
              status: 'success',
              result: { nodes: [], edges: [] },
            })
          ),
      });

      const response = await analyzeRelationships('관계 정보가 없는 텍스트');

      expect(response.status).toBe(200);
      expect(response.data?.nodes).toHaveLength(0);
      expect(response.data?.edges).toHaveLength(0);
    });
  });
});
