import React from 'react';

const Dashboard = ({ handleLogout }) => {
  return (
    <div className="container mt-5">
      <h2>Welcome to the Dashboard</h2>
      <button className="btn btn-danger mt-4" onClick={() => handleLogout(false)}>
        Logout
      </button>
    </div>
  );
};

export default Dashboard;
