import React from 'react';
import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="header">
      <h1>Roundtable</h1>
      <nav className="header-nav">
        <Link to="/">Home</Link>
      </nav>
    </header>
  );
}

export default Header;
