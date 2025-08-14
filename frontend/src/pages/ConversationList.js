import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getConversations, createConversation } from '../services/api';

function ConversationList() {
  const [conversations, setConversations] = useState([]);
  const [newConversationName, setNewConversationName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await getConversations();
      setConversations(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch conversations. Please try again later.');
      console.error('Error fetching conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConversation = async (e) => {
    e.preventDefault();
    if (!newConversationName.trim()) return;

    try {
      const response = await createConversation({
        name: newConversationName,
      });
      setConversations([...conversations, response.data]);
      setNewConversationName('');
    } catch (err) {
      setError('Failed to create conversation. Please try again.');
      console.error('Error creating conversation:', err);
    }
  };

  if (loading) {
    return <div className="loading">Loading conversations...</div>;
  }

  return (
    <div>
      <h2>Conversations</h2>
      
      <div className="card">
        <form onSubmit={handleCreateConversation}>
          <div className="form-group">
            <input
              type="text"
              className="form-control"
              placeholder="New conversation name"
              value={newConversationName}
              onChange={(e) => setNewConversationName(e.target.value)}
            />
          </div>
          <button type="submit" className="btn">Create Conversation</button>
        </form>
      </div>

      {error && <div className="error">{error}</div>}

      {conversations.length === 0 ? (
        <div className="card">No conversations yet. Create one to get started!</div>
      ) : (
        <div className="conversation-list">
          {conversations.map((conversation) => (
            <div key={conversation.id} className="card conversation-card">
              <h3>{conversation.name}</h3>
              <p>Created: {new Date(conversation.created_at).toLocaleString()}</p>
              <Link to={`/conversations/${conversation.id}`} className="btn">
                View Conversation
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ConversationList;
