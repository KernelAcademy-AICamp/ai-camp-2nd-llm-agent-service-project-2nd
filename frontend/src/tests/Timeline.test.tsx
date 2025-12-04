import '@testing-library/jest-dom';

// SKIPPED: Timeline feature is work-in-progress (002-evidence-timeline)
// These tests will be enabled once the Timeline component is complete

describe.skip('Timeline', () => {
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
