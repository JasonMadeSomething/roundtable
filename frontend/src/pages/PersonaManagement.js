import React, { useState, useEffect } from 'react';
import { getModelConfigs, createModelConfig, updateModelConfig, deleteModelConfig } from '../services/api';

function PersonaManagement() {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingPersona, setEditingPersona] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    provider: 'openai',
    model_id: 'gpt-4',
    persona_name: '',
    persona_description: '',
    persona_instructions: '',
    temperature: 0.7,
    max_tokens: 500,
    top_p: 1.0,
    provider_parameters: {},
    is_active: true
  });

  useEffect(() => {
    fetchPersonas();
  }, []);

  const fetchPersonas = async () => {
    try {
      setLoading(true);
      const response = await getModelConfigs();
      setPersonas(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch personas.');
      console.error('Error fetching personas:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setFormData({ ...formData, [name]: checked });
    } else if (name === 'provider_parameters') {
      try {
        const parsedValue = JSON.parse(value);
        setFormData({ ...formData, [name]: parsedValue });
      } catch (err) {
        // If not valid JSON, store as string to be validated before submission
        setFormData({ ...formData, [name]: value });
      }
    } else if (name === 'temperature' || name === 'top_p' || name === 'max_tokens') {
      setFormData({ ...formData, [name]: parseFloat(value) });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form data
    if (!formData.name || !formData.persona_name || !formData.provider || !formData.model_id) {
      setError('Please fill out all required fields.');
      return;
    }

    // Ensure provider_parameters is an object
    let finalFormData = { ...formData };
    if (typeof finalFormData.provider_parameters === 'string') {
      try {
        finalFormData.provider_parameters = JSON.parse(finalFormData.provider_parameters);
      } catch (err) {
        setError('Provider parameters must be valid JSON.');
        return;
      }
    }

    try {
      if (editingPersona) {
        await updateModelConfig(editingPersona.id, finalFormData);
      } else {
        await createModelConfig(finalFormData);
      }
      
      // Reset form and refresh personas
      setFormData({
        name: '',
        provider: 'openai',
        model_id: 'gpt-4',
        persona_name: '',
        persona_description: '',
        persona_instructions: '',
        temperature: 0.7,
        max_tokens: 500,
        top_p: 1.0,
        provider_parameters: {},
        is_active: true
      });
      setEditingPersona(null);
      setShowForm(false);
      await fetchPersonas();
      setError(null);
    } catch (err) {
      setError('Failed to save persona. Please try again.');
      console.error('Error saving persona:', err);
    }
  };

  const handleEdit = (persona) => {
    // Convert provider_parameters from string to object if needed
    let providerParams = persona.provider_parameters;
    if (typeof providerParams === 'string') {
      try {
        providerParams = JSON.parse(providerParams);
      } catch (err) {
        providerParams = {};
      }
    }

    setFormData({
      name: persona.name,
      provider: persona.provider,
      model_id: persona.model_id,
      persona_name: persona.persona_name,
      persona_description: persona.persona_description,
      persona_instructions: persona.persona_instructions,
      temperature: persona.temperature,
      max_tokens: persona.max_tokens,
      top_p: persona.top_p,
      provider_parameters: providerParams,
      is_active: persona.is_active
    });
    setEditingPersona(persona);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this persona?')) {
      return;
    }

    try {
      await deleteModelConfig(id);
      await fetchPersonas();
      setError(null);
    } catch (err) {
      setError('Failed to delete persona.');
      console.error('Error deleting persona:', err);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: '',
      provider: 'openai',
      model_id: 'gpt-4',
      persona_name: '',
      persona_description: '',
      persona_instructions: '',
      temperature: 0.7,
      max_tokens: 500,
      top_p: 1.0,
      provider_parameters: {},
      is_active: true
    });
    setEditingPersona(null);
    setShowForm(false);
  };

  if (loading && personas.length === 0) {
    return <div className="loading">Loading personas...</div>;
  }

  return (
    <div className="persona-management">
      <h2>Persona Management</h2>
      
      {error && <div className="error">{error}</div>}
      
      <div className="persona-actions">
        <button 
          className="btn primary" 
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Cancel' : 'Create New Persona'}
        </button>
      </div>

      {showForm && (
        <div className="card">
          <h3>{editingPersona ? 'Edit Persona' : 'Create New Persona'}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Configuration Name:</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Provider:</label>
              <select
                name="provider"
                value={formData.provider}
                onChange={handleInputChange}
                required
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="deepseek">DeepSeek</option>
              </select>
            </div>

            <div className="form-group">
              <label>Model ID:</label>
              <input
                type="text"
                name="model_id"
                value={formData.model_id}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Persona Name:</label>
              <input
                type="text"
                name="persona_name"
                value={formData.persona_name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Persona Description:</label>
              <textarea
                name="persona_description"
                value={formData.persona_description}
                onChange={handleInputChange}
                rows="3"
              ></textarea>
            </div>

            <div className="form-group">
              <label>Persona Instructions:</label>
              <textarea
                name="persona_instructions"
                value={formData.persona_instructions}
                onChange={handleInputChange}
                rows="5"
              ></textarea>
            </div>

            <div className="form-group">
              <label>Temperature:</label>
              <input
                type="number"
                name="temperature"
                value={formData.temperature}
                onChange={handleInputChange}
                step="0.1"
                min="0"
                max="2"
              />
            </div>

            <div className="form-group">
              <label>Max Tokens:</label>
              <input
                type="number"
                name="max_tokens"
                value={formData.max_tokens}
                onChange={handleInputChange}
                step="1"
                min="1"
              />
            </div>

            <div className="form-group">
              <label>Top P:</label>
              <input
                type="number"
                name="top_p"
                value={formData.top_p}
                onChange={handleInputChange}
                step="0.1"
                min="0"
                max="1"
              />
            </div>

            <div className="form-group">
              <label>Provider Parameters (JSON):</label>
              <textarea
                name="provider_parameters"
                value={typeof formData.provider_parameters === 'object' 
                  ? JSON.stringify(formData.provider_parameters, null, 2) 
                  : formData.provider_parameters}
                onChange={handleInputChange}
                rows="5"
                placeholder="{}"
              ></textarea>
            </div>

            <div className="form-group checkbox">
              <label>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                />
                Active
              </label>
            </div>

            <div className="form-actions">
              <button type="button" className="btn secondary" onClick={handleCancel}>
                Cancel
              </button>
              <button type="submit" className="btn primary">
                {editingPersona ? 'Update Persona' : 'Create Persona'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="personas-list">
        <h3>Available Personas</h3>
        {personas.length === 0 ? (
          <p>No personas available. Create one to get started.</p>
        ) : (
          personas.map((persona) => (
            <div key={persona.id} className={`persona-card ${!persona.is_active ? 'inactive' : ''}`}>
              <div className="persona-header">
                <h4>{persona.persona_name}</h4>
                <span className={`status ${persona.is_active ? 'active' : 'inactive'}`}>
                  {persona.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="persona-body">
                <p><strong>Provider:</strong> {persona.provider}</p>
                <p><strong>Model:</strong> {persona.model_id}</p>
                <p><strong>Description:</strong> {persona.persona_description}</p>
              </div>
              <div className="persona-actions">
                <button className="btn small" onClick={() => handleEdit(persona)}>
                  Edit
                </button>
                <button className="btn small danger" onClick={() => handleDelete(persona.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default PersonaManagement;
