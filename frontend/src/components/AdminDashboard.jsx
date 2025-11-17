// components/AdminDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BASE_URLS } from '../api/api';
// import './css/AdminDashboard.css';


function AdminDashboard({ admin, setAdmin }) {
  const [providers, setProviders] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [servicesModalUser, setServicesModalUser] = useState(null);
  const [sending, setSending] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    const storedAdmin = localStorage.getItem('admin');
    if (!storedAdmin) {
      navigate('/admin/login');
      return;
    }
    const adminData = JSON.parse(storedAdmin);
    setAdmin(adminData);
    fetchProviders();
    fetchContractors();
  }, [navigate]);

  // ---------------- PROVIDERS ----------------
  const fetchProviders = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URLS.admin}/api/admin/providers`);
      const data = await response.json();
      console.log("Individual Data: ",data);
      if (response.ok) setProviders(data);
      else setError('Failed to fetch providers');
    } catch {
      setError('Error fetching providers');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveProvider = async (email) => {
    if (!confirm('Approve this provider?')) return;
    try {
      const res = await fetch(`${BASE_URLS.admin}/api/admin/approve_provider`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      if (res.ok) {
        fetchProviders();
        alert('Provider approved');
      } else alert('Error approving provider');
    } catch { alert('An error occurred'); }
  };

  const handleRejectProvider = async (email) => {
    if (!confirm('Reject this provider?')) return;
    try {
      const res = await fetch(`${BASE_URLS.admin}/api/admin/reject_provider`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      if (res.ok) {
        fetchProviders();
        alert('Provider rejected');
      } else alert('Error rejecting provider');
    } catch { alert('An error occurred'); }
  };

  // ---------------- CONTRACTORS ----------------
  const fetchContractors = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URLS.admin}/api/admin/contractors`);
      const data = await response.json();
      console.log("company Data: ",data);
      if (response.ok) setContractors(data);
      else setError('Failed to fetch contractors');
    } catch {
      setError('Error fetching contractors');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveContractor = async (email) => {
    if (!confirm('Approve this contractor?')) return;
    try {
      const res = await fetch(`${BASE_URLS.admin}/api/admin/approve_contractor`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      if (res.ok) {
        fetchContractors();
        alert('Contractor approved');
      } else alert('Error approving contractor');
    } catch { alert('An error occurred'); }
  };

  const handleRejectContractor = async (email) => {
    if (!confirm('Reject this contractor?')) return;
    try {
      const res = await fetch(`${BASE_URLS.admin}/api/admin/reject_contractor`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      if (res.ok) {
        fetchContractors();
        alert('Contractor rejected');
      } else alert('Error rejecting contractor');
    } catch { alert('An error occurred'); }
  };

  // ---------------- COMMON ----------------
const handleSendMessage = async (email, type) => {
  if (!message.trim()) {
    alert('Message cannot be empty');
    return;
  }
  setSending(true);
  try {
    const route =
      type === 'provider' ? 'send_message' : 'send_message_contractor';

    const response = await fetch(`${BASE_URLS.admin}/api/admin/${route}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, message }),
    });

    if (response.ok) {
      setMessage('');
      setSelectedUser(null);
      alert('Message sent successfully');
    } else {
      alert('Failed to send message');
    }
  } catch {
    alert('Error sending message');
  } finally {
    setSending(false);
  }
};


  const openServicesModal = (user) => setServicesModalUser(user);
  const closeServicesModal = () => setServicesModalUser(null);

  const getServicesTableData = (services) => {
    const tableData = [];
    if (services && Object.keys(services).length > 0) {
      Object.entries(services).forEach(([serviceName, locations]) => {
        Object.entries(locations).forEach(([location, price]) => {
          tableData.push({
            service: serviceName,
            location: location,
            cost: price
          });
        });
      });
    }
    return tableData;
  };

  if (loading) return <div className="text-center mt-5">Loading...</div>;
  if (error) return <div className="alert alert-danger text-center mt-5">{error}</div>;

  return (
    <div className=" admin-dashboard container mt-4">
      {/* ---------------- PROVIDER SECTION ---------------- */}
      <div className="card mb-4">
        <div className="card-header bg-primary text-white">
          <h5>Individual Management</h5>
        </div>
        <div className="card-body table-responsive">
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Full Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Services</th>
                <th>Status</th>
                <th>Actions</th>                  
                <th>Certificates</th>
              </tr>
            </thead>
            <tbody>
  {providers.map((p) => (
    <tr key={p.provider_id}>
      <td>{p.full_name || 'N/A'}</td>
      <td>{p.email_id}</td>
      <td>{p.contact_number || 'N/A'}</td>
      <td>
        {p.services && Object.keys(p.services).length > 0 ? (
          <button
            className="btn btn-link btn-sm p-0"
            onClick={() => openServicesModal(p)}>
            View ({Object.keys(p.services).length})
          </button>
        ) : 'N/A'}
      </td>
      <td>
        <span className={`badge ${
          p.status === 'approved' ? 'bg-success' :
          p.status === 'pending' ? 'bg-warning' : 'bg-danger'
        }`}>
          {p.status}
        </span>
      </td>
      <td>
        {p.status === 'pending' && (
          <>
            <button
              className="btn btn-sm btn-success me-1"
              onClick={() => handleApproveProvider(p.email_id)}>
              Approve
            </button>
            <button
              className="btn btn-sm btn-danger me-1"
              onClick={() => handleRejectProvider(p.email_id)}>
              Reject
            </button>
            <button
              className="btn btn-sm btn-info"
              onClick={() => setSelectedUser({ email: p.email_id, type: 'provider' })}>
              Message
            </button>
          </>
        )}
      </td>
      <td>
        {p.full_name && (
          <a
            href={`${BASE_URLS.user}/api/get_image/${p.email_id}/profile`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-sm btn-outline-primary me-2">
            Profile
          </a>
        )}
        {p.full_name && (
          <a
            href={`${BASE_URLS.user}/api/get_image/${p.email_id}/certificate`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-sm btn-outline-secondary">
            Certificate
          </a>
        )}
      </td>
    </tr>
  ))}
</tbody>

          </table>
        </div>
      </div>

      {/* ---------------- CONTRACTOR SECTION ---------------- */}
      <div className="card mb-4">
        <div className="card-header bg-secondary text-white">
          <h5>Company Management</h5>
        </div>
        <div className="card-body table-responsive">
          <table className="table table-striped">
            <thead>
              <tr>
                <th>Company Name</th>
                <th>Email</th>
                <th>Contact</th>
                <th>Services</th>
                <th>Status</th>
                <th>Actions</th>
                <th>Certificates</th>
              </tr>
            </thead>
            <tbody>
              {contractors.map((c) => (
                <tr key={c.company_id}>
                  <td>{c.company_name || 'N/A'}</td>
                  <td>{c.head_email}</td>
                  <td>{c.contact_number || 'N/A'}</td>
                  <td>
                    {c.services && Object.keys(c.services).length > 0 ? (
                      <button
                        className="btn btn-link btn-sm p-0"
                        onClick={() => openServicesModal(c)}>
                        View ({Object.keys(c.services).length})
                      </button>
                    ) : 'N/A'}
                  </td>
                  <td>
                    <span className={`badge ${c.status === 'approved' ? 'bg-success' :
                      c.status === 'pending' ? 'bg-warning' : 'bg-danger'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td>
                    {c.status === 'pending' && (
                      <>
                        <button className="btn btn-sm btn-success me-1"
                          onClick={() => handleApproveContractor(c.head_email)}>Approve</button>
                        <button className="btn btn-sm btn-danger me-1"
                          onClick={() => handleRejectContractor(c.head_email)}>Reject</button>
                        <button className="btn btn-sm btn-info"
                          onClick={() => setSelectedUser({ email: c.head_email, type: 'contractor' })}>Message</button>
                      </>
                    )}
                  </td>
                  <td>
                    {c.company_name && (
                      <a
                        href={`${BASE_URLS.user}/api/get_image/${c.head_email}/contractor_logo`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm btn-outline-primary me-2">
                        Logo
                      </a>
                    )}
                    {c.company_name && (
                      <a
                        href={`${BASE_URLS.user}/api/get_image/${c.head_email}/contractor_certificate`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm btn-outline-secondary">
                        Certificate
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Shared Services Modal */}
      {servicesModalUser && (
        <div className="modal fade show d-block" style={{ background: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Services for {servicesModalUser.full_name || servicesModalUser.company_name}
                </h5>
                <button className="btn-close" onClick={closeServicesModal}></button>
              </div>
              <div className="modal-body">
                <table className="table table-bordered">
                  <thead>
                    <tr>
                      <th>Service</th><th>Location</th><th>Rate (MYR)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.isArray(servicesModalUser.services) && servicesModalUser.services.length > 0 ? (
                      servicesModalUser.services.map((s, i) => (
                        <tr key={i}>
                          <td>{s.service_name || '-'}</td>
                          <td>{s.service_location || '-'}</td>
                          <td>{s.service_rate || '-'}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="3" className="text-center">No services available</td>
                      </tr>
                    )}

                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Shared Message Modal */}
 {selectedUser && (
  <div
    className="modal fade show d-block"
    style={{ background: 'rgba(0,0,0,0.5)' }}
  >
    <div className="modal-dialog">
      <div className="modal-content">
        <div className="modal-header">
          <h5 className="modal-title">
            Send Message to {selectedUser.email}
          </h5>
          <button
            className="btn-close"
            onClick={() => {
              setSelectedUser(null);
              setMessage('');
            }}
            disabled={sending}
          ></button>
        </div>
        <div className="modal-body">
          {sending ? (
            <div className="text-center py-4">
              <div className="spinner-border text-primary mb-3" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="text-muted">Sending message...</p>
            </div>
          ) : (
            <textarea
              className="form-control"
              rows="4"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter your message..."
            ></textarea>
          )}
        </div>
        {!sending && (
          <div className="modal-footer">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setSelectedUser(null);
                setMessage('');
              }}
            >
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={() =>
                handleSendMessage(selectedUser.email, selectedUser.type)
              }
              disabled={sending || !message.trim()}
            >
              {sending ? 'Sending...' : 'Send'}
            </button>
          </div>
        )}
      </div>
    </div>
  </div>
)}

    </div>
  );
}

export default AdminDashboard;
