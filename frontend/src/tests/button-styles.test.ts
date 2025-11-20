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

    test('tailwind.config.js should define accent color as #1ABC9C', () => {
        const tailwindConfigPath = path.join(projectRoot, 'tailwind.config.js');
        const configContent = fs.readFileSync(tailwindConfigPath, 'utf-8');

        // Check that accent color is defined as #1ABC9C
        expect(configContent).toMatch(/accent:\s*{[^}]*DEFAULT:\s*["']#1ABC9C["']/);
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

    test('tailwind.config.js should define semantic-error color as #E74C3C', () => {
        const tailwindConfigPath = path.join(projectRoot, 'tailwind.config.js');
        const configContent = fs.readFileSync(tailwindConfigPath, 'utf-8');

        // Check that semantic-error color is defined as #E74C3C
        expect(configContent).toMatch(/["']semantic-error["']:\s*["']#E74C3C["']/);
    });
});
