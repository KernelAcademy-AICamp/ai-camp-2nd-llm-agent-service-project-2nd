# LEH Frontend

Next.js 14 frontend for Legal Evidence Hub.

## Requirements

- Node.js 18+
- npm or yarn

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Development Commands

```bash
# Development
npm run dev              # Start dev server

# Build & Production
npm run build            # Production build
npm start                # Start production server

# Testing
npm test                 # Run Jest tests
npm run test:watch       # Watch mode

# Linting & Type Check
npm run lint             # ESLint
npm run typecheck        # TypeScript check
```

## Project Structure

```
frontend/
├── src/
│   ├── app/             # Next.js App Router pages
│   │   ├── lawyer/      # Lawyer portal pages
│   │   ├── client/      # Client portal pages
│   │   ├── staff/       # Staff portal pages
│   │   └── settings/    # Settings pages
│   ├── components/      # React components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utilities and API clients
│   ├── contexts/        # React contexts (Auth, Theme)
│   └── types/           # TypeScript type definitions
├── public/              # Static assets
└── e2e/                 # Playwright E2E tests
```

## Environment Variables

Uses unified `.env` file from project root (symlinked to `frontend/.env`).

Client-side variables must start with `NEXT_PUBLIC_`:
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_APP_ENV` - Environment (local/dev/production)

See `../.env.example` for full list.

## E2E Testing

```bash
# Install Playwright browsers
npx playwright install --with-deps chromium

# Run E2E tests
npx playwright test

# Run with UI
npx playwright test --ui
```
