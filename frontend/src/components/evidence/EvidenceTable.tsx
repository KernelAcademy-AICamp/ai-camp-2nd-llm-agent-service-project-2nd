/**
 * Evidence Table Component (Refactored)
 *
 * This component now serves as a thin wrapper around EvidenceDataTable,
 * following Clean Code principles:
 * - Separation of concerns (logic in hooks, presentation in components)
 * - Single Responsibility Principle (each component has one job)
 * - Composition over inheritance (built from smaller components)
 *
 * Architecture:
 * - EvidenceTable (this file): Main export, backward compatibility
 * - EvidenceDataTable: Core table with TanStack Table integration
 * - useEvidenceTable: Business logic (sorting, filtering, pagination)
 * - Sub-components: EvidenceTypeIcon, EvidenceStatusBadge, DataTablePagination
 */

import { Evidence } from '@/types/evidence';
import { EvidenceDataTable } from './EvidenceDataTable';

interface EvidenceTableProps {
  items: Evidence[];
}

/**
 * Main Evidence Table Component
 * Maintains backward compatibility while delegating to new DataTable architecture
 */
export default function EvidenceTable({ items }: EvidenceTableProps) {
  return <EvidenceDataTable items={items} />;
}
