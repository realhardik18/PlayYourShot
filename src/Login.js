import React, { useState } from 'react';
import { supabase } from './supabaseClient';

const Login = ({ handleLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isSignUp, setIsSignUp] = useState(false); // Toggle between login and sign-up
  const [error, setError] = useState('');

  const handleSignUp = async (e) => {
    e.preventDefault();
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username: username,
          phone_number: phoneNumber
        }
      }
    });
    if (error) {
      setError(error.message);
    } else {
      handleLogin(true);
    }
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) {
      setError(error.message);
    } else {
      handleLogin(true);
    }
  };

  return (
    <div className="container mt-5">
      <h2 className="text-center">{isSignUp ? 'Sign Up' : 'Login'}</h2>
      <form onSubmit={isSignUp ? handleSignUp : handleSignIn} className="mt-4">
        <div className="form-group">
          <label>Email</label>
          <input
            type="email"
            className="form-control"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group mt-3">
          <label>Password</label>
          <input
            type="password"
            className="form-control"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {isSignUp && (
          <>
            <div className="form-group mt-3">
              <label>Username</label>
              <input
                type="text"
                className="form-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="form-group mt-3">
              <label>Phone Number</label>
              <input
                type="tel"
                className="form-control"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
              />
            </div>
          </>
        )}
        {error && <div className="text-danger mt-3">{error}</div>}
        <button type="submit" className="btn btn-primary mt-4 w-100">
          {isSignUp ? 'Sign Up' : 'Login'}
        </button>
      </form>
      <div className="mt-4 text-center">
        <button
          className="btn btn-secondary"
          onClick={() => setIsSignUp(!isSignUp)}
        >
          {isSignUp ? 'Already have an account? Login' : 'Need an account? Sign Up'}
        </button>
      </div>
    </div>
  );
};

export default Login;
