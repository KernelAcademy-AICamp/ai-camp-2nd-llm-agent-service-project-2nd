import { render, screen, fireEvent } from '@testing-library/react';
import EvidenceUpload from '@/components/evidence/EvidenceUpload';
import '@testing-library/jest-dom';

describe('EvidenceUpload', () => {
    it('renders upload area correctly', () => {
        const handleUpload = jest.fn();
        render(<EvidenceUpload onUpload={handleUpload} />);

        expect(screen.getByText(/파일을 끌어다 놓거나 클릭하여 업로드/i)).toBeInTheDocument();
    });

    it('calls onUpload when file is selected', () => {
        const handleUpload = jest.fn();
        render(<EvidenceUpload onUpload={handleUpload} />);

        const file = new File(['hello'], 'hello.png', { type: 'image/png' });
        // The label is linked to the input via htmlFor, so getByLabelText returns the input directly if it's correctly associated.
        // However, in my component: <input id="file-upload" ... /> <label htmlFor="file-upload">...</label>
        // getByLabelText should return the input. Let's verify.
        // Actually, the previousSibling logic was fragile.
        // Let's try getting by display value or just use the ID if possible, but testing-library prefers user-visible.
        // Since the input is hidden, we can use fireEvent on the input directly if we can find it. 
        // But getByLabelText should work for hidden inputs if associated.

        // Let's try a different approach: get the input by its ID using container.querySelector or similar if needed, 
        // but better: the input has id="file-upload".
        // Let's use: const input = document.getElementById('file-upload') as HTMLInputElement;
        // But that's not "React Testing Library" way.
        // The error said "Unable to fire a change event - please provide a DOM element".
        // This means `input` was null/undefined.

        // In EvidenceUpload.tsx:
        // <input ... id="file-upload" ... />
        // <label htmlFor="file-upload" ...> ... </label>

        // screen.getByLabelText(...) should return the input.
        // Let's trust getByLabelText.

        fireEvent.change(screen.getByLabelText(/파일을 끌어다 놓거나 클릭하여 업로드/i), { target: { files: [file] } });

        expect(handleUpload).toHaveBeenCalledTimes(1);
        expect(handleUpload).toHaveBeenCalledWith([file]);
    });
});
