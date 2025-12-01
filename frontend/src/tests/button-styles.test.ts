import * as fs from 'fs';
import * as path from 'path';

describe('Button Style Rules', () => {
    const projectRoot = path.resolve(__dirname, '../../');

    test('Primary CTA buttons should use accent color (#1ABC9C)', () => {
        const globalsCssPath = path.join(projectRoot, 'src/styles/globals.css');
        const cssContent = fs.readFileSync(globalsCssPath, 'utf-8');

        // Check for .btn-primary class definition
        const btnPrimaryMatch = cssContent.match(/\.btn-primary\s*{([^}]*)}/);
        expect(btnPrimaryMatch).not.toBeNull();

        if (btnPrimaryMatch) {
            const btnPrimaryContent = btnPrimaryMatch[1];
            // Should use bg-accent (which is #1ABC9C in tailwind config)
            expect(btnPrimaryContent).toMatch(/bg-accent/);
        }
    });

    test('design tokens should define primary color as #1ABC9C', () => {
        const tokensPath = path.join(projectRoot, 'src/styles/tokens.css');
        const tokensContent = fs.readFileSync(tokensPath, 'utf-8');

        // Check that primary color is defined as #1ABC9C in design tokens
        expect(tokensContent).toMatch(/--color-primary:\s*#1ABC9C/);
    });

    test('Destructive action buttons should use semantic-error color (#E74C3C)', () => {
        const globalsCssPath = path.join(projectRoot, 'src/styles/globals.css');
        const cssContent = fs.readFileSync(globalsCssPath, 'utf-8');

        // Check for .btn-danger class definition
        const btnDangerMatch = cssContent.match(/\.btn-danger\s*{([^}]*)}/);
        expect(btnDangerMatch).not.toBeNull();

        if (btnDangerMatch) {
            const btnDangerContent = btnDangerMatch[1];
            // Should use bg-semantic-error (which is #E74C3C in tailwind config)
            expect(btnDangerContent).toMatch(/bg-semantic-error/);
        }
    });

    test('design tokens should define error color as #E74C3C', () => {
        const tokensPath = path.join(projectRoot, 'src/styles/tokens.css');
        const tokensContent = fs.readFileSync(tokensPath, 'utf-8');

        // Check that error color is defined as #E74C3C in design tokens
        expect(tokensContent).toMatch(/--color-error:\s*#E74C3C/);
    });
});
