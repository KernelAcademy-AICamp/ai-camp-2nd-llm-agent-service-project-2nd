import { Metadata } from 'next';
import RelationshipClient from './RelationshipClient';

export const metadata: Metadata = {
  title: '인물 관계도 | LEH',
  description: '사건 관련 인물들의 관계를 시각화합니다.',
};

// Required for static export with dynamic routes
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

export default function RelationshipPage({ params }: PageProps) {
  return <RelationshipClient caseId={params.id} />;
}
