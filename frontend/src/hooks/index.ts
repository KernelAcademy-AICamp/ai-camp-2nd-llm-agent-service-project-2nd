/**
 * Custom Hooks
 *
 * Reusable React hooks for common functionality
 */

// Authentication
export { useAuth } from './useAuth';

// Role-based access
export { useRole } from './useRole';

// Data fetching
export { useCaseList } from './useCaseList';
export { useLawyerDashboard } from './useLawyerDashboard';

// Evidence management
export { useEvidenceTable } from './useEvidenceTable';
export {
  useEvidencePolling,
  useSingleEvidencePolling,
} from './useEvidencePolling';
