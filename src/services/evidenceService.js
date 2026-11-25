import apiClient from './api';

/**
 * Service to handle all multimodal evidence processing and investigation contracts
 * Designed to cleanly interface with FastAPI endpoints developed by Members 2, 3, and 4.
 */

// 1. Health check endpoint (GET /health)
export const checkBackendHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return {
      online: true,
      data: response.data
    };
  } catch (error) {
    return {
      online: false,
      error: error.message || 'FastAPI service offline'
    };
  }
};

// 2. Upload and process single file (POST /process-file)
// Member 2 Integration: Multimodal data processing
export const processFile = async (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/process-file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

// 3. Upload and process batch of multimodal evidence files (POST /process-batch)
// Member 2 Integration: Multimodal batch ingestion
export const processBatch = async (files, onUploadProgress) => {
  const formData = new FormData();
  Array.from(files).forEach((file) => {
    formData.append('files', file);
  });

  const response = await apiClient.post('/process-batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

// ============================================================================
// INTEGRATION CONTRACTS FOR MEMBERS 3 & 4
// If backend has different route names, adjust below without touching UI components
// ============================================================================

// 4. Retrieve Extracted Claims & Provenance (Contract with Member 2 / 3)
export const getExtractedClaims = async (params = {}) => {
  const response = await apiClient.get('/claims', { params });
  return response.data;
};

// 5. Retrieve Conflict Analysis & Contradiction Detection (Contract with Member 3)
export const getConflictAnalysis = async (params = {}) => {
  const response = await apiClient.get('/conflicts', { params });
  return response.data;
};

// 6. Retrieve Multimodal Knowledge Graph data (Contract with Member 3)
export const getKnowledgeGraphData = async (params = {}) => {
  const response = await apiClient.get('/graph', { params });
  return response.data;
};

// 7. Submit Investigation Question and Get AI Reasoning Result (Contract with Member 4)
export const submitInvestigationQuery = async (queryPayload) => {
  // queryPayload: { question: string, caseId?: string, evidenceIds?: string[] }
  const response = await apiClient.post('/investigate', queryPayload);
  return response.data;
};

// 8. Retrieve Full AI Reasoning Report (Contract with Member 4)
export const getInvestigationReport = async (reportId) => {
  const response = await apiClient.get(`/investigation-report/${reportId || 'latest'}`);
  return response.data;
};
