// src/pages/WorkOrderAreaPage.jsx
import React, { useState, useEffect } from "react";
import "./css/setuppage.css";
import { apiGet, apiPost, apiPut, apiDelete } from "../../api/api";

const WorkOrderAreaPage = () => {
  const [formData, setFormData] = useState({
    WORKORDER_AREA: "",
    STATUS: "Active",
  });

  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingData, setEditingData] = useState({ WORKORDER_AREA: "", STATUS: "" });

  // Allow letters, numbers, hyphen (no spaces)
  const cleanInput = (value) => value.replace(/[^A-Za-z0-9-]/g, "");

  const fetchAreas = async () => {
    try {
      setLoading(true);
      const data = await apiGet("/api/workorder-areas");
      setAreas(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error fetching areas:", err);
      alert("Failed to load areas. See console for details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreas();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const cleaned = name === "WORKORDER_AREA" ? cleanInput(value) : value;
    setFormData((p) => ({ ...p, [name]: cleaned }));
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    const cleaned = name === "WORKORDER_AREA" ? cleanInput(value) : value;
    setEditingData((p) => ({ ...p, [name]: cleaned }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.WORKORDER_AREA) return alert("Please enter Work Order Area.");
    try {
      await apiPost("/api/workorder-area", formData);
      setFormData({ WORKORDER_AREA: "", STATUS: "Active" });
      await fetchAreas();
      alert("✅ Work Order Area added successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to add area: " + err.message);
    }
  };

  const handleEdit = (area) => {
    setEditingId(area.id);
    setEditingData({ WORKORDER_AREA: area.workorder_area, STATUS: area.status });
  };

  const handleCancel = () => { setEditingId(null); setEditingData({ WORKORDER_AREA: "", STATUS: "" }); };

  const handleUpdate = async (id) => {
    if (!editingData.WORKORDER_AREA) return alert("Please enter Work Order Area.");
    try {
      await apiPut(`/api/workorder-area/${id}`, editingData);
      setEditingId(null);
      await fetchAreas();
      alert("✅ Work Order Area updated!");
    } catch (err) {
      console.error(err);
      alert("Failed to update: " + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this record?")) return;
    try {
      await apiDelete(`/api/workorder-area/${id}`);
      await fetchAreas();
      alert("✅ Work Order Area deleted!");
    } catch (err) {
      console.error(err);
      alert("Failed to delete: " + err.message);
    }
  };

  return (
    <div className="setup-page">
      <div className="page-container">
        <div className="box-section form-box">
          <h2>Add New Work Order Area</h2>
          <form onSubmit={handleSubmit} className="form-create">
            <div className="form-header-row">
              <div className="form-header-cell">WORK ORDER AREA</div>
              <div className="form-header-cell">STATUS</div>
            </div>

            <div className="form-group">
              <div className="input-with-star">
                <input
                  type="text"
                  name="WORKORDER_AREA"
                  value={formData.WORKORDER_AREA}
                  onChange={handleChange}
                  placeholder="Enter Work Order Area (no spaces)"
                  required
                />
                <span className="required-star">★</span>
              </div>
            </div>

            <div className="form-group">
              <div className="input-with-star">
                <select name="STATUS" value={formData.STATUS} onChange={handleChange} required>
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
                <span className="required-star">★</span>
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary">Submit</button>
              <button type="button" className="btn-reset" onClick={() => setFormData({ WORKORDER_AREA: "", STATUS: "Active" })}>Reset</button>
            </div>
          </form>
        </div>

        <div className="box-section table-box">
          <h2>Existing Work Order Areas</h2>
          {loading ? <p>Loading...</p> : (
            <div className="table-wrapper">
              <div className="fixed-table">
                <table className="workorder-table">
                  <thead>
                    <tr><th>Work Order Area</th><th>Status</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {areas.length ? areas.map(area => (
                      <tr key={area.id}>
                        {editingId === area.id ? (
                          <>
                            <td>
                              <input type="text" name="WORKORDER_AREA" value={editingData.WORKORDER_AREA} onChange={handleEditChange} />
                            </td>
                            <td>
                              <select name="STATUS" value={editingData.STATUS} onChange={handleEditChange}>
                                <option value="Active">Active</option>
                                <option value="Inactive">Inactive</option>
                              </select>
                            </td>
                            <td>
                              <button className="btn-save" onClick={() => handleUpdate(area.id)}>Save</button>
                              <button className="btn-cancel" onClick={handleCancel}>Cancel</button>
                            </td>
                          </>
                        ) : (
                          <>
                            <td>{area.workorder_area}</td>
                            <td>{area.status}</td>
                            <td>
                              <button className="btn-edit" onClick={() => handleEdit(area)}>Edit</button>
                              <button className="btn-delete" onClick={() => handleDelete(area.id)}>Delete</button>
                            </td>
                          </>
                        )}
                      </tr>
                    )) : (
                      <tr><td colSpan="3" style={{textAlign:"center"}}>No data available</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkOrderAreaPage;
