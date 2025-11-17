// src/pages/Contractor.jsx
import React, { useEffect, useState } from "react";
import "./css/workorders.css";
import { apiGet } from "../../api/api";
import { useNavigate } from "react-router-dom";

const Contractor = () => {
  const [workorders, setWorkorders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [status, setStatus] = useState("All");
  const [showTable, setShowTable] = useState(false);

  const navigate = useNavigate();

  const fetchFilteredData = async () => {
    if (!fromDate || !toDate) {
      alert("⚠️ Please select From & To dates");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append("from", fromDate);
      params.append("to", toDate);
      if (status !== "All") params.append("status", status);

      const data = await apiGet(`/api/workorders/filter?${params.toString()}`);

      setWorkorders(data);
      setShowTable(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setFromDate("");
    setToDate("");
    setStatus("All");
    setWorkorders([]);
    setShowTable(false);
  };

  return (
    <div className="dashboard-page">

      {/* ---------- FILTER HEADER ---------- */}
      <div className="dashboard-card">
        <div className="dashboard-header">Work Orders List</div>

        <div className="dashboard-content">
          <div className="dashboard-filters">

            <div>
              <label>From Date:</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>

            <div>
              <label>To Date:</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>

            <div>
              <label>Status:</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="All">All</option>
                <option value="OPEN">OPEN</option>
                <option value="Accepted">Accepted</option>
                <option value="REJECTED">Rejected</option>
                <option value="In Progress">In Progress</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>

            <div className="dashboard-btn-group">
              <button className="btn btn-green" onClick={fetchFilteredData}>
                🔍 Submit
              </button>
              <button className="btn btn-blue" onClick={resetFilters}>
                🔄 Reset
              </button>
            </div>

          </div>
        </div>
      </div>

      {/* ---------- RESULTS TABLE ---------- */}
      {showTable && (
        <div className="results-main clean-results">
          <div className="results-content">

            {loading && <div className="info-message">Loading workorders...</div>}
            {error && <div className="error-message">Error: {error}</div>}

            {!loading && workorders.length === 0 && (
              <div className="info-message">No workorders found</div>
            )}

            {workorders.length > 0 && (
              <div className="table-wrapper">
                <table className="workorders-table">
                  <thead>
                    <tr>
                      <th>Work Order</th>
                      <th>Type</th>
                      <th>Area</th>
                      <th>Status</th>
                      <th>Requested Time Closing</th>
                      <th>Remarks</th>
                      <th>Rate</th>
                      <th>Created At</th>
                    </tr>
                  </thead>

                  <tbody>
                    {workorders.map((wo) => (
                      <tr key={wo.ID}>
                        {/* 👉 CLICKABLE WORK ORDER */}
                        <td
                          className="clickable-wo"
                          onClick={() => navigate(`/workorders/${wo.ID}`)}
                        >
                          {wo.WORKORDER}
                        </td>

                        <td>{wo.WORKORDER_TYPE}</td>
                        <td>{wo.WORKORDER_AREA}</td>

                        <td className={`status ${wo.STATUS.toLowerCase()}`}>
                          {wo.STATUS}
                        </td>

                        <td>
                          {wo.REQUESTED_TIME_CLOSING
                            ? new Date(wo.REQUESTED_TIME_CLOSING).toLocaleString()
                            : "N/A"}
                        </td>

                        <td>{wo.REMARKS || "-"}</td>

                        <td>
                          {wo.RATE?.total_rate ?? "N/A"} (
                          {wo.RATE?.type_rates
                            ? Object.entries(wo.RATE.type_rates)
                                .map(([type, rate]) => `${type}: ${rate}`)
                                .join(", ")
                            : "N/A"}
                          )
                        </td>

                        <td>
                          {wo.CREATED_T
                            ? new Date(wo.CREATED_T).toLocaleString()
                            : "N/A"}
                        </td>
                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
};

export default Contractor;
