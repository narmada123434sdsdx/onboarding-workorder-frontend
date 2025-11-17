// src/pages/CompanyDashboardHome.jsx
import React from "react";
import { useOutletContext, Link } from "react-router-dom";
import {
  FaUsers,
  FaHandshake,
  FaClipboardList,
  FaDollarSign,
  FaChartLine,
  FaArrowUp,
  FaCheckCircle,
  FaClock,
  FaStar,
  FaBuilding,
} from "react-icons/fa";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import "./css/CompanyDashboardHome.css";

function CompanyDashboardHome() {
  const { contractor } = useOutletContext();
  const companyName = contractor?.company_name || "Your Company";

  // Mock dashboard data (replace with real API data later)
  const stats = {
    partners: 12,
    activeProjects: 28,
    completedProjects: 156,
    monthlyRevenue: 84500,
    revenueGrowth: 9.2,
    satisfactionRate: 4.8,
    avgResponse: "1.9 hrs",
  };

  const revenueData = [
    { month: "Jun", revenue: 76800 },
    { month: "Jul", revenue: 78500 },
    { month: "Aug", revenue: 80200 },
    { month: "Sep", revenue: 81500 },
    { month: "Oct", revenue: 83200 },
    { month: "Nov", revenue: 84500 },
  ];

  return (
    <div className="company-dashboard-home">
      {/* WELCOME HEADER */}
      <div className="welcome-section d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="fw-bold text-dark">Welcome, {companyName} 👋</h2>
          <p className="text-muted mb-0">
            Here’s a quick overview of your B2B performance and business metrics.
          </p>
        </div>
        {/* <Link to="/contractor/dashboard/projects" className="btn btn-primary">
          <FaClipboardList className="me-2" /> Manage Projects
        </Link> */}
      </div>

      {/* METRICS GRID */}
      <div className="metrics-grid mb-4">
        <div className="metric-card revenue-card">
          <div className="metric-icon bg-primary text-white">
            <FaDollarSign />
          </div>
          <div className="metric-details">
            <h5>Monthly Revenue</h5>
            <h3>${stats.monthlyRevenue.toLocaleString()}</h3>
            <p className="text-success mb-0">
              <FaArrowUp className="me-1" />
              {stats.revenueGrowth}% growth
            </p>
          </div>
        </div>

        <div className="metric-card projects-card">
          <div className="metric-icon bg-info text-white">
            <FaClipboardList />
          </div>
          <div className="metric-details">
            <h5>Active Projects</h5>
            <h3>{stats.activeProjects}</h3>
            <p className="text-muted mb-0">Currently in progress</p>
          </div>
        </div>

        <div className="metric-card partners-card">
          <div className="metric-icon bg-success text-white">
            <FaHandshake />
          </div>
          <div className="metric-details">
            <h5>Active Partners</h5>
            <h3>{stats.partners}</h3>
            <p className="text-muted mb-0">B2B Collaborations</p>
          </div>
        </div>

        <div className="metric-card completed-card">
          <div className="metric-icon bg-warning text-white">
            <FaCheckCircle />
          </div>
          <div className="metric-details">
            <h5>Completed Projects</h5>
            <h3>{stats.completedProjects}</h3>
            <p className="text-muted mb-0">Successfully delivered</p>
          </div>
        </div>
      </div>

      {/* CHARTS & PERFORMANCE SECTION */}
      <div className="row g-4 mb-4">
        {/* Revenue Chart */}
        <div className="col-lg-8">
          <div className="dashboard-card">
            <div className="card-header-custom d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-0">Revenue Overview</h5>
                <small className="text-muted">Performance over last 6 months</small>
              </div>
              <FaChartLine className="text-primary" />
            </div>
            <div className="card-body-custom">
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
                  <XAxis dataKey="month" stroke="#6c757d" />
                  <YAxis stroke="#6c757d" />
                  <Tooltip
                    contentStyle={{
                      background: "#fff",
                      border: "1px solid #e9ecef",
                      borderRadius: "8px",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    stroke="#0d6efd"
                    strokeWidth={3}
                    dot={{ fill: "#0d6efd", r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="col-lg-4">
          <div className="dashboard-card text-center p-4">
            <div className="performance-score-circle mx-auto mb-3">
              <h2>{stats.satisfactionRate}</h2>
              <small>/5.0</small>
            </div>
            <h5 className="fw-bold text-dark">Client Satisfaction</h5>
            <p className="text-muted mb-3">Based on partner feedback</p>
            <div className="performance-mini-stats">
              <p>
                <FaClock className="text-primary me-2" />
                Avg Response: {stats.avgResponse}
              </p>
              <p>
                <FaStar className="text-warning me-2" />
                Consistent Excellence
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* BUSINESS SUMMARY */}
      <div className="dashboard-card p-4">
        <div className="d-flex align-items-center mb-3">
          <FaBuilding className="text-primary me-2" />
          <h5 className="mb-0">Business Summary</h5>
        </div>
        <p className="text-muted">
          {companyName} is collaborating with {stats.partners} active partners across{" "}
          {stats.activeProjects} ongoing projects, achieving a {stats.satisfactionRate}/5
          satisfaction rating and maintaining monthly revenue of $
          {stats.monthlyRevenue.toLocaleString()}.
        </p>
      </div>
    </div>
  );
}

export default CompanyDashboardHome;