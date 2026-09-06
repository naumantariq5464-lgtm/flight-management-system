import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';
import { useNotification } from './NotificationContext';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);
  const { addToast } = useNotification();

  // Load user profile if token exists
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      try {
        const profile = await api.get('/auth/me');
        setUser(profile);
      } catch (err) {
        console.error('Failed to load user profile:', err);
        logout();
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    try {
      const res = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      addToast(`Welcome back, ${res.user.first_name}!`, 'success');
      return res.user;
    } catch (err) {
      addToast(err.message || 'Login failed', 'error');
      throw err;
    }
  };

  const register = async (payload) => {
    try {
      const res = await api.post('/auth/register', payload);
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      addToast('Registration successful! Account activated.', 'success');
      return res.user;
    } catch (err) {
      addToast(err.message || 'Registration failed', 'error');
      throw err;
    }
  };

  const switchDemoAccount = async (roleType) => {
    let creds = { email: 'customer@flightsystem.com', pass: 'Customer@123456' };
    if (roleType === 'SUPER_ADMIN') {
      creds = { email: 'admin@flightsystem.com', pass: 'Admin@123456' };
    } else if (roleType === 'OPERATIONS_AGENT') {
      creds = { email: 'agent@flightsystem.com', pass: 'Agent@123456' };
    }
    return login(creds.email, creds.pass);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    addToast('Logged out successfully', 'info');
  };

  const isSuperAdmin = user?.role?.name === 'SUPER_ADMIN';
  const isAgent = user?.role?.name === 'OPERATIONS_AGENT';
  const isAdminOrAgent = isSuperAdmin || isAgent;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        switchDemoAccount,
        isSuperAdmin,
        isAgent,
        isAdminOrAgent,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
