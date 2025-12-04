/**
 * Relationship Visualization Page
 * Displays person relationship graph for a case
 */

import { Metadata } from 'next';
import RelationshipClient from './RelationshipClient';

export const metadata: Metadata = {
  title: '인물 관계도 - Legal Evidence Hub',
  description: '사건 관련 인물들의 관계를 시각적으로 표시합니다',
};

interface RelationshipPageProps {
  params: {
    id: string;
  };
}

export default function RelationshipPage({ params }: RelationshipPageProps) {
  return <RelationshipClient caseId={params.id} />;
}
