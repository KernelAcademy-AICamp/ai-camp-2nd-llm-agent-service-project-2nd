/**
 * Evidence Components
 *
 * Components for displaying and managing evidence items including:
 * - Evidence status badges and indicators
 * - Evidence cards for grid/card view
 * - Evidence data table for list view
 * - Evidence type icons
 * - File upload functionality
 */

// Status display
export { EvidenceStatusBadge } from './EvidenceStatusBadge';

// Type icons
export { EvidenceTypeIcon } from './EvidenceTypeIcon';

// Card view components
export { EvidenceCard, EvidenceCardGrid } from './EvidenceCard';

// Table view components
export { EvidenceDataTable } from './EvidenceDataTable';
export { default as EvidenceTable } from './EvidenceTable';
export { DataTablePagination } from './DataTablePagination';

// Upload functionality
export { default as EvidenceUpload } from './EvidenceUpload';
