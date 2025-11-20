import * as fs from 'fs';
import * as path from 'path';

describe('Frontend Style Rules', () => {
    const projectRoot = path.resolve(__dirname, '../../');

    test('globals.css should define body font-size as 16px and use Pretendard', () => {
        const globalsCssPath = path.join(projectRoot, 'src/styles/globals.css');
        const cssContent = fs.readFileSync(globalsCssPath, 'utf-8');

        // Check for font import or definition
        expect(cssContent).toMatch(/Pretendard/);

        // Check for body font size 16px
        // We look for "font-size: 16px;" inside body block or generally in the file if specific parsing is hard
        // A simple regex for body block would be better
        const bodyBlockMatch = cssContent.match(/body\s*{([^}]*)}/);
        expect(bodyBlockMatch).not.toBeNull();

        if (bodyBlockMatch) {
            const bodyContent = bodyBlockMatch[1];
            expect(bodyContent).toMatch(/font-size:\s*16px/);
            expect(bodyContent).toMatch(/font-family:\s*var\(--font-pretendard\)/);
        }
    });

    test('tailwind.config.js should extend fontFamily with Pretendard', () => {
        const tailwindConfigPath = path.join(projectRoot, 'tailwind.config.js');
        const configContent = fs.readFileSync(tailwindConfigPath, 'utf-8');

        expect(configContent).toMatch(/fontFamily:\s*{[^}]*sans:\s*\["var\(--font-pretendard\)"/);
    });
});
