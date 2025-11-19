import { render, screen, fireEvent } from '@testing-library/react';
import Timeline from '@/components/evidence/Timeline';
import { Evidence } from '@/types/evidence';
import '@testing-library/jest-dom';

const mockEvidence: Evidence[] = [
    {
        id: '1',
        caseId: 'case1',
        filename: 'record.mp3',
        type: 'audio',
        status: 'completed',
        uploadDate: '2024-05-01T10:00:00Z',
        summary: 'First evidence summary',
        size: 1000,
    },
    {
        id: '2',
        caseId: 'case1',
        filename: 'chat.txt',
        type: 'text',
        status: 'completed',
        uploadDate: '2024-05-02T15:00:00Z',
        summary: 'Second evidence summary',
        size: 2000,
    },
];

describe('Timeline', () => {
    it('renders timeline items sorted by date', () => {
        render(<Timeline items={mockEvidence} onSelect={jest.fn()} />);

        expect(screen.getByText('First evidence summary')).toBeInTheDocument();
        expect(screen.getByText('Second evidence summary')).toBeInTheDocument();
        expect(screen.getByText('2024. 5. 1.')).toBeInTheDocument(); // Date formatting check
    });

    it('calls onSelect when an item is clicked', () => {
        const handleSelect = jest.fn();
        render(<Timeline items={mockEvidence} onSelect={handleSelect} />);

        fireEvent.click(screen.getByText('First evidence summary'));
        expect(handleSelect).toHaveBeenCalledWith('1');
    });

    it('renders empty state when no items provided', () => {
        render(<Timeline items={[]} onSelect={jest.fn()} />);
        expect(screen.getByText('표시할 타임라인이 없습니다.')).toBeInTheDocument();
    });
});
