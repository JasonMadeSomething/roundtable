import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import ConversationList from './pages/ConversationList';
import Conversation from './pages/Conversation';
import PersonaManagement from './pages/PersonaManagement';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Header />
        <div className="container">
          <Routes>
            <Route path="/" element={<ConversationList />} />
            <Route path="/conversations/:conversationId" element={<Conversation />} />
            <Route path="/personas" element={<PersonaManagement />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
