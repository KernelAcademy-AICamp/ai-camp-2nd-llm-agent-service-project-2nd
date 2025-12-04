import LawyerCaseDetailClient from './LawyerCaseDetailClient';

// Required for static export with dynamic routes
// Pre-render sample case pages; additional routes are handled at request time
export function generateStaticParams() {
  return [
    { id: '1' },
    { id: '2' },
    { id: '3' },
  ];
}

// Allow dynamic routes not listed in generateStaticParams
export const dynamicParams = true;

interface PageProps {
  params: { id: string };
}

export default function LawyerCaseDetailPage({ params }: PageProps) {
  return <LawyerCaseDetailClient id={params.id} />;
}
