import React, { useState, useEffect } from "react";
import "./css/setuppage.css";
import { apiGet, apiPost, apiPut, apiDelete } from "../../api/api"; // ✅ import clean API

const WorkOrderTypePage = () => {

  const [formData, setFormData] = useState({
    WORKORDER_TYPE: "",
    STATUS: "Active",
  });

  const [types, setTypes] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editingData, setEditingData] = useState({
    WORKORDER_TYPE: "",
    STATUS: "",
  });

  // Restrict input
  const cleanInput = (value) => value.replace(/[^A-Za-z0-9-]/g, "");

  // ✅ FETCH LIST (REPLACED localhost with apiGet)
  const fetchTypes = async () => {
    try {
      const data = await apiGet("/api/workorder-type");
      setTypes(data);
    } catch (error) {
      console.error("Error fetching types:", error);
    }
  };

  useEffect(() => {
    fetchTypes();
  }, []);

  // Add Form Input
  const handleChange = (e) => {
    const { name, value } = e.target;
    const cleaned = name === "WORKORDER_TYPE" ? cleanInput(value) : value;

    setFormData((prev) => ({ ...prev, [name]: cleaned }));
  };

  // Edit Form Input
  const handleEditChange = (e) => {
    const { name, value } = e.target;
    const cleaned = name === "WORKORDER_TYPE" ? cleanInput(value) : value;

    setEditingData((prev) => ({ ...prev, [name]: cleaned }));
  };

  // ✅ ADD NEW (uses apiPost instead of fetch localhost)
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiPost("/api/workorder-type", formData);
      setFormData({ WORKORDER_TYPE: "", STATUS: "Active" });
      fetchTypes();
      alert("✅ Work Order Type added successfully!");
    } catch (error) {
      console.error("Error:", error);
      alert("❌ Failed to add work order type.");
    }
  };

  // Edit record
  const handleEdit = (type) => {
    setEditingId(type.id);
    setEditingData({
      WORKORDER_TYPE: type.workorder_type,
      STATUS: type.status,
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditingData({ WORKORDER_TYPE: "", STATUS: "" });
  };

  // ✅ UPDATE (uses apiPut instead of fetch localhost)
  const handleUpdate = async (id) => {
    try {
      await apiPut(`/api/workorder-type/${id}`, editingData);
      setEditingId(null);
      fetchTypes();
      alert("✅ Updated Successfully!");
    } catch (error) {
      console.error("Error:", error);
      alert("❌ Failed to update");
    }
  };

  // ✅ DELETE (uses apiDelete instead of fetch localhost)
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure?")) return;

    try {
      await apiDelete(`/api/workorder-type/${id}`);
      fetchTypes();
      alert("🗑️ Deleted Successfully!");
    } catch (error) {
      console.error("Error:", error);
      alert("❌ Failed to delete");
    }
  };

  const handleReset = () => {
    setFormData({ WORKORDER_TYPE: "", STATUS: "Active" });
  };

  return (
    <div className="setup-page">
      <div className="page-container">
        {/* --- FORM --- */}
        <div className="box-section form-box">
          <h2>Add New Work Type</h2>

          <form onSubmit={handleSubmit} className="form-create">
            <div className="form-header-row">
              <div className="form-header-cell">WORK ORDER TYPE</div>
              <div className="form-header-cell">STATUS</div>
            </div>

            <div className="form-group">
              <div className="input-with-star">
                <input
                  type="text"
                  name="WORKORDER_TYPE"
                  value={formData.WORKORDER_TYPE}
                  onChange={handleChange}
                  placeholder="Enter Work Order Type"
                  required
                />
                <span className="required-star">★</span>
              </div>
            </div>

            <div className="form-group">
              <div className="input-with-star">
                <select
                  name="STATUS"
                  value={formData.STATUS}
                  onChange={handleChange}
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
                <span className="required-star">★</span>
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary">Submit</button>
              <button type="button" className="btn-reset" onClick={handleReset}>Reset</button>
            </div>
          </form>
        </div>

        {/* --- TABLE --- */}
        <div className="box-section table-box">
          <h2>Existing Work Order Types</h2>
          <div className="table-wrapper">
            <table className="workorder-table">
              <thead>
                <tr>
                  <th>Work Order Type</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {types.length > 0 ? (
                  types.map((type) => (
                    <tr key={type.id}>
                      {editingId === type.id ? (
                        <>
                          <td>
                            <input
                              type="text"
                              name="WORKORDER_TYPE"
                              value={editingData.WORKORDER_TYPE}
                              onChange={handleEditChange}
                            />
                          </td>
                          <td>
                            <select
                              name="STATUS"
                              value={editingData.STATUS}
                              onChange={handleEditChange}
                            >
                              <option value="Active">Active</option>
                              <option value="Inactive">Inactive</option>
                            </select>
                          </td>
                          <td>
                            <button className="btn-save" onClick={() => handleUpdate(type.id)}>Save</button>
                            <button className="btn-cancel" onClick={handleCancel}>Cancel</button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{type.workorder_type}</td>
                          <td>{type.status}</td>
                          <td>
                            <button className="btn-edit" onClick={() => handleEdit(type)}>Edit</button>
                            <button className="btn-delete" onClick={() => handleDelete(type.id)}>Delete</button>
                          </td>
                        </>
                      )}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="3" style={{ textAlign: "center" }}>No Data</td>
                  </tr>
                )}
              </tbody>

            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkOrderTypePage;
