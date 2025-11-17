import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import "./css/companyActivateAccount.css";
import { BASE_URLS } from '../../api/api';

function CompanyActivateAccount({ setContractor }) {
  const [activated, setActivated] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing activation link.');
    }
  }, [token]);

  const handleActivate = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${BASE_URLS.user}/api/contractor/contractor_activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });

      const data = await response.json();
      console.log("activate account",data);
      if (response.ok) {
        setActivated(true);

        // ✅ Save the contractor in localStorage for persistence
        if (data.email_id) {
          localStorage.setItem('contractor', JSON.stringify({ head_email: data.email_id }));
          setContractor({ head_email: data.email_id });
        }

        // ✅ Redirect to company dashboard after short delay
        setTimeout(() => {
          navigate('/contractor/dashboard/profile', { state: { email: data.email_id } });
        }, 1500);
      } else {
        setError(data.error || 'Activation failed. Please try again.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    }
  };

  if (error)
    return (
      <div className="activate-container" style={{ color: '#ef4444', padding: '1rem' }}>
        {error}
      </div>
    );

  return (
    <div className="activate-container">
      <h2 className="activate-title">Activate Company Account</h2>
      {!activated ? (
        <form onSubmit={handleActivate} className="activate-form">
          <p className="activate-text">Do you want to activate your company account?</p>
          <div className="activate-buttons">
            <button type="submit" className="activate-yes">Yes</button>
            <button type="button" onClick={() => navigate('/contractor/login')} className="activate-no">No</button>
          </div>
        </form>
      ) : (
        <p className="activate-success">Company account activated! Redirecting...</p>
      )}
    </div>
  );
}

export default CompanyActivateAccount;
