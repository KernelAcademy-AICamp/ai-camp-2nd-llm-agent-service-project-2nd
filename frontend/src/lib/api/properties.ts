/**
 * Properties API Client
 * Handles property CRUD and division prediction operations
 */

import { apiRequest, ApiResponse } from './client';
import {
  Property,
  PropertyCreate,
  PropertyUpdate,
  PropertyListResponse,
  PropertySummary,
  DivisionPrediction,
} from '@/types/property';

/**
 * Get all properties for a case
 */
export async function getProperties(
  caseId: string
): Promise<ApiResponse<PropertyListResponse>> {
  return apiRequest<PropertyListResponse>(`/cases/${caseId}/properties`, {
    method: 'GET',
  });
}

/**
 * Get a single property by ID
 */
export async function getProperty(
  caseId: string,
  propertyId: string
): Promise<ApiResponse<Property>> {
  return apiRequest<Property>(`/cases/${caseId}/properties/${propertyId}`, {
    method: 'GET',
  });
}

/**
 * Create a new property for a case
 */
export async function createProperty(
  caseId: string,
  data: PropertyCreate
): Promise<ApiResponse<Property>> {
  return apiRequest<Property>(`/cases/${caseId}/properties`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Update an existing property
 */
export async function updateProperty(
  caseId: string,
  propertyId: string,
  data: PropertyUpdate
): Promise<ApiResponse<Property>> {
  return apiRequest<Property>(`/cases/${caseId}/properties/${propertyId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a property
 */
export async function deleteProperty(
  caseId: string,
  propertyId: string
): Promise<ApiResponse<void>> {
  return apiRequest<void>(`/cases/${caseId}/properties/${propertyId}`, {
    method: 'DELETE',
  });
}

/**
 * Get property summary for a case
 */
export async function getPropertySummary(
  caseId: string
): Promise<ApiResponse<PropertySummary>> {
  return apiRequest<PropertySummary>(`/cases/${caseId}/properties/summary`, {
    method: 'GET',
  });
}

/**
 * Get the latest division prediction for a case
 */
export async function getDivisionPrediction(
  caseId: string
): Promise<ApiResponse<DivisionPrediction | null>> {
  return apiRequest<DivisionPrediction | null>(
    `/cases/${caseId}/division-prediction`,
    {
      method: 'GET',
    }
  );
}

/**
 * Calculate a new division prediction for a case
 */
export async function calculateDivisionPrediction(
  caseId: string,
  forceRecalculate: boolean = false
): Promise<ApiResponse<DivisionPrediction>> {
  return apiRequest<DivisionPrediction>(`/cases/${caseId}/division-prediction`, {
    method: 'POST',
    body: JSON.stringify({ force_recalculate: forceRecalculate }),
  });
}
