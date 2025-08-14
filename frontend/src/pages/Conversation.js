import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  getConversation,
  getTurns,
  createTurn,
  getModelConfigs,
  uploadDocument,
} from '../services/api';

function Conversation() {
  const { conversationId } = useParams();
  const [conversation, setConversation] = useState(null);
  const [turns, setTurns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [query, setQuery] = useState('');
  const [personas, setPersonas] = useState([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState('');
  const [loadingPersonas, setLoadingPersonas] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchConversation();
    fetchTurns();
    fetchPersonas();
  }, [conversationId]);

  const fetchConversation = async () => {
    try {
      const response = await getConversation(conversationId);
      setConversation(response.data);
    } catch (err) {
      setError('Failed to fetch conversation details.');
      console.error('Error fetching conversation:', err);
    }
  };

  const fetchTurns = async () => {
    try {
      setLoading(true);
      const response = await getTurns(conversationId);
      setTurns(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch conversation turns.');
      console.error('Error fetching turns:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchPersonas = async () => {
    try {
      setLoadingPersonas(true);
      const response = await getModelConfigs(true); // Get only active personas
      setPersonas(response.data);
      
      // Set default selected persona if available
      if (response.data.length > 0) {
        setSelectedPersonaId(response.data[0].id);
      }
    } catch (err) {
      console.error('Error fetching personas:', err);
    } finally {
      setLoadingPersonas(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      await uploadDocument(conversationId, formData);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setError(null);
    } catch (err) {
      setError('Failed to upload document. Please try again.');
      console.error('Error uploading document:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateTurn = async () => {
    try {
      setGenerating(true);
      await createTurn(conversationId, {
        query: query,
        model_config_id: selectedPersonaId || undefined
      });
      setQuery('');
      await fetchTurns();
    } catch (err) {
      setError('Failed to generate turn. Please try again.');
      console.error('Error generating turn:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleStartConversation = async () => {
    if (!query.trim()) {
      setError('Please enter a query to start the conversation.');
      return;
    }
    await handleGenerateTurn();
  };

  const handleContinueConversation = async () => {
    await handleGenerateTurn();
  };

  if (loading && !conversation) {
    return <div className="loading">Loading conversation...</div>;
  }

  return (
    <div>
      {conversation && <h2>{conversation.name}</h2>}

      <div className="card">
        <h3>Upload Document</h3>
        <div className="file-upload">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            disabled={uploading}
            accept=".txt,.pdf,.doc,.docx"
          />
          <p>Drag and drop a file or click to select</p>
          {uploading && <p>Uploading...</p>}
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {turns.length === 0 ? (
        <div className="card">
          <h3>Start Conversation</h3>
          <div className="form-group">
            <textarea
              className="form-control"
              rows="3"
              placeholder="Enter your query to start the conversation..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            ></textarea>
          </div>
          
          <div className="form-group">
            <label>Select Persona:</label>
            <select
              value={selectedPersonaId}
              onChange={(e) => setSelectedPersonaId(e.target.value)}
              disabled={loadingPersonas}
            >
              {personas.length === 0 && <option value="">No personas available</option>}
              {personas.map(persona => (
                <option key={persona.id} value={persona.id}>
                  {persona.persona_name} ({persona.provider}/{persona.model_id})
                </option>
              ))}
            </select>
            {loadingPersonas && <span className="loading-text">Loading personas...</span>}
          </div>
          <button
            className="btn"
            onClick={handleStartConversation}
            disabled={generating || !query.trim()}
          >
            {generating ? 'Generating...' : 'Start'}
          </button>
        </div>
      ) : (
        <>
          <div className="turns-container">
            {turns.map((turn) => (
              <div key={turn.id} className="turn">
                <div className="turn-header">
                  <span>Turn {turn.turn_number}</span>
                  <span>
                    {turn.model_config_id ? 
                      personas.find(p => p.id === turn.model_config_id)?.persona_name || turn.model_name : 
                      turn.model_name}
                  </span>
                  <span>{new Date(turn.created_at).toLocaleString()}</span>
                </div>
                <div className="turn-content">
                  <p>{turn.response}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="form-group">
              <label>Select Persona:</label>
              <select
                value={selectedPersonaId}
                onChange={(e) => setSelectedPersonaId(e.target.value)}
                disabled={loadingPersonas || generating}
              >
                {personas.length === 0 && <option value="">No personas available</option>}
                {personas.map(persona => (
                  <option key={persona.id} value={persona.id}>
                    {persona.persona_name} ({persona.provider}/{persona.model_id})
                  </option>
                ))}
              </select>
              {loadingPersonas && <span className="loading-text">Loading personas...</span>}
            </div>
            <button
              className="btn"
              onClick={handleContinueConversation}
              disabled={generating}
            >
              {generating ? 'Generating...' : 'Continue Conversation'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default Conversation;
