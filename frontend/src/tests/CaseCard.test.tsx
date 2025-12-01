import { render, screen } from '@testing-library/react';
import CaseCard from '@/components/cases/CaseCard';
import { Case } from '@/types/case';
import '@testing-library/jest-dom';

const mockCase: Case = {
    id: '1',
    title: 'Test Case',
    clientName: 'Test Client',
    status: 'open',
    evidenceCount: 5,
    draftStatus: 'ready',
    lastUpdated: '2024-01-01T00:00:00Z',
};

describe('CaseCard', () => {
    it('renders case information correctly', () => {
        render(<CaseCard caseData={mockCase} />);

        expect(screen.getByText('Test Case')).toBeInTheDocument();
        expect(screen.getByText('Test Client')).toBeInTheDocument();
        expect(screen.getByText('진행 중')).toBeInTheDocument();
        expect(screen.getByText('증거 5건')).toBeInTheDocument();
        expect(screen.getByText('준비됨')).toBeInTheDocument();
    });
});
