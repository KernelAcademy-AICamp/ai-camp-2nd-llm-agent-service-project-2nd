import Head from 'next/head';
import { useCallback, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import ClientUploadCard from '@/components/portal/ClientUploadCard';

type UploadStatus = 'idle' | 'success' | 'error';

const DEFAULT_FIRM_NAME = 'Legal Evidence Hub 로펌';
const DEFAULT_CASE_NAME = '의뢰인 사건';

export default function ClientEvidencePortalPage() {
    const router = useRouter();
    const [status, setStatus] = useState<UploadStatus>('idle');
    const [uploadedCount, setUploadedCount] = useState(0);
    const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

    const { firmName, caseName } = useMemo(() => {
        const rawFirm = router.query.firm;
        const rawCase = router.query.case;

        const safeFirm = typeof rawFirm === 'string' && rawFirm.trim().length > 0 ? rawFirm : DEFAULT_FIRM_NAME;
        const safeCase = typeof rawCase === 'string' && rawCase.trim().length > 0 ? rawCase : DEFAULT_CASE_NAME;

        return { firmName: safeFirm, caseName: safeCase };
    }, [router.query.firm, router.query.case]);

    const handleFilesSelected = useCallback((files: File[]) => {
        if (files.length === 0) {
            setStatus('error');
            setUploadedFiles([]);
            return;
        }

        setUploadedCount(files.length);
        setUploadedFiles(files.map((file) => file.name));
        setStatus('success');
    }, []);

    return (
        <div className="min-h-screen bg-gradient-to-b from-calm-grey to-white flex items-center justify-center px-6 py-12">
            <Head>
                <title>의뢰인 증거 제출 | Legal Evidence Hub</title>
            </Head>

            <ClientUploadCard
                status={status}
                uploadedCount={uploadedCount}
                uploadedFiles={uploadedFiles}
                onSelectFiles={handleFilesSelected}
                firmName={firmName}
                caseName={caseName}
            />
        </div>
    );
}
