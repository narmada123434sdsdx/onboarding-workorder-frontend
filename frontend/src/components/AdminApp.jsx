import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import AdminDashboard from './AdminDashboard';
import './css/AdminApp.css';
import AdminStandardRate from './AdminStandardRate';
import AdminHome from './AdminHome';
import { Menu, X } from 'lucide-react';
import WorkOrderLayout from './workorders/WorkOrderLayout';

function AdminApp({ admin, setAdmin }) {
  const navigate = useNavigate();
  const [activeLink, setActiveLink] = useState('home');
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const storedAdmin = localStorage.getItem('admin');
    if (!storedAdmin) {
      navigate('/admin/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('admin');
    setAdmin(null);
    navigate('/admin/login');
  };

  const handleLinkClick = (link) => {
    setActiveLink(link);
    setMenuOpen(false); // close menu on mobile after navigation
  };

  return (
    <div className="admin-app">
      {/* Top Navbar */}
      <nav className="admin-navbar">
        <div className="nav-left">
          <h3 className="nav-title">Admin Portal</h3>
        </div>

        {/* Mobile toggle button */}
        <button
          className="menu-toggle"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>

        {/* Navigation links */}
        <ul className={`nav-links ${menuOpen ? 'open' : ''}`}>
          <li>
            <Link
              to="/admin/home"
              className={activeLink === 'home' ? 'active' : ''}
              onClick={() => handleLinkClick('home')}
            >
              Home
            </Link>
          </li>
          <li>
            <Link
              to="/admin/workorder"
              className={activeLink === 'workorders' ? 'active' : ''}
              onClick={() => handleLinkClick('workorders')}
            >
              Work Orders
            </Link>
          </li>
          <li>
            <Link
              to="/admin/standard_rate"
              className={activeLink === 'standard_rate' ? 'active' : ''}
              onClick={() => handleLinkClick('standard_rate')}
            >
              Standard Rate
            </Link>
          </li>
          <li>
            <Link
              to="/admin/management"
              className={activeLink === 'management' ? 'active' : ''}
              onClick={() => handleLinkClick('management')}
            >
              Management
            </Link>
          </li>
          <li>
            <button className="logout-btn" onClick={handleLogout}>
              Logout
            </button>
          </li>
        </ul>
      </nav>

      {/* Content Area */}
      <div className="admin-content">
        <Routes>
          <Route path="/home" element={<AdminHome admin={admin} setAdmin={setAdmin} />} />
            {/* WorkOrders Nested Layout */}
          <Route path="/workorder/*" element={<WorkOrderLayout />} />

          <Route path="/standard_rate" element={<AdminStandardRate admin={admin} setAdmin={setAdmin} />} />
          <Route path="/management" element={<AdminDashboard admin={admin} setAdmin={setAdmin} />} />
        </Routes>
      </div>
    </div>
  );
}

export default AdminApp;
