import React, { useState, useEffect } from 'react';
import Login from './Login';
import Dashboard from './Dashboard';
import { supabase } from './supabaseClient';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const session = supabase.auth.getSession();
    session.then(({ data: { session } }) => {
      if (session) {
        setIsLoggedIn(true);
      }
    });
  }, []);

  const handleLogin = (status) => {
    setIsLoggedIn(status);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setIsLoggedIn(false);
  };

  return (
    <div>
      {isLoggedIn ? (
        <Dashboard handleLogout={handleLogout} />
      ) : (
        <Login handleLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
