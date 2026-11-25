import apiClient from './api';

export const getKnowledgeGraphData = async (params = {}) => {
  const response = await apiClient.get('/graph', { params });
  return response.data;
};

export const getEntityNodeDetails = async (nodeId) => {
  const response = await apiClient.get(`/graph/nodes/${nodeId}`);
  return response.data;
};

export default {
  getKnowledgeGraphData,
  getEntityNodeDetails
};
