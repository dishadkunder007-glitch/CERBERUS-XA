import apiClient from './api';

export const submitInvestigationQuery = async (queryPayload) => {
  const response = await apiClient.post('/investigate', queryPayload);
  return response.data;
};

export const getInvestigationReport = async (reportId = 'latest') => {
  const response = await apiClient.get(`/investigation-report/${reportId}`);
  return response.data;
};

export const getEntityResolutions = async (params = {}) => {
  const response = await apiClient.get('/entity-resolution', { params });
  return response.data;
};

export const getReliabilityAnalysis = async (params = {}) => {
  const response = await apiClient.get('/reliability', { params });
  return response.data;
};

export const getAdversarialAnalysis = async (params = {}) => {
  const response = await apiClient.get('/adversarial', { params });
  return response.data;
};

export const getAuditLogs = async (params = {}) => {
  const response = await apiClient.get('/audit', { params });
  return response.data;
};

export default {
  submitInvestigationQuery,
  getInvestigationReport,
  getEntityResolutions,
  getReliabilityAnalysis,
  getAdversarialAnalysis,
  getAuditLogs
};
