import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import "./css/otpverification.css";
import { BASE_URLS } from '../api/api';

function OTPVerification({ setUser }) {
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  //18-10-2025 for resend otp
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(); // ⏳ for resend cooldown
  //-------resend otp
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';


    // Countdown logic 18-10-2025
  useEffect(() => {
    let interval = null;
    if (timer > 0) {
      interval = setInterval(() => setTimer((t) => t - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [timer]);


  const handleSubmit = async (e) => {
    e.preventDefault();
    //18-10-2025
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${BASE_URLS.user}/api/verify_otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp })
      });
      const data = await response.json();
      if (response.ok) {
         // ✅ Save logged-in user permanently--Ramya 17-10-2025
        localStorage.setItem('user', JSON.stringify({ email }));
        setUser({ email });
         navigate('/provider_home', { state: { email } });
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    }
  };

   const handleResendOtp = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${BASE_URLS.user}/api/resend_otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();
      if (response.ok) {
        setSuccess('A new OTP has been sent to your email.');
        setTimer(30); // ⏳ Start 30s cooldown
      } else {
        setError(data.error || 'Failed to resend OTP.');
      }
    } catch {
      setError('An error occurred while resending OTP.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="otpverification-container">
     <div className="otpverification-card">
    <h2 className="otpverification-title">Verify OTP</h2>
      <p className="otpverification-text">An OTP has been sent to {email}</p>
      {error && <p className="otpverification-error">{error}</p>}
      {success && <p className="otpverification-success">{success}</p>}
      <form onSubmit={handleSubmit} className="otpverification-form">
        <div className="otpverification-input-group">
          <label className="otpverification-label">OTP</label>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            className="otpverification-input"
            required
          />
        </div>
        <button type="submit" className="otpverification-button">Verify</button>
      </form>
          <button
          onClick={handleResendOtp}
          className="otpverification-resend-button"
          disabled={loading || timer > 0}
        >
          {loading
            ? 'Sending...'
            : timer > 0
            ? `Resend OTP (${timer}s)`
            : 'Resend OTP'}
        </button>

    </div>
    </div>
  );
}

export default OTPVerification;