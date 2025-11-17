import React, { useState } from "react";
import "./css/workorders.css";
import { apiGet } from "../../api/api";


const WorkOrders = () => {
  const [workorders, setWorkorders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [showResults, setShowResults] = useState(false);

  const [showModal, setShowModal] = useState(false);
  const [modalMessage, setModalMessage] = useState("");

  const fetchFilteredWorkOrders = async () => {
    if (!fromDate || !toDate) {
      setModalMessage("⚠️ Please select both From Date and To Date.");
      setShowModal(true);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      params.append("from", fromDate);
      params.append("to", toDate);
      if (statusFilter !== "All") params.append("status", statusFilter);

const data = await apiGet(`/api/workorders/filter?${params.toString()}`);


      if (data.length === 0) {
        setModalMessage("📭 No workorders found for the selected filters.");
        setShowModal(true);
        setShowResults(false);
        setWorkorders([]);
      } else {
        setWorkorders(data);
        setShowResults(true);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resetFilters = () => {
    setFromDate("");
    setToDate("");
    setStatusFilter("All");
    setWorkorders([]);
    setShowResults(false);
  };

  return (
    <div className="dashboard-page">
      {/* Top Filter Section */}
      <div className="dashboard-card">
        <div className="dashboard-header">Work Orders Dashboard</div>

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
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="All">All</option>
                <option value="OPEN">OPEN</option>
                <option value="ACCEPTED">ACCEPTED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="In Progress">In Progress</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>
            <div className="dashboard-btn-group">
              <button className="btn btn-green" onClick={fetchFilteredWorkOrders}>
                🔍 Submit
              </button>
              <button className="btn btn-blue" onClick={resetFilters}>
                🔄 Reset
              </button>
            </div>
          </div>

          {loading && <div className="info-message">Loading workorders...</div>}
          {error && <div className="error-message">Error: {error}</div>}

          {showModal && (
            <div className="modal-overlay">
              <div className="modal-content">
                <p>{modalMessage}</p>
                <button className="modal-btn" onClick={() => setShowModal(false)}>
                  OK
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results Section - clean, no blue outer border */}
      {showResults && (
        <div className="results-main clean-results">
          <div className="results-content">
            {workorders.length > 0 ? (
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
                     <tr key={wo.ID} className={`status-${wo.STATUS.toLowerCase().replace(/\s+/g, "-")}`}>

                        <td>{wo.WORKORDER}</td>
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
                        <td>{wo.REMARKS}</td>
                        <td>
                          {wo.RATE?.total_rate} (
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
            ) : (
              <div className="info-message">No work orders to display.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkOrders;