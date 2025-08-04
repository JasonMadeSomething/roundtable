import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Conversations
export const getConversations = () => api.get('/conversations');
export const getConversation = (id) => api.get(`/conversations/${id}`);
export const createConversation = (data) => api.post('/conversations', data);
export const deleteConversation = (id) => api.delete(`/conversations/${id}`);

// Documents
export const getDocuments = (conversationId) => 
  api.get(`/conversations/${conversationId}/documents`);
export const uploadDocument = (conversationId, formData) => 
  api.post(`/conversations/${conversationId}/documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
export const deleteDocument = (id) => api.delete(`/documents/${id}`);

// Turns
export const getTurns = (conversationId) => 
  api.get(`/conversations/${conversationId}/turns`);
export const createTurn = (conversationId, data) => 
  api.post(`/conversations/${conversationId}/turns`, data);

export default api;
