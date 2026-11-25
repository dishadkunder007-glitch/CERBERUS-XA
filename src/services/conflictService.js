import apiClient from './api';

export const getConflictAnalysis = async (params = {}) => {
  const response = await apiClient.get('/conflicts', { params });
  return response.data;
};

export const resolveConflict = async (conflictId, resolutionData) => {
  const response = await apiClient.post(`/conflicts/${conflictId}/resolve`, resolutionData);
  return response.data;
};

export default {
  getConflictAnalysis,
  resolveConflict
};
