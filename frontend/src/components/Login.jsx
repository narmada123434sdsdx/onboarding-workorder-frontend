import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import './css/login.css';
import { BASE_URLS } from '../api/api';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userCaptchaInput, setUserCaptchaInput] = useState(''); // ✅ FIXED: Separate state for USER input
  const [generatedCaptchaCode, setGeneratedCaptchaCode] = useState(''); // ✅ FIXED: Separate state for generated code
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [captchaImage, setCaptchaImage] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const message = location.state?.message;

  // Generate CAPTCHA
  const generateCaptcha = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'; // Only uppercase + numbers
    let code = '';
    for (let i = 0; i < 6; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    // ✅ FIXED: Only set generated code, NOT user input
    setGeneratedCaptchaCode(code);
    setUserCaptchaInput(''); // ✅ Clear user input on refresh
    
    // Generate distorted image
    const canvas = document.createElement('canvas');
    canvas.width = 120;
    canvas.height = 40;
    const ctx = canvas.getContext('2d');
    
    // Background
    const gradient = ctx.createLinearGradient(0, 0, 120, 40);
    gradient.addColorStop(0, '#f8f9ff');
    gradient.addColorStop(1, '#e8f0ff');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 120, 40);
    
    // Border
    ctx.strokeStyle = '#e1e5e9';
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, 118, 38);
    
    // Noise lines
    ctx.strokeStyle = 'rgba(0,0,0,0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.moveTo(Math.random() * 120, Math.random() * 40);
      ctx.lineTo(Math.random() * 120, Math.random() * 40);
      ctx.stroke();
    }
    
    // Text
    ctx.font = 'bold 24px Arial, sans-serif';
    ctx.fillStyle = '#1e40af';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Split text for distortion
    for (let i = 0; i < code.length; i++) {
      ctx.save();
      ctx.translate(15 + i * 18, 20);
      ctx.rotate((Math.random() - 0.5) * 0.3);
      ctx.fillText(code[i], 0, 0);
      ctx.restore();
    }
    
    setCaptchaImage(canvas.toDataURL());
  };

  useEffect(() => {
    generateCaptcha();
  }, []);

  const refreshCaptcha = () => {
    generateCaptcha();
    setFieldErrors(prev => ({ ...prev, captcha: '' }));
  };

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!email.trim()) {
      errors.email = 'Email is required.';
    } else if (!emailRegex.test(email)) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!password.trim()) {
      errors.password = 'Password is required.';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters.';
    }

    // ✅ FIXED: Compare USER input vs GENERATED code
    if (!userCaptchaInput.trim()) {
      errors.captcha = 'Enter the code shown above.';
    } else if (userCaptchaInput.toUpperCase() !== generatedCaptchaCode.toUpperCase()) {
      errors.captcha = 'Incorrect captcha. Please try again.';
    }

    setFieldErrors(errors);
    return { errors, isValid: Object.keys(errors).length === 0 };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const { errors, isValid } = validateForm();
    
    if (!isValid) {
      // ✅ FIXED: Show error briefly, then auto-refresh CAPTCHA on incorrect input
      if (errors.captcha) {
        setTimeout(() => {
          refreshCaptcha();
        }, 1500);
      }
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${BASE_URLS.user}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email, 
          password
          // ✅ CAPTCHA already validated on frontend - no need to send
        }),
      });

      const data = await response.json();
      console.log(data);
      if (response.ok) {
        navigate('/verify-otp', { state: { email } });
        setEmail('');
        setPassword('');
        setUserCaptchaInput('');
        generateCaptcha();
      } else {
        setError(data.error || 'Login failed. Please try again.');
        generateCaptcha();
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
      generateCaptcha();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Welcome Back</h2>
        <p className="login-subtitle">Sign in to your account</p>

        {error && <p className="login-error">{error}</p>}
        {message && <p className="success-message">{message}</p>}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => {
                const value = e.target.value;
                setEmail(value);
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (emailRegex.test(value)) {
                  setFieldErrors((prev) => ({ ...prev, email: '' }));
                }
              }}
              placeholder="Enter your email"
              disabled={loading}
            />
            {fieldErrors.email && <span className="error-text">{fieldErrors.email}</span>}
          </div>

          <div className="form-group password-group">
            <label htmlFor="password">Password</label>
            <div className="password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                value={password}
                onChange={(e) => {
                  const value = e.target.value;
                  setPassword(value);
                  if (value.length >= 8) {
                    setFieldErrors((prev) => ({ ...prev, password: '' }));
                  }
                }}
                placeholder="Enter your password"
                disabled={loading}
              />
              <span className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </span>
            </div>
            {fieldErrors.password && <span className="error-text">{fieldErrors.password}</span>}
          </div>

          {/* ✅ FIXED CAPTCHA SECTION Bhanu 22-10-2025 */}
          <div className="form-group captcha-group">
            <label>Captcha</label>
            <div className="captcha-container">
              <div className="captcha-image-wrapper">
                {captchaImage && (
                  <img 
                    src={captchaImage} 
                    alt="Captcha" 
                    className="captcha-image"
                  />
                )}
                <button 
                  type="button" 
                  className="refresh-captcha"
                  onClick={refreshCaptcha}
                  disabled={loading}
                  title="Refresh Captcha"
                >
                  🔄
                </button>
              </div>
              <input
                type="text"
                className="captcha-input"
                value={userCaptchaInput} // ✅ FIXED: User input state
                onChange={(e) => {
                  const value = e.target.value.toUpperCase();
                  setUserCaptchaInput(value);
                  // Clear error if they start typing
                  if (fieldErrors.captcha) {
                    setFieldErrors((prev) => ({ ...prev, captcha: '' }));
                  }
                }}
                placeholder="Enter the code shown above"
                disabled={loading}
                maxLength={6}
              />
            </div>
            {fieldErrors.captcha && (
              <span className="error-text">{fieldErrors.captcha}</span>
            )}
            <div className="captcha-hint">
              Solve the challenge question to verify you are not a robot.
            </div>
          </div>

          <button 
            type="submit" 
            className="login-button" 
            disabled={loading || Object.values(fieldErrors).some((msg) => msg)}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing In...
              </>
            ) : (
              'Continue'
            )}
          </button>
        </form>

        <p className="forgot-password">
          <Link to="/forgot_password" className="link">
            Forgot Password?
          </Link>
        </p>
        <p className="signup-link">
          Don't have an account?{' '}
          <Link to="/signup" className="link">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
