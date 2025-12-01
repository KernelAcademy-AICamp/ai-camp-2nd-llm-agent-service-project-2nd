import { downloadDraftAsDocx } from '@/services/documentService';

describe('Plan 3.12 - Draft 다운로드 외부 변환 API 연동', () => {
    const originalFetch = global.fetch;
    const originalCreateObjectURL = URL.createObjectURL;
    const originalRevokeObjectURL = URL.revokeObjectURL;

    afterEach(() => {
        jest.restoreAllMocks();
        global.fetch = originalFetch;
        Object.defineProperty(URL, 'createObjectURL', { writable: true, configurable: true, value: originalCreateObjectURL });
        Object.defineProperty(URL, 'revokeObjectURL', { writable: true, configurable: true, value: originalRevokeObjectURL });
    });

    test('DOCX 다운로드는 변환 API 호출 후 Blob 다운로드를 트리거해야 한다', async () => {
        const convertedBlob = new Blob(['docx'], {
            type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        });

        const fetchMock = jest.fn().mockResolvedValue({
            ok: true,
            blob: jest.fn().mockResolvedValue(convertedBlob),
        } as unknown as Response);
        global.fetch = fetchMock as unknown as typeof fetch;

        const createObjectURLSpy = jest.fn().mockReturnValue('blob:docx');
        Object.defineProperty(URL, 'createObjectURL', { writable: true, configurable: true, value: createObjectURLSpy });
        Object.defineProperty(URL, 'revokeObjectURL', {
            writable: true,
            configurable: true,
            value: jest.fn(),
        });
        const appendSpy = jest.spyOn(document.body, 'appendChild');

        await downloadDraftAsDocx('docx-ready text', 'case-external-api');

        expect(fetchMock).toHaveBeenCalledWith(
            '/api/cases/case-external-api/draft/convert?format=docx',
            expect.objectContaining({
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: 'docx-ready text' }),
            }),
        );

        const appendedAnchor = appendSpy.mock.calls.at(-1)?.[0] as HTMLAnchorElement;
        expect(appendedAnchor.download).toContain('case-external-api');
        expect(appendedAnchor.download).toContain('.docx');
        expect(createObjectURLSpy).toHaveBeenCalledWith(convertedBlob);
    });

    test('HWP 포맷도 변환 API를 통해 .hwp 파일로 다운로드되어야 한다', async () => {
        const hwpBlob = new Blob(['hwp'], { type: 'application/x-hwp' });
        const fetchMock = jest.fn().mockResolvedValue({
            ok: true,
            blob: jest.fn().mockResolvedValue(hwpBlob),
        } as unknown as Response);
        global.fetch = fetchMock as unknown as typeof fetch;

        Object.defineProperty(URL, 'createObjectURL', {
            writable: true,
            configurable: true,
            value: jest.fn().mockReturnValue('blob:hwp'),
        });
        Object.defineProperty(URL, 'revokeObjectURL', {
            writable: true,
            configurable: true,
            value: jest.fn(),
        });
        const appendSpy = jest.spyOn(document.body, 'appendChild');

        // broaden signature to allow format parameter until implementation catches up
        await downloadDraftAsDocx('한글 문서 본문', 'case-external-api', 'hwp');

        expect(fetchMock).toHaveBeenCalledWith(
            '/api/cases/case-external-api/draft/convert?format=hwp',
            expect.any(Object),
        );

        const appendedAnchor = appendSpy.mock.calls.at(-1)?.[0] as HTMLAnchorElement;
        expect(appendedAnchor.download).toContain('.hwp');
    });
});
