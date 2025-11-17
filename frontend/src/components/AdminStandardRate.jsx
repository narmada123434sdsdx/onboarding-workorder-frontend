import React, { useState, useEffect } from "react";
import axios from "axios";
import * as XLSX from "xlsx";
import './css/AdminStandardRate.css';
import { BASE_URLS } from "../api/api";

function AdminStandardRate() {
  const [rates, setRates] = useState([]);
  const [file, setFile] = useState(null);
  const [form, setForm] = useState({ service_name: "", service_location: "", service_rate: "" ,client: ""});
  const [editIndex, setEditIndex] = useState(null);

  useEffect(() => {
    fetchRates();
  }, []);

  // Fetch all rates from backend
  const fetchRates = async () => {
    try {
      const res = await axios.get(`${BASE_URLS.admin}/api/admin/rates`);
      console.log("Rates data:", res.data);
      setRates(res.data);
    } catch (err) {
      console.error("Error fetching rates:", err);
    }
  };

  // Handle single record add/update
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editIndex !== null) {
        await axios.put(`${BASE_URLS.admin}/api/admin/standard_rates/${editIndex}`, form);
      } else {
        await axios.post(`${BASE_URLS.admin}/api/admin/standard_rates`, form);
      }
      setForm({ service_name: "", service_location: "", service_rate: "" , client:""});
      setEditIndex(null);
      fetchRates();
    } catch (err) {
      alert(err.response?.data?.error || "Error saving rate");
    }
  };

  // Handle delete
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure to delete this rate?")) return;
    await axios.delete(`${BASE_URLS.admin}/api/admin/standard_rates/${id}`);
    fetchRates();
  };

  // Handle Excel upload
const handleFileUpload = async (e) => {
  e.preventDefault();
  if (!file) return alert("Please select an Excel file");

  const formData = new FormData();
  formData.append("file", file);

  try {
    await axios.post(`${BASE_URLS.admin}/api/admin/upload_excel`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    alert("Upload successful!");
    setFile(null);
    document.getElementById("excelUpload").value = ""; // ✅ clear file input
    fetchRates();
  } catch (err) {
    alert(err.response?.data?.error || "Error uploading file");
  }
};


  const handleEdit = (rate) => {
      setForm({
    service_name: rate.service_name,
    service_location: rate.service_location,
    service_rate: rate.service_rate,
    client: rate.client
  });
    setEditIndex(rate.id);
  };

  return (
    <div className="container mt-4">
      <h2 className="mb-4">Standard Rate Management</h2>

      {/* Excel Upload */}
      <div className="card p-3 mb-4">
        <h5>Upload Excel File(service_name,service_location,service_rate,client)</h5>
        <form onSubmit={handleFileUpload}>
          <input
            id="excelUpload"
            type="file"
            accept=".xlsx, .xls"
            onChange={(e) => setFile(e.target.files[0])}
        />

          <button type="submit" className="btn btn-primary">Upload</button>
        </form>
      </div>

      {/* Single Add/Edit Form */}
      <div className="card p-3 mb-4">
        <h5>{editIndex ? "Edit Rate" : "Add Single Rate"}</h5>
        <form onSubmit={handleSubmit}>
          <div className="row mb-2">
            <div className="col-md-4">
              <input
                type="text"
                placeholder="Service Name"
                className="form-control"
                value={form.service_name}
                onChange={(e) => setForm({ ...form, service_name: e.target.value })}
                required
              />
            </div>
            <div className="col-md-4">
              <input
                type="text"
                placeholder="Service Location"
                className="form-control"
                value={form.service_location}
                onChange={(e) => setForm({ ...form, service_location: e.target.value })}
                required
              />
            </div>
            <div className="col-md-4">
              <input
                type="number"
                placeholder="Service Rate (MYR)"
                className="form-control"
                value={form.service_rate}
                onChange={(e) => setForm({ ...form, service_rate: e.target.value })}
                required
              />
            </div>
            <div className="col-md-4">
              <input
                type="text"
                placeholder="Client"
                className="form-control"
                value={form.client}
                onChange={(e) => setForm({ ...form, client: e.target.value })}
                required
              />
            </div>
          </div>
          <button type="submit" className="btn btn-success">
            {editIndex ? "Update" : "Add"}
          </button>
          {editIndex && (
            <button type="button" className="btn btn-secondary ms-2" onClick={() => { setEditIndex(null); setForm({ service_name: "", service_location: "", service_rate: "" }); }}>
              Cancel
            </button>
          )}
        </form>
      </div>

      {/* Rates Table */}
      <div className="card p-3">
        <h5>Existing Rates</h5>
        <table className="table table-bordered mt-2">
          <thead>
            <tr>
              <th>Service Name</th>
              <th>Service Location</th>
              <th>Rate (MYR)</th>
              <th>Client</th>
              <th>Actions</th>
            </tr>
          </thead>
<tbody>
  {rates.length > 0 ? (
    rates.map((r) => (
      <tr key={r.id}>
        <td data-label="Service Name">{r.service_name}</td>
        <td data-label="Service Location">{r.service_location}</td>
        <td data-label="Rate (MYR)">{r.service_rate}</td>
        <td data-label="Client">{r.client}</td>
        <td data-label="Actions">
          <button className="btn btn-sm btn-warning me-2" onClick={() => handleEdit(r)}>
            Edit
          </button>
          <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r.id)}>
            Delete
          </button>
        </td>
      </tr>
    ))
  ) : (
    <tr>
      <td colSpan="5" className="text-center">
        No records found
      </td>
    </tr>
  )}
</tbody>

        </table>
      </div>
    </div>
  );
}

export default AdminStandardRate;
