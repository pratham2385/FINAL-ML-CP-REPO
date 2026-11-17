import apiClient from './client';

/**
 * Fetches runtime health of the API, ML models, and PostgreSQL connection.
 */
export async function getHealth() {
  const response = await apiClient.get('/health');
  return response.data;
}
