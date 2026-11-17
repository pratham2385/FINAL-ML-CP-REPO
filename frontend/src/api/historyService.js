import apiClient from './client';

/**
 * Fetches paginated history records with optional analysis_type filtering.
 * @param {{ limit?: number, offset?: number, analysis_type?: string }} params
 */
export async function getHistory(params = {}) {
  const response = await apiClient.get('/history', { params });
  return response.data;
}

/**
 * Fetches aggregated security statistics for the dashboard.
 */
export async function getHistoryStats() {
  const response = await apiClient.get('/history/stats');
  return response.data;
}

/**
 * Fetches complete analysis record by ID.
 * @param {number|string} id
 */
export async function getHistoryById(id) {
  const response = await apiClient.get(`/history/${id}`);
  return response.data;
}

/**
 * Deletes an analysis history record by ID.
 * @param {number|string} id
 */
export async function deleteHistoryById(id) {
  const response = await apiClient.delete(`/history/${id}`);
  return response.data;
}
