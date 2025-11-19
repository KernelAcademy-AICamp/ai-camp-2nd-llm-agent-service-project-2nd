import { UploadCloud, ShieldCheck, Loader2 } from 'lucide-react';
import clsx from 'clsx';

type UploadStatus = 'idle' | 'uploading' | 'success' | 'error';

interface ClientUploadCardProps {
    status: UploadStatus;
    uploadedCount: number;
    uploadedFiles: string[];
    onSelectFiles: (files: File[]) => void;
    firmName: string;
    caseName: string;
}

const FEEDBACK_TEXT: Record<UploadStatus, (count: number) => { message: string; tone: string }> = {
    idle: () => ({
        message: '업로드 준비되었습니다. 증거 파일을 선택해 주세요.',
        tone: 'text-gray-500',
    }),
    uploading: (count) => ({
        message: `${count}개 파일 업로드 중... 안전하게 암호화되는 중입니다.`,
        tone: 'text-accent font-semibold',
    }),
    success: (count) => ({
        message: `파일 ${count}개가 안전하게 전송되었습니다.`,
        tone: 'text-success-green font-semibold',
    }),
    error: () => ({
        message: '업로드에 실패했습니다. 다시 시도해 주세요.',
        tone: 'text-semantic-error font-semibold',
    }),
};

export default function ClientUploadCard({ status, uploadedCount, uploadedFiles, onSelectFiles, firmName, caseName }: ClientUploadCardProps) {
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files ? Array.from(event.target.files) : [];
        onSelectFiles(files);
        event.target.value = '';
    };

    const feedback = FEEDBACK_TEXT[status](uploadedCount);

    return (
        <div className="w-full max-w-2xl bg-white border border-gray-100 shadow-xl rounded-3xl p-10 space-y-8">
            <header className="text-center space-y-3">
                <div className="inline-flex items-center justify-center px-4 py-1 rounded-full bg-accent/10 text-accent text-xs font-semibold tracking-[0.25em] uppercase">
                    Legal Evidence Hub
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-deep-trust-blue">의뢰인 증거 제출 포털</h1>
                    <p className="text-gray-600 mt-2">
                        {`${firmName}의 '${caseName}'을 위한 증거 제출 페이지입니다.`}
                    </p>
                    <p className="text-gray-500">
                        모든 파일은 종단간 암호화되어 담당 변호사에게만 안전하게 전송됩니다.
                    </p>
                    <p className="text-sm text-gray-500">
                        안내: 아래 영역에 파일을 끌어다 놓거나 클릭하여 업로드할 수 있습니다.
                    </p>
                </div>
            </header>

            <div className="flex flex-col items-center text-gray-500 text-sm bg-calm-grey rounded-2xl p-4 space-y-2">
                <ShieldCheck className="w-5 h-5 text-deep-trust-blue" />
                <p>암호화된 연결로 업로드되며, 요청하신 목적 외에는 사용되지 않습니다.</p>
            </div>

            <label
                htmlFor="client-file-upload"
                data-testid="client-upload-zone"
                className={clsx(
                    'flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-200 bg-calm-grey/60 px-6 py-12 text-center cursor-pointer transition-all duration-200',
                    'hover:border-accent hover:bg-accent/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/30',
                )}
            >
                <input
                    id="client-file-upload"
                    type="file"
                    multiple
                    className="sr-only"
                    aria-label="증거 파일 업로드"
                    onChange={handleFileChange}
                />

                <UploadCloud className="w-12 h-12 text-accent mb-4" />
                <p className="text-lg font-semibold text-deep-trust-blue">파일을 끌어다 놓거나 클릭하여 업로드</p>
                <p className="text-sm text-gray-500 mt-2">PDF, 이미지, 음성, 텍스트 파일을 지원합니다.</p>
                <span className="mt-3 inline-flex items-center px-4 py-1.5 rounded-full bg-white shadow text-xs font-medium text-gray-600">
                    증거 파일 업로드
                </span>
            </label>

            <div className="space-y-2" aria-live="polite">
                {uploadedFiles.length > 0 ? (
                    <div
                        data-testid="uploaded-files-list"
                        className="rounded-2xl border border-gray-100 bg-white px-5 py-4"
                    >
                        <p className="text-sm font-medium text-deep-trust-blue mb-2">업로드된 파일</p>
                        <ul className="space-y-1 text-sm text-gray-700">
                            {uploadedFiles.map((name) => (
                                <li key={name} className="flex items-center gap-2">
                                    <span className="inline-block w-2 h-2 rounded-full bg-success-green" aria-hidden="true" />
                                    <span>{name}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ) : (
                    <p className="text-sm text-gray-400 text-center">업로드된 파일이 여기 표시됩니다.</p>
                )}
            </div>

            <div
                data-testid="upload-feedback"
                className={clsx(
                    'rounded-2xl px-5 py-4 text-center text-sm bg-calm-grey',
                    status === 'success' && 'bg-success-green/5 border border-success-green/40',
                    status === 'error' && 'bg-semantic-error/5 border border-semantic-error/40',
                )}
            >
                <p className={feedback.tone}>{feedback.message}</p>
                {status === 'uploading' && (
                    <div className="mt-3 flex items-center justify-center text-xs text-gray-500" role="status">
                        <Loader2 className="w-4 h-4 mr-2 animate-spin text-accent" />
                        <span>업로드 중...</span>
                    </div>
                )}
            </div>
        </div>
    );
}
